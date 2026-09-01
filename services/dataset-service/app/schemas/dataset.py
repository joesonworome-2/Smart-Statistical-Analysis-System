from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DatasetResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    row_count: int
    column_count: int
    columns: list[str]
    status: str

    is_derived: bool = False
    source_dataset_id: str | None = None

    preparation_steps: list[dict[str, Any]] = []

    created_at: datetime
    updated_at: datetime


class DatasetListResponse(BaseModel):
    datasets: list[DatasetResponse]
    total: int
