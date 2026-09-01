from fastapi import FastAPI

from app.routes.regression_analysis import (
    router as regression_analysis_router,
)
from app.config import settings
from app.database import database_is_available
from app.routes.statistics import router as statistics_router

from app.routes.hypothesis import (
    router as hypothesis_router,
)

from app.routes.smart_statistics import (
    router as smart_statistics_router,
)

from app.routes.correlation_analysis import (
    router as correlation_analysis_router,
)

from app.routes.statistical_results import (
    router as statistical_results_router,
)

from app.routes.predictive_analysis import (
    router as predictive_analysis_router,
)


from app.routes.ancova_analysis import (
    router as ancova_analysis_router,
)

from app.routes.survival_analysis import (
    router as survival_analysis_router,
)
from app.routes.efa_pca_analysis import (
    router as efa_pca_analysis_router,
)
from app.routes.reliability_analysis import (
    router as reliability_analysis_router,
)
from app.routes.cluster_analysis import (
    router as cluster_analysis_router,
)


app = FastAPI(
    title="SSAS Statistics Service",
    description=(
        "Statistical computation service for the "
        "Smart Statistical Analysis System"
    ),
    version="1.0.0",
)

app.include_router(
    correlation_analysis_router
)

app.include_router(
    statistical_results_router
)

app.include_router(statistics_router)

app.include_router(
    hypothesis_router
)
app.include_router(
    regression_analysis_router
)
app.include_router(
    ancova_analysis_router
)
app.include_router(
    predictive_analysis_router
)
app.include_router(
    ancova_analysis_router
)

app.include_router(
    survival_analysis_router
)
app.include_router(
    efa_pca_analysis_router
)
app.include_router(
    reliability_analysis_router
)
app.include_router(
    cluster_analysis_router
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
app.include_router(
    statistics_router
)
app.include_router(
    smart_statistics_router
)
