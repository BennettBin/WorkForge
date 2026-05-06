from abc import ABC, abstractmethod
from app.models.entities import SkillCall


class SkillCallRepository(ABC):
    @abstractmethod
    def create(self, call: SkillCall) -> SkillCall:
        raise NotImplementedError

    @abstractmethod
    def list_by_task(self, task_id: str) -> list[SkillCall]:
        raise NotImplementedError
