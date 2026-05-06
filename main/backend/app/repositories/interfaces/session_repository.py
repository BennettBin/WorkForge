from abc import ABC, abstractmethod
from typing import Optional

from app.models.entities import Session


class SessionRepository(ABC):
    @abstractmethod
    def create(self, session: Session) -> Session:
        raise NotImplementedError

    @abstractmethod
    def get_by_token(self, token: str) -> Optional[Session]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, session_id: str) -> None:
        raise NotImplementedError
