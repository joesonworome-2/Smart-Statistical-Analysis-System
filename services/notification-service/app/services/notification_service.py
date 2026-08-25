from datetime import datetime, timezone

from app.database import notifications_collection
from app.services.email_service import (
    email_is_configured,
    send_email,
)


def serialize_notification(document):
    return {
        "notification_id": str(document["_id"]),
        "user_id": document.get("user_id"),
        "email": document.get("email"),
        "type": document.get("type"),
        "title": document.get("title"),
        "message": document.get("message"),
        "channel": document.get("channel"),
        "email_status": document.get(
            "email_status"
        ),
        "email_error": document.get(
            "email_error"
        ),
        "is_read": document.get(
            "is_read",
            False,
        ),
        "metadata": document.get(
            "metadata",
            {},
        ),
        "created_at": (
            document["created_at"].isoformat()
            if document.get("created_at")
            else None
        ),
        "sent_at": (
            document["sent_at"].isoformat()
            if document.get("sent_at")
            else None
        ),
    }


def create_notification(
    user,
    notification_type,
    title,
    message,
    send_email_notification=True,
    metadata=None,
):
    now = datetime.now(timezone.utc)

    email_status = "not_requested"
    email_error = None
    sent_at = None

    user_email = user.get("email")

    if send_email_notification:

        if not user_email:
            email_status = "no_email_address"

        elif not email_is_configured():
            email_status = "not_configured"

        else:
            try:
                send_email(
                    to_email=user_email,
                    subject=title,
                    body=message,
                )

                email_status = "sent"
                sent_at = datetime.now(
                    timezone.utc
                )

            except Exception as exc:
                email_status = "failed"
                email_error = str(exc)

    document = {
        "user_id": user["id"],
        "email": user_email,
        "type": notification_type,
        "title": title,
        "message": message,
        "channel": (
            "email_and_in_app"
            if send_email_notification
            else "in_app"
        ),
        "email_status": email_status,
        "email_error": email_error,
        "is_read": False,
        "metadata": metadata or {},
        "created_at": now,
        "sent_at": sent_at,
    }

    result = notifications_collection.insert_one(
        document
    )

    document["_id"] = result.inserted_id

    return serialize_notification(document)
