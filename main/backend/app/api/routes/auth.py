from fastapi import APIRouter, Header, Request
from typing import Optional

from app.models import ApiResponse, LoginRequest, RegisterRequest, UpdatePasswordRequest, UpdateProfileRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _auth_service(request: Request) -> AuthService:
    return AuthService(request.app.state.repositories)


def _token_from_header(authorization: Optional[str]) -> str:
    if not authorization:
        raise ValueError("Missing Authorization header.")
    if not authorization.lower().startswith("bearer "):
        raise ValueError("Authorization must be Bearer token.")
    return authorization[7:].strip()


@router.post("/register", response_model=ApiResponse)
def register(payload: RegisterRequest, request: Request) -> ApiResponse:
    svc = _auth_service(request)
    user = svc.register(payload)
    return ApiResponse(success=True, data={"user_id": user.user_id, "email": user.email, "username": user.username})


@router.post("/login", response_model=ApiResponse)
def login(payload: LoginRequest, request: Request) -> ApiResponse:
    svc = _auth_service(request)
    result = svc.login(payload)
    return ApiResponse(success=True, data=result)


@router.get("/me", response_model=ApiResponse)
def me(request: Request, authorization: Optional[str] = Header(default=None)) -> ApiResponse:
    svc = _auth_service(request)
    user = svc.validate_token(_token_from_header(authorization))
    return ApiResponse(success=True, data={"user_id": user.user_id, "email": user.email, "username": user.username})


@router.put("/profile", response_model=ApiResponse)
def update_profile(
    payload: UpdateProfileRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> ApiResponse:
    svc = _auth_service(request)
    user = svc.update_profile(_token_from_header(authorization), payload)
    return ApiResponse(success=True, data={"user_id": user.user_id, "email": user.email, "username": user.username})


@router.put("/password", response_model=ApiResponse)
def update_password(
    payload: UpdatePasswordRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> ApiResponse:
    svc = _auth_service(request)
    svc.update_password(_token_from_header(authorization), payload)
    return ApiResponse(success=True, data={"updated": True})
