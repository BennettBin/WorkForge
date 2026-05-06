from dataclasses import dataclass
from typing import Literal
from typing import Optional

from app.models.entities import LLMProviderConfig
from app.services.llm_provider import OllamaConfig
from app.services.repository_factory import RepositoryBundle


StageType = Literal["planning", "generation", "review", "export"]


@dataclass
class ModelDecision:
    stage: StageType
    provider_type: str
    model_name: str
    base_url: Optional[str]
    source: str


class ModelRouter:
    def __init__(self, repos: RepositoryBundle):
        self.repos = repos

    def pick(self, user_id: str, stage: StageType) -> ModelDecision:
        cfg = self.repos.providers.get_default_for_user(user_id)
        if cfg is None:
            cfg = self._ollama_default(user_id)
            source = "system_default"
        else:
            source = "user_default"

        return ModelDecision(
            stage=stage,
            provider_type=cfg.provider_type,
            model_name=cfg.model_name,
            base_url=cfg.base_url,
            source=source,
        )

    def _ollama_default(self, user_id: str) -> LLMProviderConfig:
        default = OllamaConfig()
        return LLMProviderConfig(
            provider_id="default_ollama_local",
            user_id=user_id,
            provider_type="ollama",
            display_name="Ollama Local (Default)",
            base_url=default.base_url,
            model_name=default.chat_model,
            chat_model=default.chat_model,
            embedding_model=default.embedding_model,
            is_default=True,
        )
