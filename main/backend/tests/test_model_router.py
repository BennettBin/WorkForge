from pathlib import Path
from tempfile import TemporaryDirectory

from app.models.entities import LLMProviderConfig
from app.services.model_router import ModelRouter
from app.services.repository_factory import build_repository_bundle


def test_model_router_uses_system_default_ollama_without_user_config():
    with TemporaryDirectory() as temp_dir:
        repos = build_repository_bundle(Path(temp_dir))
        router = ModelRouter(repos)
        decision = router.pick("u-1", "generation")
        assert decision.provider_type == "ollama"
        assert decision.model_name == "qwen3:8b"
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
