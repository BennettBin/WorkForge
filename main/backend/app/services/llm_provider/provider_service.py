from datetime import datetime, timezone
import json
from urllib import error, request

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
        base_url = payload.base_url
        model_name = payload.model_name
        chat_model = payload.chat_model
        embedding_model = payload.embedding_model

        if payload.provider_type == "ollama":
            base_url = base_url or defaults.base_url
            chat_model = chat_model or model_name or defaults.chat_model
            embedding_model = embedding_model or defaults.embedding_model
            model_name = model_name or chat_model
        else:
            chat_model = chat_model or model_name or defaults.chat_model
            embedding_model = embedding_model or defaults.embedding_model
            model_name = model_name or chat_model

        cfg = LLMProviderConfig(
            provider_id=provider_id,
            user_id=payload.user_id,
            provider_type=payload.provider_type,
            display_name=payload.display_name,
            base_url=base_url,
            api_key_encrypted=payload.api_key,
            model_name=model_name or "",
            chat_model=chat_model,
            embedding_model=embedding_model,
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
                "message": (
                    f"Ollama reachable and model found: {model_name}"
                    if found
                    else f"Ollama reachable, but model not found: {model_name}. Available: {sorted(model_names)[:8]}"
                ),
            }
        checks = {
            "provider_type": payload.provider_type,
            "base_url": payload.base_url,
            "model_name": model_name,
            "status": "ok",
            "message": "Connection parameters accepted in MVP mode.",
        }
        return checks
