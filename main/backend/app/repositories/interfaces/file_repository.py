from abc import ABC, abstractmethod
from typing import Optional
from app.models.entities import FileRecord


class FileRepository(ABC):
    @abstractmethod
    def create(self, file_record: FileRecord) -> FileRecord:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, file_id: str) -> Optional[FileRecord]:
        raise NotImplementedError

    @abstractmethod
    def list_by_task(self, task_id: str) -> list[FileRecord]:
        raise NotImplementedError
