from pathlib import Path
from tempfile import TemporaryDirectory

from app.models.entities import LLMProviderConfig
from app.services.model_router import ModelRouter
from app.services.repository_factory import build_repository_bundle


def test_model_router_uses_system_default_vllm_without_user_config():
    with TemporaryDirectory() as temp_dir:
        repos = build_repository_bundle(Path(temp_dir))
        router = ModelRouter(repos)
        decision = router.pick("u-1", "generation")
        assert decision.provider_type == "vllm"
        assert decision.model_name == "Qwen/Qwen2.5-7B-Instruct"
        assert decision.base_url == "http://127.0.0.1:8000/v1"
        assert decision.source == "system_default"


def test_model_router_uses_user_default_config():
    with TemporaryDirectory() as temp_dir:
        repos = build_repository_bundle(Path(temp_dir))
        repos.providers.upsert(
            LLMProviderConfig(
                provider_id="p1",
                user_id="u-1",
                provider_type="ollama",
                display_name="Local Ollama",
                base_url="http://localhost:11434",
                model_name="qwen3:8b",
                is_default=True,
            )
        )
        router = ModelRouter(repos)
        decision = router.pick("u-1", "review")
        assert decision.provider_type == "ollama"
        assert decision.model_name == "qwen3:8b"
        assert decision.source == "user_default"


def test_model_router_switches_immediately_after_default_change():
    with TemporaryDirectory() as temp_dir:
        repos = build_repository_bundle(Path(temp_dir))
        repos.providers.upsert(
            LLMProviderConfig(
                provider_id="p1",
                user_id="u-1",
                provider_type="ollama",
                display_name="Local Ollama",
                base_url="http://localhost:11434",
                model_name="qwen3:8b",
                is_default=True,
            )
        )
        router = ModelRouter(repos)
        first = router.pick("u-1", "generation")
        assert first.provider_type == "ollama"
        assert first.model_name == "qwen3:8b"
        assert first.source == "user_default"

        repos.providers.upsert(
            LLMProviderConfig(
                provider_id="p2",
                user_id="u-1",
                provider_type="vllm",
                display_name="User vLLM",
                base_url="http://127.0.0.1:8000/v1",
                model_name="Qwen/Qwen2.5-14B-Instruct",
                is_default=True,
            )
        )

        second = router.pick("u-1", "generation")
        assert second.provider_type == "vllm"
        assert second.model_name == "Qwen/Qwen2.5-14B-Instruct"
        assert second.source == "user_default"


def test_model_router_falls_back_when_user_default_is_invalid():
    with TemporaryDirectory() as temp_dir:
        repos = build_repository_bundle(Path(temp_dir))
        repos.providers.upsert(
            LLMProviderConfig(
                provider_id="p-invalid",
                user_id="u-1",
                provider_type="vllm",
                display_name="Broken Config",
                base_url="http://127.0.0.1:8000/v1",
                model_name="",
                is_default=True,
            )
        )
        router = ModelRouter(repos)
        decision = router.pick("u-1", "review")
        assert decision.provider_type == "vllm"
        assert decision.model_name == "Qwen/Qwen2.5-7B-Instruct"
        assert decision.source == "system_default"
