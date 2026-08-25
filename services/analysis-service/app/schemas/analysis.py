from typing import Any

from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    id: str
    dataset_id: str
    user_id: str
    analysis_type: str
    results: dict[str, Any]
    created_at: str


class AnalysisRequest(BaseModel):
    dataset_id: str = Field(
        ...,
        description="MongoDB ID of the dataset to analyze",
    )
