from abc import ABC, abstractmethod
from typing import Optional
from app.models.entities import LLMProviderConfig


class ProviderConfigRepository(ABC):
    @abstractmethod
    def upsert(self, config: LLMProviderConfig) -> LLMProviderConfig:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, provider_id: str) -> Optional[LLMProviderConfig]:
        raise NotImplementedError

    @abstractmethod
    def get_default_for_user(self, user_id: str) -> Optional[LLMProviderConfig]:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[LLMProviderConfig]:
        raise NotImplementedError
