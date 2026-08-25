from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.gateway import router as gateway_router
from app.routes.health import router as health_router


app = FastAPI(
    title="SSAS API Gateway",
    description=(
        "Single API entry point for the "
        "Smart Statistical Analysis System"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health_router
)

app.include_router(
    gateway_router
)


@app.get("/")
def root():
    return {
        "service": "api-gateway",
        "status": "running",
        "port": 8000,
        "system": (
            "Smart Statistical Analysis System"
        ),
    }
