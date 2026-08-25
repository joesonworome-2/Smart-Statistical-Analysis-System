from fastapi import FastAPI

from app.database import (
    database_is_available,
)
from app.routes.reports import (
    router as reports_router,
)


app = FastAPI(
    title=(
        "SSAS Report Service"
    ),
    description=(
        "PDF and Excel report "
        "generation service for SSAS."
    ),
    version="1.0.0",
)


app.include_router(
    reports_router
)


@app.get("/")
def root():

    return {
        "service": (
            "report-service"
        ),
        "message": (
            "SSAS Report Service "
            "is running."
        ),
    }


@app.get("/health")
def health():

    database_status = (
        database_is_available()
    )

    return {
        "service": (
            "report-service"
        ),
        "status": (
            "healthy"
            if database_status
            else "degraded"
        ),
        "database": (
            "connected"
            if database_status
            else "disconnected"
        ),
    }
