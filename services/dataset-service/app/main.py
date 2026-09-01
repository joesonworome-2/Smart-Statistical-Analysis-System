from fastapi import FastAPI

from app.config import settings
from app.database import (
    check_database_connection,
)
from app.routes.datasets import (
    router as dataset_router,
)
from app.routes.preparation import (
    router as preparation_router,
)


app = FastAPI(
    title=settings.project_name,
    version="1.1.0",
)


# Existing dataset APIs
app.include_router(
    dataset_router
)

# Smart Data Preparation APIs
app.include_router(
    preparation_router
)


@app.get("/")
def root():
    return {
        "service":
            "SSAS Dataset Service",

        "status":
            "running",

        "data_preparation":
            True,
    }


@app.get("/health")
def health():
    database_status = (
        check_database_connection()
    )

    return {
        "service":
            "dataset-service",

        "status":
            (
                "healthy"
                if database_status
                else "unhealthy"
            ),

        "database":
            (
                "connected"
                if database_status
                else "disconnected"
            ),
    }
