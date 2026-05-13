from datetime import datetime, timedelta, timezone
import hashlib

from app.models.entities import Session, User
from app.models.requests import LoginRequest, RegisterRequest, UpdatePasswordRequest, UpdateProfileRequest
from app.services.repository_factory import RepositoryBundle
from app.utils.ids import new_id


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, repos: RepositoryBundle):
        self.repos = repos

    def register(self, payload: RegisterRequest) -> User:
        username = payload.username.strip()
        if self.repos.users.get_by_username(username) is not None:
            raise ValueError("Username already registered.")

        user = User(
            user_id=new_id("user"),
            # Keep email field for existing data model; generate deterministic internal email from username.
            email=f"{username.lower()}@local.workforge",
            username=username,
            password_hash=_hash_password(payload.password),
        )
        self.repos.users.create(user)
        return user

    def ensure_admin_account(self, email: str, username: str, password: str) -> User:
        normalized_email = email.strip().lower()
        existing = self.repos.users.get_by_email(normalized_email)
        if existing is not None:
            return existing

        admin = User(
            user_id=new_id("user"),
            email=normalized_email,
            username=username.strip(),
            password_hash=_hash_password(password),
        )
        self.repos.users.create(admin)
        return admin

    def login(self, payload: LoginRequest) -> dict:
        account = payload.account.strip()
        user = self.repos.users.get_by_username(account)
        if user is None:
            user = self.repos.users.get_by_email(account.lower())
        if user is None:
            raise ValueError("User not found.")
        if user.password_hash != _hash_password(payload.password):
            raise ValueError("Invalid password.")

        session = Session(
            session_id=new_id("sess"),
            user_id=user.user_id,
            token=new_id("tok"),
            expires_at=_utc_now() + timedelta(days=7),
        )
        self.repos.sessions.create(session)
        return {"token": session.token, "user_id": user.user_id, "username": user.username, "email": user.email}

    def validate_token(self, token: str) -> User:
        if not token:
            raise ValueError("Missing token.")
        session = self.repos.sessions.get_by_token(token)
        if session is None:
            raise ValueError("Session not found.")
        if session.expires_at < _utc_now():
            self.repos.sessions.delete(session.session_id)
            raise ValueError("Session expired.")
        user = self.repos.users.get_by_id(session.user_id)
        if user is None:
            raise ValueError("User not found.")
        return user

    def update_profile(self, token: str, payload: UpdateProfileRequest) -> User:
        user = self.validate_token(token)
        updated = user.model_copy(update={"username": payload.username.strip(), "updated_at": _utc_now()})
        self.repos.users.update(updated)
        return updated

    def update_password(self, token: str, payload: UpdatePasswordRequest) -> None:
        user = self.validate_token(token)
        if user.password_hash != _hash_password(payload.old_password):
            raise ValueError("Old password is incorrect.")
        updated = user.model_copy(update={"password_hash": _hash_password(payload.new_password), "updated_at": _utc_now()})
        self.repos.users.update(updated)
