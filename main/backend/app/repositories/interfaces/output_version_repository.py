from abc import ABC, abstractmethod
from typing import Optional
from app.models.entities import OutputFile


class OutputVersionRepository(ABC):
    @abstractmethod
    def create(self, output_file: OutputFile) -> OutputFile:
        raise NotImplementedError

    @abstractmethod
    def get_latest(self, task_id: str) -> Optional[OutputFile]:
        raise NotImplementedError

    @abstractmethod
    def list_versions(self, task_id: str) -> list[OutputFile]:
        raise NotImplementedError
