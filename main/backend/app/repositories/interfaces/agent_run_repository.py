from abc import ABC, abstractmethod
from app.models.entities import AgentRun


class AgentRunRepository(ABC):
    @abstractmethod
    def create(self, run: AgentRun) -> AgentRun:
        raise NotImplementedError

    @abstractmethod
    def list_by_task(self, task_id: str) -> list[AgentRun]:
        raise NotImplementedError
