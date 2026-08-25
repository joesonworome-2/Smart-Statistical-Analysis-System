from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


ReportFormat = Literal[
    "pdf",
    "xlsx",
]


class ReportGenerateResponse(
    BaseModel
):
    report_id: str
    dataset_id: str
    title: str
    format: ReportFormat
    file_name: str
    created_at: datetime
    download_endpoint: str


class ReportListItem(
    BaseModel
):
    report_id: str
    dataset_id: str
    title: str
    format: str
    file_name: str
    created_at: datetime


class ReportListResponse(
    BaseModel
):
    count: int
    reports: list[
        ReportListItem
    ]


class ReportDetailResponse(
    BaseModel
):
    report_id: str
    dataset_id: str
    user_id: str
    title: str
    format: str
    file_name: str
    created_at: datetime
    metadata: dict[
        str,
        Any,
    ]
