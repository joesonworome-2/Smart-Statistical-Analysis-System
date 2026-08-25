from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.database import notifications_collection
from app.schemas.notification import (
    EmailNotificationRequest,
    ReportReadyRequest,
)
from app.security.dependencies import get_current_user
from app.services.notification_service import (
    create_notification,
    serialize_notification,
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("")
def list_notifications(
    unread_only: bool = False,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    current_user=Depends(get_current_user),
):
    query = {
        "user_id": current_user["id"]
    }

    if unread_only:
        query["is_read"] = False

    records = notifications_collection.find(
        query
    ).sort(
        "created_at",
        -1,
    ).limit(limit)

    notifications = [
        serialize_notification(record)
        for record in records
    ]

    return {
        "count": len(notifications),
        "notifications": notifications,
    }


@router.get("/unread-count")
def unread_count(
    current_user=Depends(get_current_user),
):
    count = notifications_collection.count_documents(
        {
            "user_id": current_user["id"],
            "is_read": False,
        }
    )

    return {
        "unread_count": count
    }


@router.post("/email")
def create_email_notification(
    request: EmailNotificationRequest,
    current_user=Depends(get_current_user),
):
    return create_notification(
        user=current_user,
        notification_type=(
            request.notification_type
        ),
        title=request.title,
        message=request.message,
        send_email_notification=(
            request.send_email
        ),
        metadata=request.metadata,
    )


@router.post("/test-email")
def test_email(
    current_user=Depends(get_current_user),
):
    return create_notification(
        user=current_user,
        notification_type="test",
        title="SSAS Email Test",
        message=(
            "This is a test notification from the "
            "Smart Statistical Analysis System."
        ),
        send_email_notification=True,
        metadata={
            "source": "notification-service"
        },
    )


@router.post("/report-ready")
def report_ready(
    request: ReportReadyRequest,
    current_user=Depends(get_current_user),
):
    file_text = (
        f" ({request.file_name})"
        if request.file_name
        else ""
    )

    return create_notification(
        user=current_user,
        notification_type="report_ready",
        title="Your SSAS report is ready",
        message=(
            "Your statistical analysis report"
            f"{file_text} has been generated "
            "successfully and is ready for download."
        ),
        send_email_notification=True,
        metadata={
            "report_id": request.report_id,
            "dataset_id": request.dataset_id,
            "file_name": request.file_name,
        },
    )


@router.patch("/{notification_id}/read")
def mark_as_read(
    notification_id: str,
    current_user=Depends(get_current_user),
):
    try:
        object_id = ObjectId(
            notification_id
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid notification ID.",
        )

    result = notifications_collection.find_one_and_update(
        {
            "_id": object_id,
            "user_id": current_user["id"],
        },
        {
            "$set": {
                "is_read": True
            }
        },
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Notification not found.",
        )

    return serialize_notification(result)
