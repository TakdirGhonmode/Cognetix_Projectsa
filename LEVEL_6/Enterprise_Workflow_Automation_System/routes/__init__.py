from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.templates import router as templates_router
from routes.instances import router as instances_router
from routes.tasks import router as tasks_router
from routes.analytics import router as analytics_router
from routes.audit import router as audit_router

__all__ = [
    "auth_router",
    "users_router",
    "templates_router",
    "instances_router",
    "tasks_router",
    "analytics_router",
    "audit_router"
]
