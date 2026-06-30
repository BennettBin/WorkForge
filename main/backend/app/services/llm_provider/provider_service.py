from datetime import datetime, timezone
import json
import socket
from urllib import error, request
from typing import Optional

from app.models.entities import LLMProviderConfig
from app.models.requests import ProviderTestRequest, ProviderUpsertRequest
from app.services.repository_factory import RepositoryBundle
from app.services.llm_provider.provider_defaults import OllamaConfig
from app.utils.ids import new_id


def _utc_now():
    return datetime.now(timezone.utc)


class ProviderService:
    def __init__(self, repos: RepositoryBundle):
        self.repos = repos

    def upsert(self, payload: ProviderUpsertRequest) -> LLMProviderConfig:
        provider_id = payload.provider_id or new_id("provider")
        defaults = OllamaConfig()
        existing = self.repos.providers.get_by_id(provider_id) if payload.provider_id else None
        base_url = payload.base_url
        model_name = payload.model_name
        chat_model = payload.chat_model
        api_key = (payload.api_key or "").strip() or None

        if payload.provider_type == "ollama":
            base_url = base_url or defaults.base_url
            chat_model = chat_model or model_name or defaults.chat_model
            model_name = model_name or chat_model
        else:
            chat_model = chat_model or model_name or defaults.chat_model
            model_name = model_name or chat_model

        if payload.provider_type in {"deepseek_api", "openai_api", "anthropic_api", "qwen_api"}:
            if not api_key and existing and existing.user_id == payload.user_id:
                api_key = (existing.api_key_encrypted or "").strip() or None
            if not api_key:
                raise ValueError("api_key is required for this provider type.")

        cfg = LLMProviderConfig(
            provider_id=provider_id,
            user_id=payload.user_id,
            provider_type=payload.provider_type,
            display_name=payload.display_name,
            base_url=base_url,
            api_key_encrypted=api_key,
            model_name=model_name or "",
            chat_model=chat_model,
            embedding_model=None,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            timeout_seconds=payload.timeout_seconds,
            streaming_enabled=payload.streaming_enabled,
            is_default=payload.is_default,
            updated_at=_utc_now(),
        )
        return self.repos.providers.upsert(cfg)

    def list_by_user(self, user_id: str) -> list[LLMProviderConfig]:
        return self.repos.providers.list_by_user(user_id)

    def get_default_for_user(self, user_id: str) -> Optional[LLMProviderConfig]:
        return self.repos.providers.get_default_for_user(user_id)

    def test_connection(self, payload: ProviderTestRequest) -> dict:
        model_name = payload.model_name
        if payload.provider_type == "ollama":
            defaults = OllamaConfig()
            model_name = payload.chat_model or payload.model_name or defaults.chat_model
            base_url = (payload.base_url or defaults.base_url).rstrip("/")
            tags_url = f"{base_url}/api/tags"
            req = request.Request(url=tags_url, method="GET")
            try:
                with request.urlopen(req, timeout=8) as resp:
                    body = resp.read().decode("utf-8", errors="ignore")
            except error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="ignore")
                return {
                    "provider_type": payload.provider_type,
                    "base_url": base_url,
                    "model_name": model_name,
                    "status": "error",
                    "message": f"Ollama reachable check failed: HTTP {exc.code} {detail[:180]}",
                }
            except Exception as exc:
                return {
                    "provider_type": payload.provider_type,
                    "base_url": base_url,
                    "model_name": model_name,
                    "status": "error",
                    "message": f"Ollama reachable check failed: {exc}",
                }

            try:
                data = json.loads(body)
            except Exception:
                return {
                    "provider_type": payload.provider_type,
                    "base_url": base_url,
                    "model_name": model_name,
                    "status": "error",
                    "message": f"Ollama /api/tags returned invalid JSON: {body[:180]}",
                }

            models = data.get("models", []) if isinstance(data, dict) else []
            model_names: set[str] = set()
            for row in models:
                if not isinstance(row, dict):
                    continue
                for k in ("name", "model"):
                    v = str(row.get(k, "")).strip()
                    if v:
                        model_names.add(v)
            found = False
            target = (model_name or "").strip()
            if target:
                target_l = target.lower()
                found = any(x.lower() == target_l or x.lower().startswith(target_l + ":") for x in model_names)
            else:
                found = True
            return {
                "provider_type": payload.provider_type,
                "base_url": base_url,
                "model_name": model_name,
                "status": "ok" if found else "error",
                "reachable": True,
                "model_found": found,
                "error_code": None if found else "MODEL_NOT_FOUND",
                "message": (
                    f"Ollama reachable and model found: {model_name}"
                    if found
                    else f"Ollama reachable, but model not found: {model_name}. Available: {sorted(model_names)[:8]}"
                ),
            }
        if payload.provider_type in {
            "vllm",
            "huggingface",
            "openai_compatible",
            "openai_api",
            "deepseek_api",
            "qwen_api",
            "custom_http",
            "local_llm",
        }:
            return self._test_openai_compatible_models(
                provider_type=payload.provider_type,
                base_url=payload.base_url or "",
                model_name=model_name or "",
                api_key=payload.api_key,
            )
        if payload.provider_type == "anthropic_api":
            return self._test_anthropic_messages(
                base_url=payload.base_url or "",
                model_name=model_name or "",
                api_key=payload.api_key or "",
            )
        return {
            "provider_type": payload.provider_type,
            "base_url": payload.base_url,
            "model_name": model_name,
            "status": "error",
            "reachable": False,
            "model_found": False,
            "error_code": "UNSUPPORTED_PROVIDER_TEST",
            "message": f"Provider test is not implemented for provider_type={payload.provider_type}.",
        }

    def _test_openai_compatible_models(
        self,
        provider_type: str,
        base_url: str,
        model_name: str,
        api_key: Optional[str] = None,
    ) -> dict:
        normalized_base = (base_url or "").rstrip("/")
        models_url = f"{normalized_base}/models"
        req = request.Request(url=models_url, method="GET")
        if api_key:
            req.add_header("Authorization", f"Bearer {api_key}")
        body = ""
        try:
            with request.urlopen(req, timeout=8) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            code = "BAD_BASE_URL" if exc.code == 404 else "UNAUTHORIZED" if exc.code in {401, 403} else "HTTP_ERROR"
            return self._build_test_error(provider_type, normalized_base, model_name, code, f"HTTP {exc.code}: {detail[:180]}")
        except error.URLError as exc:
            return self._build_test_error(provider_type, normalized_base, model_name, self._map_url_error(exc), str(exc.reason))
        except TimeoutError as exc:
            return self._build_test_error(provider_type, normalized_base, model_name, "TIMEOUT", str(exc))
        except Exception as exc:
            return self._build_test_error(provider_type, normalized_base, model_name, "REQUEST_FAILED", str(exc))

        try:
            data = json.loads(body)
        except Exception:
            return self._build_test_error(
                provider_type,
                normalized_base,
                model_name,
                "INVALID_JSON",
                f"/models returned invalid JSON: {body[:180]}",
            )

        rows = data.get("data", []) if isinstance(data, dict) else []
        model_ids: list[str] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            item = str(row.get("id", "")).strip()
            if item:
                model_ids.append(item)

        if not model_ids:
            return self._build_test_error(
                provider_type,
                normalized_base,
                model_name,
                "EMPTY_MODEL_LIST",
                "/models reachable but returned no model ids.",
            )

        found = self._model_matches(model_name, model_ids, provider_type=provider_type)
        return {
            "provider_type": provider_type,
            "base_url": normalized_base,
            "model_name": model_name,
            "status": "ok" if found else "error",
            "reachable": True,
            "model_found": found,
            "error_code": None if found else "MODEL_NOT_FOUND",
            "message": (
                f"Endpoint reachable and model found: {model_name}"
                if found
                else f"Endpoint reachable, but model not found: {model_name}. Available: {model_ids[:8]}"
            ),
        }

    def _test_anthropic_messages(self, base_url: str, model_name: str, api_key: str) -> dict:
        provider_type = "anthropic_api"
        normalized_base = (base_url or "").rstrip("/")
        messages_url = f"{normalized_base}/messages"
        body = json.dumps(
            {
                "model": model_name,
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "ping"}],
            }
        ).encode("utf-8")
        req = request.Request(url=messages_url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("x-api-key", api_key)
        req.add_header("anthropic-version", "2023-06-01")
        try:
            with request.urlopen(req, timeout=8) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            code = "BAD_BASE_URL" if exc.code == 404 else "UNAUTHORIZED" if exc.code in {401, 403} else "HTTP_ERROR"
            return self._build_test_error(provider_type, normalized_base, model_name, code, f"HTTP {exc.code}: {detail[:180]}")
        except error.URLError as exc:
            return self._build_test_error(provider_type, normalized_base, model_name, self._map_url_error(exc), str(exc.reason))
        except TimeoutError as exc:
            return self._build_test_error(provider_type, normalized_base, model_name, "TIMEOUT", str(exc))
        except Exception as exc:
            return self._build_test_error(provider_type, normalized_base, model_name, "REQUEST_FAILED", str(exc))

        try:
            data = json.loads(raw)
        except Exception:
            return self._build_test_error(
                provider_type,
                normalized_base,
                model_name,
                "INVALID_JSON",
                f"/messages returned invalid JSON: {raw[:180]}",
            )
        content = data.get("content", []) if isinstance(data, dict) else []
        ok = isinstance(content, list) and len(content) > 0
        return {
            "provider_type": provider_type,
            "base_url": normalized_base,
            "model_name": model_name,
            "status": "ok" if ok else "error",
            "reachable": True,
            "model_found": ok,
            "error_code": None if ok else "EMPTY_RESPONSE",
            "message": (
                f"Anthropic endpoint reachable and model responded: {model_name}"
                if ok
                else "Anthropic endpoint reachable but returned no message content."
            ),
        }

    def _build_test_error(
        self,
        provider_type: str,
        base_url: str,
        model_name: str,
        error_code: str,
        reason: str,
    ) -> dict:
        return {
            "provider_type": provider_type,
            "base_url": base_url,
            "model_name": model_name,
            "status": "error",
            "reachable": False,
            "model_found": False,
            "error_code": error_code,
            "message": f"Provider reachable check failed ({error_code}): {reason}",
        }

    def _map_url_error(self, exc: error.URLError) -> str:
        reason = getattr(exc, "reason", None)
        text = str(reason).lower()
        if isinstance(reason, TimeoutError) or "timed out" in text or "timeout" in text:
            return "TIMEOUT"
        if isinstance(reason, ConnectionRefusedError) or "actively refused" in text or "10061" in text:
            return "CONNECTION_REFUSED"
        if isinstance(reason, socket.gaierror) or "name or service not known" in text or "nodename nor servname" in text:
            return "HOST_UNREACHABLE"
        return "NETWORK_ERROR"

    def _model_matches(self, target_model: str, available_models: list[str], provider_type: str = "") -> bool:
        target = (target_model or "").strip()
        if not target:
            return True
        target_l = target.lower()
        available_l = {item.lower() for item in available_models}
        if provider_type == "deepseek_api":
            alias_map = {
                "deepseek-chat": {"deepseek-v4-flash", "deepseek-v4-pro"},
                "deepseek-reasoner": {"deepseek-v4-pro"},
            }
            aliases = alias_map.get(target_l)
            if aliases and available_l.intersection(aliases):
                return True
        for item in available_models:
            if item.lower() == target_l:
                return True
        target_base = target.replace("\\", "/").split("/")[-1].lower()
        for item in available_models:
            item_base = item.replace("\\", "/").split("/")[-1].lower()
            if item_base == target_base:
                return True
        for item in available_models:
            item_l = item.lower()
            if target_l in item_l or item_l in target_l:
                return True
        return False
