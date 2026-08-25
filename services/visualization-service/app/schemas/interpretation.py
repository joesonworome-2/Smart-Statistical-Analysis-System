from typing import Any

from pydantic import BaseModel

from app.schemas.visualization import (
    ChartRecommendation,
)


class VisualizationInterpretation(
    BaseModel
):
    chart_type: str
    title: str
    summary: str
    key_findings: list[str]
    metrics: dict[str, Any]
    cautions: list[str]


class VisualizationInterpretationResponse(
    BaseModel
):
    dataset_id: str
    goal: str
    rank: int
    recommendation: ChartRecommendation
    interpretation: (
        VisualizationInterpretation
    )
