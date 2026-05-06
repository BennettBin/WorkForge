from .auth import router as auth_router
from .health import router as health_router
from .providers import router as providers_router
from .skills import router as skills_router
from .tasks import router as tasks_router
from .ws_tasks import router as ws_tasks_router

__all__ = [
    "health_router",
    "tasks_router",
    "auth_router",
    "providers_router",
    "skills_router",
    "ws_tasks_router",
]
