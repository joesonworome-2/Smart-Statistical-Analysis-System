from __future__ import annotations

import json
from datetime import (
    datetime,
    timezone,
)

from bson import ObjectId
from fastapi import (
    FastAPI,
    Request,
    Response,
)

from app.config import settings
from app.database import database_is_available

from app.routes.statistics import (
    router as statistics_router,
)
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
from app.routes.regression_analysis import (
    router as regression_analysis_router,
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

from app.services.auth_identity import (
    get_authenticated_user,
)
from app.services.statistical_result_store import (
    get_results_collection,
)


app = FastAPI(
    title="SSAS Statistics Service",
    description=(
        "Statistical computation service for the "
        "Smart Statistical Analysis System"
    ),
    version="1.0.0",
)


# ============================================================
# Automatic result capture
# ============================================================
#
# Purpose:
# Every successful statistical test carried out by SSAS should
# be available later to the report service.  This middleware
# stores the returned result in the existing statistical_results
# collection.
#
# Descriptive statistics are excluded here because the frontend
# saves the exact table the user selected (Mean, Median, Std.
# Deviation, etc.), not the entire backend payload.
# ============================================================

TITLE_MAP = {
    "hypothesis": "Hypothesis Test",
    "correlation": "Correlation Analysis",
    "regression": "Regression Analysis",
    "multiple-regression": "Multiple Regression Analysis",
    "predictive": "Predictive Analytics",
    "ancova": "ANCOVA",
    "survival": "Survival Analysis",
    "efa-pca": "EFA / PCA",
    "factor": "EFA / PCA",
    "reliability": "Reliability Analysis",
    "cluster": "Cluster Analysis",
    "one-sample-t": "One-Sample t-Test",
    "independent-t": "Independent Samples t-Test",
    "paired-t": "Paired Samples t-Test",
    "chi-square": "Chi-Square Test",
    "shapiro": "Shapiro-Wilk Normality Test",
    "mann-whitney": "Mann-Whitney U Test",
    "wilcoxon": "Wilcoxon Signed-Rank Test",
    "kruskal-wallis": "Kruskal-Wallis Test",
    "anova": "One-Way ANOVA",
    "confidence-interval": "Confidence Interval",
}


def _humanize(
    value: str,
) -> str:
    return (
        value
        .replace("_", " ")
        .replace("-", " ")
        .strip()
        .title()
    )


def _dataset_id_from_path(
    path: str,
) -> tuple[str | None, str | None]:
    parts = [
        part
        for part in path.split("/")
        if part
    ]

    for index in range(
        len(parts) - 1,
        -1,
        -1,
    ):
        part = parts[index]

        if ObjectId.is_valid(part):
            method_slug = (
                parts[index - 1]
                if index > 0
                else "analysis"
            )

            return (
                part,
                method_slug,
            )

    return (
        None,
        None,
    )


def _response_title(
    method_slug: str,
    payload,
) -> str:
    if isinstance(
        payload,
        dict,
    ):
        for key in (
            "test",
            "test_name",
            "title",
            "analysis_name",
        ):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return TITLE_MAP.get(
        method_slug,
        _humanize(method_slug),
    )


def _response_interpretation(
    payload,
):
    if not isinstance(
        payload,
        dict,
    ):
        return None

    value = payload.get(
        "interpretation"
    )

    if isinstance(value, str):
        return value

    summary = payload.get(
        "summary"
    )

    if isinstance(summary, str):
        return summary

    return None


@app.middleware("http")
async def capture_statistical_result(
    request: Request,
    call_next,
):
    response = await call_next(
        request
    )

    path = request.url.path

    should_skip = (
        not path.startswith(
            "/statistics/"
        )
        or path.startswith(
            "/statistics/results"
        )
        or path.startswith(
            "/statistics/smart/"
        )
        or path.startswith(
            "/statistics/descriptive/"
        )
        or path == "/statistics/tests"
        or response.status_code < 200
        or response.status_code >= 300
    )

    if should_skip:
        return response

    dataset_id, method_slug = (
        _dataset_id_from_path(
            path
        )
    )

    if (
        not dataset_id
        or not method_slug
    ):
        return response

    # call_next() returns a streaming response.  Read the body,
    # store a JSON copy when possible, and then rebuild the same
    # response for the frontend.
    body = b""

    async for chunk in response.body_iterator:
        body += chunk

    headers = dict(
        response.headers
    )
    headers.pop(
        "content-length",
        None,
    )

    rebuilt_response = Response(
        content=body,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type,
        background=response.background,
    )

    try:
        payload = json.loads(
            body.decode("utf-8")
        )
    except Exception:
        return rebuilt_response

    authorization = request.headers.get(
        "authorization"
    )

    if not authorization:
        return rebuilt_response

    try:
        user = await get_authenticated_user(
            authorization
        )

        user_id = user[
            "user_id"
        ]

        now = datetime.now(
            timezone.utc
        )

        document = {
            "user_id": user_id,
            "dataset_id": dataset_id,
            "dataset_name": (
                payload.get("dataset")
                if isinstance(payload, dict)
                else None
            ),
            "method": method_slug.replace(
                "-",
                "_",
            ),
            "title": _response_title(
                method_slug,
                payload,
            ),
            "configuration": {
                "endpoint": path,
                "query": dict(
                    request.query_params
                ),
            },
            "tables": [],
            "assumptions": (
                payload.get(
                    "assumptions"
                )
                if isinstance(
                    payload,
                    dict,
                )
                else None
            ),
            "interpretation": (
                _response_interpretation(
                    payload
                )
            ),
            "apa": (
                payload.get("apa")
                if isinstance(
                    payload,
                    dict,
                )
                else None
            ),
            "metadata": {
                "raw_result": payload,
                "captured_automatically": True,
                "http_method": request.method,
            },
            "created_at": now,
            "updated_at": now,
        }

        get_results_collection().insert_one(
            document
        )

    except Exception:
        # Statistical calculation must never fail merely because
        # report-history persistence failed.
        pass

    return rebuilt_response


# ============================================================
# Routers
# ============================================================

app.include_router(
    statistical_results_router
)
app.include_router(
    statistics_router
)
app.include_router(
    smart_statistics_router
)
app.include_router(
    hypothesis_router
)
app.include_router(
    correlation_analysis_router
)
app.include_router(
    regression_analysis_router
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


# ============================================================
# Service endpoints
# ============================================================

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
