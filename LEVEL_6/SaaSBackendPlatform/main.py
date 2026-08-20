from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from config import settings
import models  # Ensure all SQLAlchemy models are registered

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Scalable Multi-Tenant Python SaaS Backend Platform with JWT Auth, RBAC, Subscriptions, Alerts, Usage Tracking & Billing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers for structured JSON error response format
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail if isinstance(exc.detail, str) else "Request processing failed",
            "errors": exc.detail if isinstance(exc.detail, list) else [str(exc.detail)]
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
    detail = getattr(exc, "detail", str(exc))
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": detail if isinstance(detail, str) else "An unhandled server error occurred",
            "errors": detail if isinstance(detail, list) else [str(detail)]
        }
    )

# Import and mount routers
from routes import (
    auth_router,
    user_router,
    org_router,
    sub_router,
    alert_router,
    usage_router,
    billing_router,
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(org_router)
app.include_router(sub_router)
app.include_router(alert_router)
app.include_router(usage_router)
app.include_router(billing_router)

# Direct Root Path Shortcuts to satisfy exact Endpoint Specs (/register, /login, /users, /subscriptions, /alerts, /usage)
@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "success": True,
        "message": f"Welcome to {settings.APP_NAME} API v1.0.0",
        "data": {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
