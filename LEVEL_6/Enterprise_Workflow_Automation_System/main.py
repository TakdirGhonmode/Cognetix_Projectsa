import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from database import engine, Base
from seed_data import seed_database
from routes import (
    auth_router,
    users_router,
    templates_router,
    instances_router,
    tasks_router,
    analytics_router,
    audit_router
)

logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Running database seeder...")
    seed_database()
    yield

app = FastAPI(
    title="Enterprise Workflow Automation System",
    description="Python 3.10+ Enterprise Workflow Engine with RBAC, Dynamic Stages, State Machine Transitions, Tamper-Resistant Audit Logs, Bottleneck Analytics, and Web UI.",
    version="2.0.0",
    lifespan=lifespan
)

# Static files for UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(templates_router)
app.include_router(instances_router)
app.include_router(tasks_router)
app.include_router(analytics_router)
app.include_router(audit_router)

@app.get("/", include_in_schema=False)
async def serve_root_ui():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"message": "Enterprise Workflow Automation System API is online. Visit /docs for OpenAPI documentation."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
