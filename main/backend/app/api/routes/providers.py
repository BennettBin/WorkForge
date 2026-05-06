from fastapi import APIRouter, Request

from app.models import ApiResponse, ProviderTestRequest, ProviderUpsertRequest
from app.services.llm_provider import ProviderService

router = APIRouter(prefix="/v1/providers", tags=["providers"])


def _provider_service(request: Request) -> ProviderService:
    return ProviderService(request.app.state.repositories)


@router.post("", response_model=ApiResponse)
def upsert_provider(payload: ProviderUpsertRequest, request: Request) -> ApiResponse:
    svc = _provider_service(request)
    cfg = svc.upsert(payload)
    return ApiResponse(success=True, data=cfg.model_dump(mode="json"))


@router.get("/{user_id}", response_model=ApiResponse)
def list_providers(user_id: str, request: Request) -> ApiResponse:
    svc = _provider_service(request)
    items = [x.model_dump(mode="json") for x in svc.list_by_user(user_id)]
    return ApiResponse(success=True, data={"items": items})


@router.post("/test", response_model=ApiResponse)
def test_provider(payload: ProviderTestRequest, request: Request) -> ApiResponse:
    svc = _provider_service(request)
    result = svc.test_connection(payload)
    return ApiResponse(success=True, data=result)
