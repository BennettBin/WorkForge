from pathlib import Path
import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Header, Request, UploadFile
from fastapi.responses import FileResponse

from app.agents.coordinator import CoordinatorAgent
from app.config import settings
from app.models import ApiResponse, CreateTaskRequest, InferTemplateSettingsRequest, InferTaskTypeRequest, ParseTaskRequest, RunTaskRequest, TemplateRecoveryCompleteRequest, TemplateRecoveryResumeRequest
from app.models.entities import Task, User
from app.models.requests import CapabilityBuildRequest, ManualStatusUpdateRequest, RevisionRequest
from app.services.auth_service import AuthService
from app.services.model_router import ModelRouter
from app.services.skill_runtime import SkillExecutor
from app.services.task_manager import build_task_service, TaskService

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])
PROJECT_MAIN_DIR = Path(__file__).resolve().parents[4]
LEGACY_STORAGE_ROOTS = [
    PROJECT_MAIN_DIR / "backend" / "storage",
    PROJECT_MAIN_DIR / "backend" / "runtime_data" / "storage",
]
TEMPLATES_ROOT = PROJECT_MAIN_DIR / "backend" / "app" / "templates"
TEMPLATE_META_FILENAME = "template.meta.json"
TEMPLATE_PARAMS_FILENAME = "template.params.json"
TEMPLATE_RENDER_SCRIPT_FILENAME = "render_from_template.py"


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


def _token_from_header(authorization: Optional[str]) -> str:
    if not authorization:
        raise ValueError("Missing Authorization header.")
    if not authorization.lower().startswith("bearer "):
        raise ValueError("Authorization must be Bearer token.")
    return authorization[7:].strip()


def _current_user(request: Request, authorization: Optional[str] = Header(default=None)) -> User:
    token = _token_from_header(authorization)
    return AuthService(request.app.state.repositories).validate_token(token)


def _owned_task_or_raise(service: TaskService, task_id: str, user_id: str) -> Task:
    task = service.repos.tasks.get_by_id(task_id)
    if task is None:
        raise ValueError("Task not found.")
    if task.user_id != user_id:
        raise ValueError("Task not found.")
    return task


def _media_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pptx":
        return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    if suffix == ".md":
        return "text/markdown; charset=utf-8"
    if suffix == ".txt":
        return "text/plain; charset=utf-8"
    if suffix == ".json":
        return "application/json"
    if suffix == ".csv":
        return "text/csv; charset=utf-8"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        return f"image/{suffix.lstrip('.') if suffix != '.jpg' else 'jpeg'}"
    if suffix == ".py":
        return "text/x-python; charset=utf-8"
    return "application/octet-stream"


def _safe_template_file(path: Path) -> Path:
    resolved = path.resolve()
    root = TEMPLATES_ROOT.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("Template file path is invalid.") from exc
    return resolved


@router.post("", response_model=ApiResponse)
def create_task(
    payload: CreateTaskRequest,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    if payload.user_id != current_user.user_id:
        raise ValueError("User mismatch for task creation.")
    task = service.create_task(payload)
    return ApiResponse(success=True, data=task.model_dump(mode="json"))


@router.post("/infer-type", response_model=ApiResponse)
def infer_task_type(payload: InferTaskTypeRequest, request: Request, current_user: User = Depends(_current_user)) -> ApiResponse:
    coordinator = CoordinatorAgent(ModelRouter(request.app.state.repositories))
    user_id = payload.user_id or current_user.user_id
    if user_id != current_user.user_id:
        raise ValueError("User mismatch for task inference.")
    task_type = coordinator.infer_task_type(payload.requirement, user_id=user_id)
    return ApiResponse(success=True, data={"task_type": task_type})


@router.post("/template-generation/infer-settings", response_model=ApiResponse)
def infer_template_settings(payload: InferTemplateSettingsRequest, request: Request, current_user: User = Depends(_current_user)) -> ApiResponse:
    coordinator = CoordinatorAgent(ModelRouter(request.app.state.repositories))
    user_id = payload.user_id or current_user.user_id
    if user_id != current_user.user_id:
        raise ValueError("User mismatch for template settings inference.")
    settings_data = coordinator.infer_template_settings(payload.requirement, user_id=user_id)
    return ApiResponse(success=True, data=settings_data)


@router.get("/user/{user_id}", response_model=ApiResponse)
def list_tasks_by_user(
    user_id: str,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    if user_id != current_user.user_id:
        raise ValueError("User mismatch for task listing.")
    items = [t.model_dump(mode="json") for t in service.repos.tasks.list_by_user(user_id)]
    return ApiResponse(success=True, data={"items": items})


@router.get("/running/me", response_model=ApiResponse)
def list_running_tasks_me(
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    items = []
    for task in service.list_running_tasks_by_user(current_user.user_id):
        items.append(
            {
                "task_id": task.task_id,
                "status": task.status,
                "task_type": task.task_type,
                "user_requirement": task.user_requirement,
                "updated_at": task.updated_at,
            }
        )
    return ApiResponse(success=True, data={"items": items})


@router.get("/{task_id}", response_model=ApiResponse)
def get_task(task_id: str, service: TaskService = Depends(_task_service), current_user: User = Depends(_current_user)) -> ApiResponse:
    task = _owned_task_or_raise(service, task_id, current_user.user_id)
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
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    record = service.upload_file(task_id, upload)
    return ApiResponse(success=True, data=record.model_dump(mode="json"))


@router.post("/{task_id}/parse", response_model=ApiResponse)
def parse_task_file(
    task_id: str,
    payload: ParseTaskRequest,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    record = service.parse_task_file(task_id, force=payload.force)
    return ApiResponse(success=True, data=record.model_dump(mode="json"))


@router.post("/{task_id}/run", response_model=ApiResponse)
def run_task(
    task_id: str,
    payload: RunTaskRequest,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    result = service.run_task(
        task_id,
        rerun=payload.rerun,
        require_llm=payload.require_llm,
        llm_timeout_seconds=payload.llm_timeout_seconds,
        force_generic_direct=payload.force_generic_direct,
        capability_name=payload.capability_name,
    )
    return ApiResponse(success=True, data=result)


@router.get("/{task_id}/template-generation/recovery", response_model=ApiResponse)
def get_template_recovery(
    task_id: str,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    data = service.get_template_generation_recovery(task_id)
    return ApiResponse(success=True, data=data)


@router.post("/{task_id}/template-generation/recovery/complete", response_model=ApiResponse)
def complete_template_recovery(
    task_id: str,
    payload: TemplateRecoveryCompleteRequest,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    data = service.complete_template_generation_recovery(task_id, payload.fields)
    return ApiResponse(success=True, data=data)


@router.post("/{task_id}/template-generation/resume", response_model=ApiResponse)
def resume_template_recovery(
    task_id: str,
    payload: TemplateRecoveryResumeRequest,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    data = service.resume_template_generation_recovery(task_id, payload.resume_token, payload.user_filled_fields)
    return ApiResponse(success=True, data=data)


@router.post("/{task_id}/capabilities/bootstrap", response_model=ApiResponse)
def bootstrap_capability(
    task_id: str,
    payload: CapabilityBuildRequest,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    data = service.bootstrap_generic_capability(task_id, payload.capability_name, capability_spec=payload.capability_spec)
    return ApiResponse(success=True, data=data)


@router.post("/{task_id}/status", response_model=ApiResponse)
def update_status(
    task_id: str,
    payload: ManualStatusUpdateRequest,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    task = service.repos.tasks.update_status(task_id, payload.status)
    if task is None:
        raise ValueError("Task not found.")
    return ApiResponse(
        success=True,
        data={"task": task.model_dump(mode="json"), "reason": payload.reason},
    )


@router.get("/{task_id}/download/latest", response_model=ApiResponse)
def download_latest(task_id: str, service: TaskService = Depends(_task_service), current_user: User = Depends(_current_user)) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
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
def download_version(
    task_id: str,
    version: int,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
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
def download_latest_file(
    task_id: str,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> FileResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    latest = service.repos.outputs.get_latest(task_id)
    if latest is None:
        raise ValueError("No output found for task.")
    path = _resolve_output_path(Path(latest.file_path))
    if not path.exists():
        raise ValueError(f"Output file missing on disk: {path}")
    return FileResponse(path=str(path), filename=path.name, media_type=_media_type_for_path(path))


@router.get("/{task_id}/download/{version}/file")
def download_version_file(
    task_id: str,
    version: int,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> FileResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
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
    return FileResponse(path=str(path), filename=path.name, media_type=_media_type_for_path(path))


@router.get("/{task_id}/versions", response_model=ApiResponse)
def list_versions(
    task_id: str,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    return ApiResponse(success=True, data={"items": service.list_versions(task_id)})


@router.get("/{task_id}/versions/compare", response_model=ApiResponse)
def compare_versions(
    task_id: str,
    from_version: int,
    to_version: int,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    data = service.compare_versions(task_id, from_version, to_version)
    return ApiResponse(success=True, data=data)


@router.post("/{task_id}/versions/rollback/{target_version}", response_model=ApiResponse)
def rollback_version(
    task_id: str,
    target_version: int,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    data = service.rollback_to_version(task_id, target_version)
    return ApiResponse(success=True, data=data)


@router.post("/{task_id}/revisions", response_model=ApiResponse)
def revise_task(
    task_id: str,
    payload: RevisionRequest,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    data = service.revise_page(task_id, payload.page_index, payload.instruction)
    return ApiResponse(success=True, data=data)


@router.post("/{task_id}/cache/clear", response_model=ApiResponse)
def clear_task_cache(
    task_id: str,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    _owned_task_or_raise(service, task_id, current_user.user_id)
    data = service.clear_task_cache(task_id)
    return ApiResponse(success=True, data=data)


@router.get("/ppt/templates", response_model=ApiResponse)
def list_ppt_templates(service: TaskService = Depends(_task_service), current_user: User = Depends(_current_user)) -> ApiResponse:
    return ApiResponse(success=True, data={"items": service.list_ppt_templates()})


@router.get("/templates/{template_type}", response_model=ApiResponse)
def list_templates(
    template_type: str,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    return ApiResponse(success=True, data={"items": service.list_templates(template_type)})


@router.get("/{task_id}/template-preview", response_model=ApiResponse)
def get_template_preview(
    task_id: str,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    task = _owned_task_or_raise(service, task_id, current_user.user_id)
    if task.task_type != "template_generation":
        raise ValueError("Task is not a template generation task.")
    latest = service.repos.outputs.get_latest(task_id)
    if latest is None:
        raise ValueError("No template output found for task.")
    template_file = _safe_template_file(Path(latest.file_path))
    template_dir = template_file.parent
    metadata_file = _safe_template_file(template_dir / TEMPLATE_META_FILENAME)
    params_file = _safe_template_file(template_dir / TEMPLATE_PARAMS_FILENAME)
    render_script = _safe_template_file(template_dir / TEMPLATE_RENDER_SCRIPT_FILENAME)
    metadata: dict = {}
    if metadata_file.exists():
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except Exception:
            metadata = {}
    assets_dir = _safe_template_file(template_dir / "assets")
    assets = []
    if assets_dir.exists() and assets_dir.is_dir():
        for p in sorted(assets_dir.iterdir()):
            if p.is_file():
                assets.append(
                    {
                        "name": p.name,
                        "download_url": f"/v1/tasks/{task_id}/template-preview/file?kind=asset&name={p.name}",
                        "size_bytes": p.stat().st_size,
                    }
                )
    router = ModelRouter(service.repos)
    decision = router.pick(task.user_id, "review")
    provider_cfg = service.repos.providers.get_default_for_user(task.user_id)
    api_key = (provider_cfg.api_key_encrypted or "").strip() if provider_cfg and provider_cfg.api_key_encrypted else ""
    preview_payload = {
        "provider_type": decision.provider_type or "",
        "base_url": decision.base_url or "",
        "model_name": decision.model_name or "",
        "api_key": api_key,
        "template_type": metadata.get("template_type", ""),
        "template_name": metadata.get("template_name", template_dir.name),
        "metadata": metadata,
        "assets": assets,
    }
    try:
        preview_text = SkillExecutor.create_default().execute("template_preview_formatter", preview_payload)
    except Exception:
        fallback_items = [{"label": str(k), "value": str(v), "explanation": "LLM explanation unavailable for this field."} for k, v in metadata.items()]
        preview_text = {
            "preview_title": f"{metadata.get('template_name', template_dir.name)} ({metadata.get('template_type', 'unknown')})",
            "preview_summary": f"Metadata fields: {len(fallback_items)}; LLM explanations unavailable.",
            "items": fallback_items or [{"label": "metadata", "value": "empty", "explanation": "No metadata fields found."}],
        }
    return ApiResponse(
        success=True,
        data={
            "task_id": task_id,
            "template_dir": str(template_dir),
            "template_file": {
                "name": template_file.name,
                "download_url": f"/v1/tasks/{task_id}/template-preview/file?kind=template",
                "size_bytes": template_file.stat().st_size if template_file.exists() else 0,
            },
            "metadata_file": {
                "name": metadata_file.name,
                "download_url": f"/v1/tasks/{task_id}/template-preview/file?kind=meta",
                "size_bytes": metadata_file.stat().st_size if metadata_file.exists() else 0,
                "content": metadata,
            },
            "params_file": {
                "name": params_file.name,
                "download_url": f"/v1/tasks/{task_id}/template-preview/file?kind=params",
                "size_bytes": params_file.stat().st_size if params_file.exists() else 0,
            },
            "render_script": {
                "name": render_script.name,
                "download_url": f"/v1/tasks/{task_id}/template-preview/file?kind=script",
                "size_bytes": render_script.stat().st_size if render_script.exists() else 0,
            },
            "assets": assets,
            "preview_text": preview_text,
        },
    )


@router.get("/{task_id}/template-preview/file")
def download_template_preview_file(
    task_id: str,
    kind: str,
    name: Optional[str] = None,
    service: TaskService = Depends(_task_service),
    current_user: User = Depends(_current_user),
) -> FileResponse:
    task = _owned_task_or_raise(service, task_id, current_user.user_id)
    if task.task_type != "template_generation":
        raise ValueError("Task is not a template generation task.")
    latest = service.repos.outputs.get_latest(task_id)
    if latest is None:
        raise ValueError("No template output found for task.")
    template_file = _safe_template_file(Path(latest.file_path))
    template_dir = template_file.parent
    if kind == "template":
        path = template_file
    elif kind == "meta":
        path = _safe_template_file(template_dir / TEMPLATE_META_FILENAME)
    elif kind == "params":
        path = _safe_template_file(template_dir / TEMPLATE_PARAMS_FILENAME)
    elif kind == "script":
        path = _safe_template_file(template_dir / TEMPLATE_RENDER_SCRIPT_FILENAME)
    elif kind == "asset":
        if not name:
            raise ValueError("Asset name is required.")
        path = _safe_template_file(template_dir / "assets" / Path(name).name)
    else:
        raise ValueError("Unsupported file kind.")
    if not path.exists():
        raise ValueError(f"File not found: {path.name}")
    return FileResponse(path=str(path), filename=path.name, media_type=_media_type_for_path(path))
