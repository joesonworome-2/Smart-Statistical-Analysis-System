from fastapi import FastAPI

from app.config import settings
from app.database import (
    check_database_connection,
)

from app.routes.users import (
    router as users_router,
)

from app.routes.admin import (
    router as admin_router,
)


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
)


app.include_router(users_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {
        "service": "SSAS User Service",
        "status": "running",
    }


@app.get("/health")
def health():
    database_status = (
        check_database_connection()
    )

    return {
        "service": "user-service",
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
