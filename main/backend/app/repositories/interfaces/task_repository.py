from abc import ABC, abstractmethod
from typing import Optional
from app.models.entities import Task, TaskStatus


class TaskRepository(ABC):
    @abstractmethod
    def create(self, task: Task) -> Task:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, task_id: str) -> Optional[Task]:
        raise NotImplementedError

    @abstractmethod
    def update_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[Task]:
        raise NotImplementedError
