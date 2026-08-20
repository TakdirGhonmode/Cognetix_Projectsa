from .services import router as services_router
from .health import router as health_router
from .alerts import router as alerts_router
from .rules import router as rules_router
from .metrics import router as metrics_router
from .reports import router as reports_router
from .logs import router as logs_router

__all__ = [
    "services_router",
    "health_router",
    "alerts_router",
    "rules_router",
    "metrics_router",
    "reports_router",
    "logs_router"
]
