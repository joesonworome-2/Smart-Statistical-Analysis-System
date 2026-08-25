from fastapi import FastAPI

from app.config import settings
from app.database import (
    check_database_connection,
    initialize_database,
)
from app.routes.auth import router as auth_router


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description=(
        "Authentication microservice for the "
        "Smart Statistical Analysis System."
    ),
)


app.include_router(auth_router)


@app.on_event("startup")
def startup_event():
    initialize_database()


@app.get("/")
def root():
    return {
        "service": "SSAS Authentication Service",
        "status": "running",
    }


@app.get("/health")
def health_check():
    database_status = check_database_connection()

    return {
        "service": "auth-service",
        "status": "healthy" if database_status else "unhealthy",
        "database": (
            "connected"
            if database_status
            else "disconnected"
        ),
    }
