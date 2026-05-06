from pathlib import Path

from fastapi import APIRouter, Request

from app.models import ApiResponse
from app.services.skill_registry import SkillRegistry

router = APIRouter(prefix="/v1/skills", tags=["skills"])


def _registry() -> SkillRegistry:
    return SkillRegistry(Path("main/backend/app/skills"))


@router.get("", response_model=ApiResponse)
def list_skills() -> ApiResponse:
    reg = _registry()
    items = [s.__dict__ for s in reg.list_all()]
    return ApiResponse(success=True, data={"items": items})


@router.get("/resolve/{task_type}/{stage}", response_model=ApiResponse)
def resolve_skills(task_type: str, stage: str, request: Request) -> ApiResponse:
    reg = _registry()
    items = [s.__dict__ for s in reg.resolve_for(task_type, stage)]
    return ApiResponse(success=True, data={"items": items})
