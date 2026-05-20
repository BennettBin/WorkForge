from app.services.llm_runtime.text_generator import LLMInvokeError, LLMTextGenerator


def test_huggingface_provider_uses_vllm_openai_compatible_route(monkeypatch):
    generator = LLMTextGenerator()
    calls = {"openai_compatible": 0}

    def fake_openai_compatible(base_url, model_name, prompt, api_key, timeout_seconds):
        calls["openai_compatible"] += 1
        assert base_url == "http://127.0.0.1:8000/v1"
        assert model_name == "meta-llama/Meta-Llama-3.1-8B-Instruct"
        assert prompt == "hello"
        assert api_key is None
        assert timeout_seconds == 30
        return "ok-from-vllm"

    def fake_get_json(url, headers, timeout_seconds):
        assert url == "http://127.0.0.1:8000/v1/models"
        return {"data": [{"id": "meta-llama/Meta-Llama-3.1-8B-Instruct"}]}

    monkeypatch.setattr(generator, "_get_json", fake_get_json)
    monkeypatch.setattr(generator, "_openai_compatible_chat", fake_openai_compatible)

    output = generator.generate(
        provider_type="huggingface",
        base_url="http://127.0.0.1:8000/v1",
        model_name="meta-llama/Meta-Llama-3.1-8B-Instruct",
        prompt="hello",
        api_key=None,
        timeout_seconds=30,
    )
    assert output == "ok-from-vllm"
    assert calls["openai_compatible"] == 1


def test_vllm_provider_resolves_model_from_models_endpoint(monkeypatch):
    generator = LLMTextGenerator()

    def fake_get_json(url, headers, timeout_seconds):
        assert url == "http://127.0.0.1:8000/v1/models"
        return {"data": [{"id": "D:/pycharm/LLMs/Qwen3.5-9B-Base"}]}

    def fake_openai_compatible(base_url, model_name, prompt, api_key, timeout_seconds):
        assert base_url == "http://127.0.0.1:8000/v1"
        assert model_name == "D:/pycharm/LLMs/Qwen3.5-9B-Base"
        assert prompt == "hello"
        return "ok-vllm"

    monkeypatch.setattr(generator, "_get_json", fake_get_json)
    monkeypatch.setattr(generator, "_openai_compatible_chat", fake_openai_compatible)

    output = generator.generate(
        provider_type="vllm",
        base_url="http://127.0.0.1:8000/v1",
        model_name=r"D:\pycharm\LLMs\Qwen3.5-9B-Base",
        prompt="hello",
        api_key=None,
        timeout_seconds=30,
    )
    assert output == "ok-vllm"


def test_vllm_provider_retries_with_available_model_when_requested_model_rejected(monkeypatch):
    generator = LLMTextGenerator()
    calls = {"n": 0}

    def fake_get_json(url, headers, timeout_seconds):
        return {"data": [{"id": "served-model-id"}]}

    def fake_openai_compatible(base_url, model_name, prompt, api_key, timeout_seconds):
        calls["n"] += 1
        if calls["n"] == 1:
            raise LLMInvokeError("LLM HTTPError 400: model not found")
        assert model_name == "served-model-id"
        return "ok-after-retry"

    monkeypatch.setattr(generator, "_get_json", fake_get_json)
    monkeypatch.setattr(generator, "_openai_compatible_chat", fake_openai_compatible)

    output = generator._vllm_chat(
        base_url="http://127.0.0.1:8000/v1",
        model_name=r"D:\pycharm\LLMs\Qwen3.5-9B-Base",
        prompt="hello",
        api_key=None,
        timeout_seconds=30,
    )
    assert output == "ok-after-retry"


def test_vllm_provider_formats_connection_refused_error(monkeypatch):
    generator = LLMTextGenerator()

    def fake_get_json(url, headers, timeout_seconds):
        raise LLMInvokeError("LLM request failed: [WinError 10061] No connection could be made because the target machine actively refused it")

    monkeypatch.setattr(generator, "_get_json", fake_get_json)

    try:
        generator._vllm_chat(
            base_url="http://127.0.0.1:8000/v1",
            model_name="qwen3.5-9b",
            prompt="hello",
            api_key=None,
            timeout_seconds=30,
        )
        assert False, "Expected LLMInvokeError"
    except LLMInvokeError as exc:
        msg = str(exc)
        assert msg.startswith("[vLLM] CONNECTION_REFUSED")
        assert "http://127.0.0.1:8000/v1/models" in msg
        assert "verify base_url includes /v1" in msg
