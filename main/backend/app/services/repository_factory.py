from dataclasses import dataclass
from pathlib import Path

from app.repositories.json_impl import (
    ExcelMirrorStore,
    JsonAgentRunRepository,
    JsonFileRepository,
    JsonOutputVersionRepository,
    JsonProviderConfigRepository,
    JsonSessionRepository,
    JsonSkillCallRepository,
    JsonTaskEventRepository,
    JsonTaskRepository,
    JsonUserRepository,
    JsonUserSettingsRepository,
)


@dataclass
class RepositoryBundle:
    tasks: JsonTaskRepository
    files: JsonFileRepository
    providers: JsonProviderConfigRepository
    outputs: JsonOutputVersionRepository
    agent_runs: JsonAgentRunRepository
    skill_calls: JsonSkillCallRepository
    users: JsonUserRepository
    sessions: JsonSessionRepository
    task_events: JsonTaskEventRepository
    user_settings: JsonUserSettingsRepository
    excel_mirror: ExcelMirrorStore


def build_repository_bundle(base_dir: Path) -> RepositoryBundle:
    repo_dir = base_dir / "repo_data"
    excel_path = base_dir / "repo_data" / "snapshot.xlsx"
    repo_dir.mkdir(parents=True, exist_ok=True)

    return RepositoryBundle(
        tasks=JsonTaskRepository(repo_dir),
        files=JsonFileRepository(repo_dir),
        providers=JsonProviderConfigRepository(repo_dir),
        outputs=JsonOutputVersionRepository(repo_dir),
        agent_runs=JsonAgentRunRepository(repo_dir),
        skill_calls=JsonSkillCallRepository(repo_dir),
        users=JsonUserRepository(repo_dir),
        sessions=JsonSessionRepository(repo_dir),
        task_events=JsonTaskEventRepository(repo_dir),
        user_settings=JsonUserSettingsRepository(repo_dir),
        excel_mirror=ExcelMirrorStore(excel_path),
    )
