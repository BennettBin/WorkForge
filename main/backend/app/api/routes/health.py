from fastapi import APIRouter

from app.config import settings
from app.models.api import ApiResponse

router = APIRouter(prefix="/WorkForge", tags=["workforge"])


@router.get("", response_model=ApiResponse)
def health_check() -> ApiResponse:
    return ApiResponse(
        success=True,
        data={
            "status": "WorkForge",
            "app": settings.app_name,
            "env": settings.app_env,
            "version": settings.app_version,
        },
    )
