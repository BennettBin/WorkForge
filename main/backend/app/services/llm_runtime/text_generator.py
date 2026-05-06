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
        # HuggingFace provider in WorkForge is executed through a vLLM OpenAI-compatible server
        # that serves locally downloaded HF models.
        return self._openai_compatible_chat(
            base_url=base_url,
            model_name=model_name,
            prompt=prompt,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )

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
