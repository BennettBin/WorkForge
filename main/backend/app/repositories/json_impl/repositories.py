from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models.entities import (
    AgentRun,
    FileRecord,
    LLMProviderConfig,
    OutputFile,
    Session,
    SkillCall,
    Task,
    TaskEvent,
    TaskStatus,
    User,
    UserSettings,
)
from app.repositories.interfaces import (
    AgentRunRepository,
    FileRepository,
    OutputVersionRepository,
    ProviderConfigRepository,
    SessionRepository,
    SkillCallRepository,
    TaskEventRepository,
    TaskRepository,
    UserRepository,
    UserSettingsRepository,
)
from app.repositories.json_impl.store import JsonCollectionStore


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JsonTaskRepository(TaskRepository):
    def __init__(self, data_dir: Path):
        self.store = JsonCollectionStore(data_dir / "tasks.json")

    def create(self, task: Task) -> Task:
        rows = self.store.read_all()
        rows.append(task.model_dump(mode="json"))
        self.store.write_all(rows)
        return task

    def get_by_id(self, task_id: str) -> Optional[Task]:
        for row in self.store.read_all():
            if row["task_id"] == task_id:
                return Task.model_validate(row)
        return None

    def update_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        rows = self.store.read_all()
        updated: Optional[Task] = None
        for row in rows:
            if row["task_id"] == task_id:
                row["status"] = status
                row["updated_at"] = _utc_now_iso()
                updated = Task.model_validate(row)
                break
        if updated:
            self.store.write_all(rows)
        return updated

    def list_by_user(self, user_id: str) -> list[Task]:
        return [Task.model_validate(row) for row in self.store.read_all() if row["user_id"] == user_id]


class JsonFileRepository(FileRepository):
    def __init__(self, data_dir: Path):
        self.store = JsonCollectionStore(data_dir / "files.json")

    def create(self, file_record: FileRecord) -> FileRecord:
        rows = self.store.read_all()
        task_files = [r for r in rows if r["task_id"] == file_record.task_id]
        if len(task_files) >= 1:
            raise ValueError("A task can bind at most one source file in MVP-1.")
        rows.append(file_record.model_dump(mode="json"))
        self.store.write_all(rows)
        return file_record

    def get_by_id(self, file_id: str) -> Optional[FileRecord]:
        for row in self.store.read_all():
            if row["file_id"] == file_id:
                return FileRecord.model_validate(row)
        return None

    def list_by_task(self, task_id: str) -> list[FileRecord]:
        return [FileRecord.model_validate(row) for row in self.store.read_all() if row["task_id"] == task_id]


class JsonProviderConfigRepository(ProviderConfigRepository):
    def __init__(self, data_dir: Path):
        self.store = JsonCollectionStore(data_dir / "provider_configs.json")

    def upsert(self, config: LLMProviderConfig) -> LLMProviderConfig:
        rows = self.store.read_all()
        upserted = False
        for row in rows:
            if row["provider_id"] == config.provider_id:
                row.update(config.model_dump(mode="json"))
                row["updated_at"] = _utc_now_iso()
                upserted = True
                break
        if not upserted:
            rows.append(config.model_dump(mode="json"))

        if config.is_default:
            for row in rows:
                if row["user_id"] == config.user_id and row["provider_id"] != config.provider_id:
                    row["is_default"] = False

        self.store.write_all(rows)
        return config

    def get_by_id(self, provider_id: str) -> Optional[LLMProviderConfig]:
        for row in self.store.read_all():
            if row["provider_id"] == provider_id:
                return LLMProviderConfig.model_validate(row)
        return None

    def get_default_for_user(self, user_id: str) -> Optional[LLMProviderConfig]:
        for row in self.store.read_all():
            if row["user_id"] == user_id and row.get("is_default"):
                return LLMProviderConfig.model_validate(row)
        return None

    def list_by_user(self, user_id: str) -> list[LLMProviderConfig]:
        return [LLMProviderConfig.model_validate(row) for row in self.store.read_all() if row["user_id"] == user_id]


class JsonOutputVersionRepository(OutputVersionRepository):
    def __init__(self, data_dir: Path):
        self.store = JsonCollectionStore(data_dir / "output_versions.json")

    def create(self, output_file: OutputFile) -> OutputFile:
        rows = self.store.read_all()
        for row in rows:
            if row["task_id"] == output_file.task_id and row["version"] == output_file.version:
                raise ValueError("Duplicate output version for the same task.")
        rows.append(output_file.model_dump(mode="json"))
        self.store.write_all(rows)
        return output_file

    def get_latest(self, task_id: str) -> Optional[OutputFile]:
        versions = self.list_versions(task_id)
        if not versions:
            return None
        return sorted(versions, key=lambda v: v.version, reverse=True)[0]

    def list_versions(self, task_id: str) -> list[OutputFile]:
        versions = [OutputFile.model_validate(row) for row in self.store.read_all() if row["task_id"] == task_id]
        return sorted(versions, key=lambda v: v.version)


class JsonAgentRunRepository(AgentRunRepository):
    def __init__(self, data_dir: Path):
        self.store = JsonCollectionStore(data_dir / "agent_runs.json")

    def create(self, run: AgentRun) -> AgentRun:
        rows = self.store.read_all()
        rows.append(run.model_dump(mode="json"))
        self.store.write_all(rows)
        return run

    def list_by_task(self, task_id: str) -> list[AgentRun]:
        return [AgentRun.model_validate(row) for row in self.store.read_all() if row["task_id"] == task_id]


class JsonSkillCallRepository(SkillCallRepository):
    def __init__(self, data_dir: Path):
        self.store = JsonCollectionStore(data_dir / "skill_calls.json")

    def create(self, call: SkillCall) -> SkillCall:
        rows = self.store.read_all()
        rows.append(call.model_dump(mode="json"))
        self.store.write_all(rows)
        return call

    def list_by_task(self, task_id: str) -> list[SkillCall]:
        return [SkillCall.model_validate(row) for row in self.store.read_all() if row["task_id"] == task_id]


class JsonUserRepository(UserRepository):
    def __init__(self, data_dir: Path):
        self.store = JsonCollectionStore(data_dir / "users.json")

    def create(self, user: User) -> User:
        rows = self.store.read_all()
        if any(r["email"].lower() == user.email.lower() for r in rows):
            raise ValueError("Email already registered.")
        if any(str(r.get("username", "")).lower() == user.username.lower() for r in rows):
            raise ValueError("Username already registered.")
        rows.append(user.model_dump(mode="json"))
        self.store.write_all(rows)
        return user

    def get_by_id(self, user_id: str) -> Optional[User]:
        for row in self.store.read_all():
            if row["user_id"] == user_id:
                return User.model_validate(row)
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        for row in self.store.read_all():
            if row["email"].lower() == email.lower():
                return User.model_validate(row)
        return None

    def get_by_username(self, username: str) -> Optional[User]:
        key = username.lower()
        for row in self.store.read_all():
            if str(row.get("username", "")).lower() == key:
                return User.model_validate(row)
        return None

    def update(self, user: User) -> User:
        rows = self.store.read_all()
        for row in rows:
            if row["user_id"] == user.user_id:
                row.update(user.model_dump(mode="json"))
                row["updated_at"] = _utc_now_iso()
                self.store.write_all(rows)
                return user
        raise ValueError("User not found.")


class JsonSessionRepository(SessionRepository):
    def __init__(self, data_dir: Path):
        self.store = JsonCollectionStore(data_dir / "sessions.json")

    def create(self, session: Session) -> Session:
        rows = self.store.read_all()
        rows.append(session.model_dump(mode="json"))
        self.store.write_all(rows)
        return session

    def get_by_token(self, token: str) -> Optional[Session]:
        for row in self.store.read_all():
            if row["token"] == token:
                return Session.model_validate(row)
        return None

    def delete(self, session_id: str) -> None:
        rows = self.store.read_all()
        rows = [r for r in rows if r["session_id"] != session_id]
        self.store.write_all(rows)


class JsonTaskEventRepository(TaskEventRepository):
    def __init__(self, data_dir: Path):
        self.store = JsonCollectionStore(data_dir / "task_events.json")

    def create(self, event: TaskEvent) -> TaskEvent:
        rows = self.store.read_all()
        rows.append(event.model_dump(mode="json"))
        self.store.write_all(rows)
        return event

    def list_by_task(self, task_id: str) -> list[TaskEvent]:
        rows = [TaskEvent.model_validate(r) for r in self.store.read_all() if r["task_id"] == task_id]
        return sorted(rows, key=lambda r: r.created_at)


class JsonUserSettingsRepository(UserSettingsRepository):
    def __init__(self, data_dir: Path):
        self.store = JsonCollectionStore(data_dir / "user_settings.json")

    def get_by_user(self, user_id: str) -> Optional[UserSettings]:
        for row in self.store.read_all():
            if row["user_id"] == user_id:
                return UserSettings.model_validate(row)
        return None

    def upsert(self, settings: UserSettings) -> UserSettings:
        rows = self.store.read_all()
        found = False
        payload = settings.model_dump(mode="json")
        for row in rows:
            if row["user_id"] == settings.user_id:
                row.update(payload)
                row["updated_at"] = _utc_now_iso()
                found = True
                break
        if not found:
            rows.append(payload)
        self.store.write_all(rows)
        return settings
