from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import (
    database_is_available,
    ensure_indexes,
)
from app.routes.notifications import (
    router as notifications_router,
)
from app.services.email_service import (
    email_is_configured,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_indexes()
    except Exception:
        pass

    yield


app = FastAPI(
    title="SSAS Notification Service",
    description=(
        "Email and in-app notification service "
        "for the Smart Statistical Analysis System"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(
    notifications_router
)


@app.get("/")
def root():
    return {
        "service": settings.service_name,
        "status": "running",
    }


@app.get("/health")
def health():
    database_status = (
        "connected"
        if database_is_available()
        else "disconnected"
    )

    return {
        "service": settings.service_name,
        "status": (
            "healthy"
            if database_status == "connected"
            else "unhealthy"
        ),
        "database": database_status,
        "email": (
            "configured"
            if email_is_configured()
            else "not_configured"
        ),
    }
