from typing import Any

from pydantic import BaseModel, Field


class EmailNotificationRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=160,
    )

    message: str = Field(
        min_length=1,
        max_length=5000,
    )

    notification_type: str = "general"

    send_email: bool = True

    metadata: dict[str, Any] | None = None


class ReportReadyRequest(BaseModel):
    report_id: str
    dataset_id: str | None = None
    file_name: str | None = None
