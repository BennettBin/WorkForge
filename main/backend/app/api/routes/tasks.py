from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.models import ApiResponse, CreateTaskRequest, ParseTaskRequest, RunTaskRequest
from app.models.requests import ManualStatusUpdateRequest, RevisionRequest
from app.services.task_manager import build_task_service, TaskService

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])
PROJECT_MAIN_DIR = Path(__file__).resolve().parents[4]
LEGACY_STORAGE_ROOTS = [
    PROJECT_MAIN_DIR / "backend" / "main" / "storage",
    PROJECT_MAIN_DIR / "backend" / "runtime_data" / "storage",
]


def _resolve_output_path(path: Path) -> Path:
    if path.exists():
        return path

    # Legacy -> current storage remap
    for legacy_root in LEGACY_STORAGE_ROOTS:
        try:
            relative = path.relative_to(legacy_root)
        except ValueError:
            continue
        candidate = settings.data_dir / relative
        if candidate.exists():
            return candidate

    # Current -> legacy storage remap
    try:
        relative_current = path.relative_to(settings.data_dir)
    except ValueError:
        relative_current = None
    if relative_current is not None:
        for legacy_root in LEGACY_STORAGE_ROOTS:
            candidate = legacy_root / relative_current
            if candidate.exists():
                return candidate

    return path


def _task_service(request: Request) -> TaskService:
    return build_task_service(request.app.state.repositories)


@router.post("", response_model=ApiResponse)
def create_task(payload: CreateTaskRequest, service: TaskService = Depends(_task_service)) -> ApiResponse:
    task = service.create_task(payload)
    return ApiResponse(success=True, data=task.model_dump(mode="json"))


@router.get("/user/{user_id}", response_model=ApiResponse)
def list_tasks_by_user(user_id: str, service: TaskService = Depends(_task_service)) -> ApiResponse:
    items = [t.model_dump(mode="json") for t in service.repos.tasks.list_by_user(user_id)]
    return ApiResponse(success=True, data={"items": items})


@router.get("/{task_id}", response_model=ApiResponse)
def get_task(task_id: str, service: TaskService = Depends(_task_service)) -> ApiResponse:
    task = service.repos.tasks.get_by_id(task_id)
    if task is None:
        raise ValueError("Task not found.")
    files = [f.model_dump(mode="json") for f in service.repos.files.list_by_task(task_id)]
    outputs = [o.model_dump(mode="json") for o in service.repos.outputs.list_versions(task_id)]
    agent_runs = [r.model_dump(mode="json") for r in service.repos.agent_runs.list_by_task(task_id)]
    skill_calls = [s.model_dump(mode="json") for s in service.repos.skill_calls.list_by_task(task_id)]
    events = [e.model_dump(mode="json") for e in service.repos.task_events.list_by_task(task_id)]
    return ApiResponse(
        success=True,
        data={
            "task": task.model_dump(mode="json"),
            "files": files,
            "outputs": outputs,
            "agent_runs": agent_runs,
            "skill_calls": skill_calls,
            "events": events,
        },
    )


@router.post("/{task_id}/upload", response_model=ApiResponse)
def upload_task_file(
    task_id: str,
    upload: UploadFile = File(...),
    service: TaskService = Depends(_task_service),
) -> ApiResponse:
    record = service.upload_file(task_id, upload)
    return ApiResponse(success=True, data=record.model_dump(mode="json"))


@router.post("/{task_id}/parse", response_model=ApiResponse)
def parse_task_file(task_id: str, payload: ParseTaskRequest, service: TaskService = Depends(_task_service)) -> ApiResponse:
    record = service.parse_task_file(task_id, force=payload.force)
    return ApiResponse(success=True, data=record.model_dump(mode="json"))


@router.post("/{task_id}/run", response_model=ApiResponse)
def run_task(task_id: str, payload: RunTaskRequest, service: TaskService = Depends(_task_service)) -> ApiResponse:
    result = service.run_task(
        task_id,
        rerun=payload.rerun,
        require_llm=payload.require_llm,
        llm_timeout_seconds=payload.llm_timeout_seconds,
    )
    return ApiResponse(success=True, data=result)


@router.post("/{task_id}/status", response_model=ApiResponse)
def update_status(
    task_id: str,
    payload: ManualStatusUpdateRequest,
    service: TaskService = Depends(_task_service),
) -> ApiResponse:
    task = service.repos.tasks.update_status(task_id, payload.status)
    if task is None:
        raise ValueError("Task not found.")
    return ApiResponse(
        success=True,
        data={"task": task.model_dump(mode="json"), "reason": payload.reason},
    )


@router.get("/{task_id}/download/latest", response_model=ApiResponse)
def download_latest(task_id: str, service: TaskService = Depends(_task_service)) -> ApiResponse:
    latest = service.repos.outputs.get_latest(task_id)
    if latest is None:
        raise ValueError("No output found for task.")
    path = _resolve_output_path(Path(latest.file_path))
    return ApiResponse(
        success=True,
        data={
            "output_id": latest.output_id,
            "version": latest.version,
            "file_path": str(path.resolve()),
            "download_url": f"/v1/tasks/{task_id}/download/{latest.version}/file",
            "exists": path.exists(),
        },
    )


@router.get("/{task_id}/download/{version}", response_model=ApiResponse)
def download_version(task_id: str, version: int, service: TaskService = Depends(_task_service)) -> ApiResponse:
    versions = service.repos.outputs.list_versions(task_id)
    target = None
    for v in versions:
        if v.version == version:
            target = v
            break
    if target is None:
        raise ValueError("Version not found.")
    path = _resolve_output_path(Path(target.file_path))
    return ApiResponse(
        success=True,
        data={
            "output_id": target.output_id,
            "version": target.version,
            "file_path": str(path.resolve()),
            "download_url": f"/v1/tasks/{task_id}/download/{target.version}/file",
            "exists": path.exists(),
        },
    )


@router.get("/{task_id}/download/latest/file")
def download_latest_file(task_id: str, service: TaskService = Depends(_task_service)) -> FileResponse:
    latest = service.repos.outputs.get_latest(task_id)
    if latest is None:
        raise ValueError("No output found for task.")
    path = _resolve_output_path(Path(latest.file_path))
    if not path.exists():
        raise ValueError(f"Output file missing on disk: {path}")
    return FileResponse(path=str(path), filename=path.name, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")


@router.get("/{task_id}/download/{version}/file")
def download_version_file(task_id: str, version: int, service: TaskService = Depends(_task_service)) -> FileResponse:
    versions = service.repos.outputs.list_versions(task_id)
    target = None
    for v in versions:
        if v.version == version:
            target = v
            break
    if target is None:
        raise ValueError("Version not found.")
    path = _resolve_output_path(Path(target.file_path))
    if not path.exists():
        raise ValueError(f"Output file missing on disk: {path}")
    return FileResponse(path=str(path), filename=path.name, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")


@router.get("/{task_id}/versions", response_model=ApiResponse)
def list_versions(task_id: str, service: TaskService = Depends(_task_service)) -> ApiResponse:
    return ApiResponse(success=True, data={"items": service.list_versions(task_id)})


@router.get("/{task_id}/versions/compare", response_model=ApiResponse)
def compare_versions(task_id: str, from_version: int, to_version: int, service: TaskService = Depends(_task_service)) -> ApiResponse:
    data = service.compare_versions(task_id, from_version, to_version)
    return ApiResponse(success=True, data=data)


@router.post("/{task_id}/versions/rollback/{target_version}", response_model=ApiResponse)
def rollback_version(task_id: str, target_version: int, service: TaskService = Depends(_task_service)) -> ApiResponse:
    data = service.rollback_to_version(task_id, target_version)
    return ApiResponse(success=True, data=data)


@router.post("/{task_id}/revisions", response_model=ApiResponse)
def revise_task(task_id: str, payload: RevisionRequest, service: TaskService = Depends(_task_service)) -> ApiResponse:
    data = service.revise_page(task_id, payload.page_index, payload.instruction)
    return ApiResponse(success=True, data=data)


@router.post("/{task_id}/cache/clear", response_model=ApiResponse)
def clear_task_cache(task_id: str, service: TaskService = Depends(_task_service)) -> ApiResponse:
    data = service.clear_task_cache(task_id)
    return ApiResponse(success=True, data=data)
