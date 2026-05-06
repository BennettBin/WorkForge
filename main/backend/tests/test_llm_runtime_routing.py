from app.services.llm_runtime.text_generator import LLMTextGenerator


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
