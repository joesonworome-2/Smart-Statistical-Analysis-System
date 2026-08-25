from fastapi import FastAPI

from app.database import database
from app.routes.visualizations import (
    router as visualization_router,
)
from app.routes.interpretations import (
    router as interpretations_router,
)


app = FastAPI(
    title="SSAS Visualization Service",
    version="1.0.0",
    description=(
        "Visualization and graphical "
        "analysis service for SSAS."
    ),
)


app.include_router(
    visualization_router
)

app.include_router(
    interpretations_router
)

@app.get("/")
def root():

    return {
        "service": (
            "visualization-service"
        ),
        "message": (
            "SSAS Visualization Service"
        ),
    }


@app.get("/health")
def health():

    try:
        database.command(
            "ping"
        )

        database_status = (
            "connected"
        )

    except Exception:
        database_status = (
            "disconnected"
        )

    return {
        "service": (
            "visualization-service"
        ),
        "status": "healthy",
        "database": database_status,
    }
