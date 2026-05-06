import uuid
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.api import ApiError, ApiResponse


def _build_error(code: str, message: str, detail=None) -> ApiResponse:
    return ApiResponse(
        success=False,
        data=None,
        error=ApiError(code=code, message=message, trace_id=uuid.uuid4().hex, detail=detail),
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError):
        payload = _build_error("BAD_REQUEST", str(exc))
        return JSONResponse(status_code=400, content=payload.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        payload = _build_error("VALIDATION_ERROR", "Request validation failed.", detail=exc.errors())
        return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException):
        payload = _build_error("HTTP_ERROR", str(exc.detail), detail={"status_code": exc.status_code})
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unknown_exception_handler(_: Request, exc: Exception):
        payload = _build_error("INTERNAL_ERROR", "Unexpected server error.", detail={"message": str(exc)})
        return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))
