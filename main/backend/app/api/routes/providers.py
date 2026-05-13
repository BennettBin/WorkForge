from typing import Optional

from fastapi import APIRouter, Depends, Header, Request

from app.models import ApiResponse, ProviderTestRequest, ProviderUpsertRequest
from app.models.entities import User
from app.services.auth_service import AuthService
from app.services.llm_provider import ProviderService

router = APIRouter(prefix="/v1/providers", tags=["providers"])


def _provider_service(request: Request) -> ProviderService:
    return ProviderService(request.app.state.repositories)


def _token_from_header(authorization: Optional[str]) -> str:
    if not authorization:
        raise ValueError("Missing Authorization header.")
    if not authorization.lower().startswith("bearer "):
        raise ValueError("Authorization must be Bearer token.")
    return authorization[7:].strip()


def _current_user(request: Request, authorization: Optional[str] = Header(default=None)) -> User:
    token = _token_from_header(authorization)
    return AuthService(request.app.state.repositories).validate_token(token)


@router.post("", response_model=ApiResponse)
def upsert_provider(
    payload: ProviderUpsertRequest,
    request: Request,
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    if payload.user_id != current_user.user_id:
        raise ValueError("User mismatch for provider upsert.")
    svc = _provider_service(request)
    cfg = svc.upsert(payload)
    return ApiResponse(success=True, data=cfg.model_dump(mode="json"))


@router.get("/default/me", response_model=ApiResponse)
def get_default_provider_me(request: Request, current_user: User = Depends(_current_user)) -> ApiResponse:
    svc = _provider_service(request)
    cfg = svc.get_default_for_user(current_user.user_id)
    if cfg is None:
        return ApiResponse(success=True, data={"item": None})
    return ApiResponse(success=True, data={"item": cfg.model_dump(mode="json")})


@router.get("/{user_id}", response_model=ApiResponse)
def list_providers(
    user_id: str,
    request: Request,
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    if user_id != current_user.user_id:
        raise ValueError("User mismatch for provider listing.")
    svc = _provider_service(request)
    items = [x.model_dump(mode="json") for x in svc.list_by_user(user_id)]
    return ApiResponse(success=True, data={"items": items})


@router.post("/test", response_model=ApiResponse)
def test_provider(
    payload: ProviderTestRequest,
    request: Request,
    current_user: User = Depends(_current_user),
) -> ApiResponse:
    svc = _provider_service(request)
    result = svc.test_connection(payload)
    return ApiResponse(success=True, data=result)
