from dataclasses import dataclass
from typing import Literal
from typing import Optional

from app.models.entities import LLMProviderConfig
from app.services.llm_provider import VllmConfig
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
        if cfg is None or not self._is_usable(cfg):
            cfg = self._vllm_default(user_id)
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

    def _vllm_default(self, user_id: str) -> LLMProviderConfig:
        default = VllmConfig()
        return LLMProviderConfig(
            provider_id="default_vllm_local",
            user_id=user_id,
            provider_type="vllm",
            display_name="vLLM Local (Default)",
            base_url=default.base_url,
            model_name=default.chat_model,
            chat_model=default.chat_model,
            is_default=True,
        )

    @staticmethod
    def _is_usable(cfg: LLMProviderConfig) -> bool:
        if not cfg.provider_type or not str(cfg.provider_type).strip():
            return False
        if not cfg.model_name or not str(cfg.model_name).strip():
            return False
        return True
