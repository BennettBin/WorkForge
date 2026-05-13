from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.errors import register_exception_handlers
from app.api.routes import (
    auth_router,
    health_router,
    providers_router,
    skills_router,
    system_router,
    tasks_router,
    users_router,
    ws_tasks_router,
)
from app.config import settings
from app.services.active_users import ActiveUserTracker
from app.services.auth_service import AuthService
from app.services.repository_factory import build_repository_bundle
from app.services.task_manager import recover_interrupted_running_tasks

PROJECT_MAIN_DIR = Path(__file__).resolve().parents[3]
FRONTEND_DIST_DIR = PROJECT_MAIN_DIR / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.repositories = build_repository_bundle(settings.data_dir)
    recover_interrupted_running_tasks(app.state.repositories)
    app.state.active_user_tracker = ActiveUserTracker(window_seconds=600)
    AuthService(app.state.repositories).ensure_admin_account(email="admin", username="admin", password="123456")
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    register_exception_handlers(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router)
    application.include_router(tasks_router)
    application.include_router(auth_router)
    application.include_router(providers_router)
    application.include_router(skills_router)
    application.include_router(system_router)
    application.include_router(users_router)
    application.include_router(ws_tasks_router)

    @application.middleware("http")
    async def track_authenticated_activity(request, call_next):
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            if token:
                try:
                    user = AuthService(request.app.state.repositories).validate_token(token)
                    request.app.state.active_user_tracker.touch(user.user_id)
                except Exception:
                    # Do not block request flow for activity tracking failures.
                    pass
        return await call_next(request)

    if FRONTEND_DIST_DIR.exists():
        application.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="assets")

    def _frontend_entry() -> FileResponse:
        if not FRONTEND_INDEX_FILE.exists():
            raise HTTPException(status_code=404, detail="Frontend build not found. Run frontend build first.")
        return FileResponse(FRONTEND_INDEX_FILE)

    @application.get("/", tags=["frontend"])
    def root_frontend():
        return _frontend_entry()

    @application.get("/Login", tags=["frontend"])
    def login_frontend():
        return _frontend_entry()

    @application.get("/Register", tags=["frontend"])
    def register_frontend():
        return _frontend_entry()

    @application.get("/tasks/create", tags=["frontend"])
    def tasks_create_frontend():
        return _frontend_entry()

    @application.get("/tasks/running", tags=["frontend"])
    def tasks_running_frontend():
        return _frontend_entry()

    @application.get("/tasks/running/{task_id}", tags=["frontend"])
    def tasks_running_task_frontend(task_id: str):
        return _frontend_entry()

    @application.get("/result", tags=["frontend"])
    def result_frontend():
        return _frontend_entry()

    @application.get("/models", tags=["frontend"])
    def models_frontend():
        return _frontend_entry()

    @application.get("/history", tags=["frontend"])
    def history_frontend():
        return _frontend_entry()

    return application


app = create_app()
