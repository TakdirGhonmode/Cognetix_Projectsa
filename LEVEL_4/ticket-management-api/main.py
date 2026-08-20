from fastapi import FastAPI
from database import engine, Base
import models

from routes import router as ticket_router
from auth import router as auth_router

app = FastAPI(
    title="Customer Support Ticket Management API",
    description="REST API for customer support ticket management",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

app.include_router(ticket_router)
app.include_router(auth_router)


@app.get("/")
def home():
    return {
        "status": "success",
        "message": "Customer Support Ticket Management API is running"
    }