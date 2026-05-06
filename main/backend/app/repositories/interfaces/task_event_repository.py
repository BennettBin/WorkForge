from abc import ABC, abstractmethod

from app.models.entities import TaskEvent


class TaskEventRepository(ABC):
    @abstractmethod
    def create(self, event: TaskEvent) -> TaskEvent:
        raise NotImplementedError

    @abstractmethod
    def list_by_task(self, task_id: str) -> list[TaskEvent]:
        raise NotImplementedError
