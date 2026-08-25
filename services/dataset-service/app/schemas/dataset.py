from datetime import datetime

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
    created_at: datetime
    updated_at: datetime


class DatasetListResponse(BaseModel):
    datasets: list[DatasetResponse]
    total: int
