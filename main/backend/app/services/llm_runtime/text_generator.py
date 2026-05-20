from __future__ import annotations

import json
from typing import Optional
from urllib import error, request


class LLMInvokeError(Exception):
    pass


class LLMTextGenerator:
    def generate(
        self,
        provider_type: str,
        base_url: Optional[str],
        model_name: str,
        prompt: str,
        api_key: Optional[str] = None,
        timeout_seconds: int = 60,
    ) -> str:
        ptype = self._normalize_provider_type(provider_type)
        if ptype == "ollama":
            return self._ollama_chat(base_url or "http://localhost:11434", model_name, prompt, timeout_seconds)
        if ptype == "anthropic_api":
            return self._anthropic_messages(base_url, model_name, prompt, api_key, timeout_seconds)
        if ptype == "huggingface":
            return self._vllm_chat(base_url, model_name, prompt, api_key, timeout_seconds)
        if ptype in {
            "openai_compatible",
            "openai_api",
            "deepseek_api",
            "qwen_api",
            "local_llm",
            "custom_http",
            "vllm",
            "local_transformers",
        }:
            if ptype == "vllm":
                return self._vllm_chat(base_url, model_name, prompt, api_key, timeout_seconds)
            return self._openai_compatible_chat(base_url, model_name, prompt, api_key, timeout_seconds)
        raise LLMInvokeError(f"Unsupported provider_type for LLM generation: {provider_type}")

    def _normalize_provider_type(self, provider_type: str) -> str:
        raw = (provider_type or "").strip().lower().replace("-", "_").replace(" ", "_")
        alias_map = {
            "openai": "openai_compatible",
            "deepseek": "deepseek_api",
            "qwen": "qwen_api",
            "anthropic": "anthropic_api",
            "hf": "huggingface",
            "hugging_face": "huggingface",
        }
        return alias_map.get(raw, raw)

    def _ollama_chat(self, base_url: str, model_name: str, prompt: str, timeout_seconds: int) -> str:
        url = f"{base_url.rstrip('/')}/api/chat"
        body = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        data = self._post_json(url, body, headers={}, timeout_seconds=timeout_seconds)
        msg = data.get("message", {}) if isinstance(data, dict) else {}
        text = msg.get("content", "") if isinstance(msg, dict) else ""
        if not text:
            raise LLMInvokeError("Ollama returned empty content.")
        return str(text)

    def _openai_compatible_chat(
        self,
        base_url: Optional[str],
        model_name: str,
        prompt: str,
        api_key: Optional[str],
        timeout_seconds: int,
    ) -> str:
        if not base_url:
            raise LLMInvokeError("Base URL is required for OpenAI-compatible request.")
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        body = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        data = self._post_json(url, body, headers=headers, timeout_seconds=timeout_seconds)
        choices = data.get("choices", []) if isinstance(data, dict) else []
        if not choices:
            raise LLMInvokeError("OpenAI-compatible response has no choices.")
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        text = message.get("content", "") if isinstance(message, dict) else ""
        if not text:
            raise LLMInvokeError("OpenAI-compatible returned empty content.")
        return str(text)

    def _anthropic_messages(
        self,
        base_url: Optional[str],
        model_name: str,
        prompt: str,
        api_key: Optional[str],
        timeout_seconds: int,
    ) -> str:
        if not base_url:
            raise LLMInvokeError("Base URL is required for Anthropic request.")
        if not api_key:
            raise LLMInvokeError("API key is required for Anthropic request.")
        url = f"{base_url.rstrip('/')}/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        body = {
            "model": model_name,
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}],
        }
        data = self._post_json(url, body, headers=headers, timeout_seconds=timeout_seconds)
        content = data.get("content", []) if isinstance(data, dict) else []
        if not content:
            raise LLMInvokeError("Anthropic response has no content.")
        first = content[0] if isinstance(content[0], dict) else {}
        text = first.get("text", "") if isinstance(first, dict) else ""
        if not text:
            raise LLMInvokeError("Anthropic returned empty text.")
        return str(text)

    def _vllm_chat(
        self,
        base_url: Optional[str],
        model_name: str,
        prompt: str,
        api_key: Optional[str],
        timeout_seconds: int,
    ) -> str:
        # vLLM serves OpenAI-compatible API. The model passed by UI may be:
        # 1) exact served model id
        # 2) local path used to launch vLLM
        # We resolve to a served id via /models and retry automatically.
        if not base_url:
            raise LLMInvokeError("[vLLM] Base URL is required for request.")
        models_url = f"{base_url.rstrip('/')}/models"
        chat_url = f"{base_url.rstrip('/')}/chat/completions"
        try:
            resolved_model = self._resolve_vllm_model_name(base_url, model_name, api_key, timeout_seconds)
        except LLMInvokeError as exc:
            self._raise_vllm_error(exc, url=models_url)
        try:
            return self._openai_compatible_chat(
                base_url=base_url,
                model_name=resolved_model,
                prompt=prompt,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
            )
        except LLMInvokeError as exc:
            message = str(exc).lower()
            # One more retry with first available model when requested model is rejected.
            if ("model" in message and ("not found" in message or "does not exist" in message or "invalid" in message)):
                fallback_model = self._resolve_vllm_model_name(base_url, "", api_key, timeout_seconds)
                try:
                    return self._openai_compatible_chat(
                        base_url=base_url,
                        model_name=fallback_model,
                        prompt=prompt,
                        api_key=api_key,
                        timeout_seconds=timeout_seconds,
                    )
                except LLMInvokeError as retry_exc:
                    self._raise_vllm_error(retry_exc, url=chat_url)
            self._raise_vllm_error(exc, url=chat_url)

    def _resolve_vllm_model_name(
        self,
        base_url: str,
        requested_model_name: str,
        api_key: Optional[str],
        timeout_seconds: int,
    ) -> str:
        url = f"{base_url.rstrip('/')}/models"
        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        data = self._get_json(url, headers=headers, timeout_seconds=timeout_seconds)
        rows = data.get("data", []) if isinstance(data, dict) else []
        model_ids: list[str] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            model_id = str(row.get("id", "")).strip()
            if model_id:
                model_ids.append(model_id)
        if not model_ids:
            raise LLMInvokeError("vLLM /models returned no model ids.")

        requested = (requested_model_name or "").strip()
        if not requested:
            return model_ids[0]

        req_l = requested.lower()
        # exact id
        for m in model_ids:
            if m.lower() == req_l:
                return m
        # basename match for local paths (Windows/Unix)
        req_base = requested.replace("\\", "/").split("/")[-1].lower()
        for m in model_ids:
            m_base = m.replace("\\", "/").split("/")[-1].lower()
            if m_base == req_base:
                return m
        # contains match
        for m in model_ids:
            if req_l in m.lower() or m.lower() in req_l:
                return m
        # If no match, keep requested value first; caller may still succeed depending on server aliasing.
        return requested

    def _get_json(self, url: str, headers: dict[str, str], timeout_seconds: int):
        req = request.Request(url=url, method="GET")
        for k, v in headers.items():
            req.add_header(k, v)
        try:
            with request.urlopen(req, timeout=timeout_seconds) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise LLMInvokeError(f"LLM HTTPError {exc.code}: {detail[:300]}") from exc
        except Exception as exc:
            raise LLMInvokeError(f"LLM request failed: {exc}") from exc
        try:
            return json.loads(text)
        except Exception as exc:
            raise LLMInvokeError(f"LLM response is not valid JSON: {text[:300]}") from exc

    def _post_json(self, url: str, body: dict, headers: dict[str, str], timeout_seconds: int):
        payload = json.dumps(body).encode("utf-8")
        req = request.Request(url=url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        for k, v in headers.items():
            req.add_header(k, v)
        try:
            with request.urlopen(req, timeout=timeout_seconds) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise LLMInvokeError(f"LLM HTTPError {exc.code}: {detail[:300]}") from exc
        except Exception as exc:
            raise LLMInvokeError(f"LLM request failed: {exc}") from exc
        try:
            return json.loads(text)
        except Exception as exc:
            raise LLMInvokeError(f"LLM response is not valid JSON: {text[:300]}") from exc

    def _raise_vllm_error(self, exc: LLMInvokeError, url: str):
        raw = str(exc)
        lower = raw.lower()
        code = "REQUEST_FAILED"
        if "10061" in lower or "actively refused" in lower or "connection refused" in lower:
            code = "CONNECTION_REFUSED"
        elif "timed out" in lower or "timeout" in lower:
            code = "TIMEOUT"
        elif "httperror 401" in lower or "httperror 403" in lower:
            code = "UNAUTHORIZED"
        elif "httperror 404" in lower:
            code = "BAD_BASE_URL"
        elif "model not found" in lower or "does not exist" in lower or "invalid model" in lower:
            code = "MODEL_NOT_FOUND"
        elif "not valid json" in lower:
            code = "INVALID_JSON"

        advice = (
            "Check vLLM is running, verify base_url includes /v1, verify host:port, "
            "and verify --served-model-name matches configured model_name."
        )
        raise LLMInvokeError(f"[vLLM] {code} at {url}: {raw}. {advice}") from exc
