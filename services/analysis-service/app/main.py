from fastapi import FastAPI

from app.config import settings
from app.database import check_database_connection
from app.routes.analysis import router as analysis_router


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description=(
        "SSAS Statistical Analysis Service"
    ),
)


@app.get("/")
def root():
    return {
        "service": "SSAS Analysis Service",
        "status": "running",
    }


@app.get("/health")
def health():
    database_status = check_database_connection()

    return {
        "service": "analysis-service",
        "status": (
            "healthy"
            if database_status
            else "unhealthy"
        ),
        "database": (
            "connected"
            if database_status
            else "disconnected"
        ),
    }


app.include_router(analysis_router)
