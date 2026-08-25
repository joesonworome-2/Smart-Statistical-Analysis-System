from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.services.proxy import proxy_request


router = APIRouter()

METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

SERVICE_ROUTES = {
    "auth": settings.auth_service_url,
    "users": settings.user_service_url,
    "datasets": settings.dataset_service_url,
    "analysis": settings.analysis_service_url,
    "statistics": settings.statistics_service_url,
    "ml": settings.ml_service_url,
    "visualizations": settings.visualization_service_url,
    "reports": settings.report_service_url,
    "notifications": settings.notification_service_url,
}


async def forward(
    service_prefix: str,
    path: str,
    request: Request,
):
    base_url = SERVICE_ROUTES.get(service_prefix)

    if not base_url:
        raise HTTPException(
            status_code=404,
            detail="Unknown service route.",
        )

    target_url = f"{base_url}/{service_prefix}"

    if path:
        target_url += f"/{path}"

    return await proxy_request(
        request=request,
        target_url=target_url,
    )


# Handles:
# /datasets
# /reports
# /notifications
# /users
# etc.
@router.api_route(
    "/{service_prefix}",
    methods=METHODS,
)
async def service_root(
    service_prefix: str,
    request: Request,
):
    return await forward(
        service_prefix,
        "",
        request,
    )


# Handles:
# /datasets/{id}
# /auth/me
# /ml/types
# /reports/{id}
# etc.
@router.api_route(
    "/{service_prefix}/{path:path}",
    methods=METHODS,
)
async def service_path(
    service_prefix: str,
    path: str,
    request: Request,
):
    return await forward(
        service_prefix,
        path,
        request,
    )
