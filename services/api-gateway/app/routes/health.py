import asyncio

import httpx

from fastapi import APIRouter

from app.config import settings


router = APIRouter()


SERVICES = {
    "auth": settings.auth_service_url,
    "user": settings.user_service_url,
    "dataset": settings.dataset_service_url,
    "analysis": settings.analysis_service_url,
    "statistics": settings.statistics_service_url,
    "ml": settings.ml_service_url,
    "visualization": (
        settings.visualization_service_url
    ),
    "report": settings.report_service_url,
    "notification": (
        settings.notification_service_url
    ),
}


async def check_service(
    name: str,
    url: str,
):
    try:
        async with httpx.AsyncClient(
            timeout=5.0
        ) as client:

            response = await client.get(
                f"{url}/health"
            )

        return {
            "service": name,
            "status": (
                "healthy"
                if response.status_code == 200
                else "unhealthy"
            ),
            "http_status": response.status_code,
        }

    except Exception:
        return {
            "service": name,
            "status": "unavailable",
            "http_status": None,
        }


@router.get("/health")
async def gateway_health():
    results = await asyncio.gather(
        *[
            check_service(name, url)
            for name, url
            in SERVICES.items()
        ]
    )

    services = {
        item["service"]: {
            "status": item["status"],
            "http_status": (
                item["http_status"]
            ),
        }
        for item in results
    }

    all_healthy = all(
        item["status"] == "healthy"
        for item in results
    )

    return {
        "service": "api-gateway",
        "status": (
            "healthy"
            if all_healthy
            else "degraded"
        ),
        "services": services,
    }
