from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import models
from database import engine
from routes import auth_routes, product_routes
import transaction_history

# Create Database Tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI Application
app = FastAPI(
    title="Product Management REST API",
    version="1.0.0",
    description="Level 4 Project - Python REST API for inventory management with JWT Auth and Role-Based Access Control.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Global Exception Handlers
# -----------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Format HTTP exceptions into standard API response structure."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": str(exc.detail),
            "details": None
        },
        headers=exc.headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format request payload validation errors into standard API response structure."""
    error_messages = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", [])])
        msg = err.get("msg", "Invalid value")
        error_messages.append(f"{field}: {msg}")

    summary_message = "Validation failed for request: " + "; ".join(error_messages)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": summary_message,
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled internal server errors (500)."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An internal server error occurred.",
            "details": str(exc)
        }
    )


# -----------------------------
# Include Routers
# -----------------------------
app.include_router(auth_routes.router)
app.include_router(product_routes.router)
app.include_router(transaction_history.router)


# -----------------------------
# Home API Endpoint
# -----------------------------
@app.get("/", tags=["General"])
def home():
    """Root endpoint for API health check and documentation links."""
    return {
        "status": "success",
        "message": "Welcome to Product Management REST API",
        "data": {
            "version": "1.0.0",
            "documentation": "/docs",
            "redoc": "/redoc"
        }
    }