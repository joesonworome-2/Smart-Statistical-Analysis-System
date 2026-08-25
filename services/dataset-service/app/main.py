from fastapi import FastAPI

from app.config import settings
from app.database import check_database_connection
from app.routes.datasets import router as dataset_router


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
)


app.include_router(dataset_router)


@app.get("/")
def root():
    return {
        "service": "SSAS Dataset Service",
        "status": "running",
    }


@app.get("/health")
def health():
    database_status = check_database_connection()

    return {
        "service": "dataset-service",
        "status": "healthy" if database_status else "unhealthy",
        "database": "connected" if database_status else "disconnected",
    }
