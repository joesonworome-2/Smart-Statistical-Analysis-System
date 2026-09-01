from fastapi import FastAPI

from app.config import settings
from app.database import database_is_available
from app.routes.ml import router as ml_router
from app.routes.predictive import (
    router as predictive_router,
)

app = FastAPI(
    title="SSAS Machine Learning Service",
    description=(
        "Machine learning service for the "
        "Smart Statistical Analysis System"
    ),
    version="1.0.0",
)

app.include_router(ml_router)
app.include_router(
    predictive_router
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
    }
