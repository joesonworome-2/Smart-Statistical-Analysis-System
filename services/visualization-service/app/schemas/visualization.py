from typing import Any

from pydantic import BaseModel, Field


class VisualizationRequest(BaseModel):

    chart_type: str = Field(
        ...,
        description=(
            "Visualization type to generate."
        ),
    )

    x: str | None = None
    y: str | None = None

    z: str | None = None

    columns: list[str] | None = None

    group_by: str | None = None

    category: str | None = None

    value: str | None = None

    size: str | None = None

    color: str | None = None

    date_column: str | None = None

    aggregation: str | None = None

    bins: int | None = 20

    title: str | None = None

    x_label: str | None = None

    y_label: str | None = None

    orientation: str = "vertical"

    normalize: bool = False

    cumulative: bool = False

    trendline: bool = False

    options: dict[str, Any] = Field(
        default_factory=dict
    )


class VisualizationResponse(BaseModel):

    dataset_id: str

    visualization_type: str

    chart: dict[str, Any]

    metadata: dict[str, Any]


class ChartRecommendation(BaseModel):
    chart_type: str
    score: float
    confidence_percent: int
    category: str
    reason: str
    suggested_config: dict[
        str,
        Any,
    ]


class VisualizationRecommendationResponse(
    BaseModel
):
    dataset_id: str
    goal: str
    dataset_profile: dict[
        str,
        Any,
    ]
    recommendation_count: int
    recommendations: list[
        ChartRecommendation
    ]
class AutoVisualizationResponse(BaseModel):
    dataset_id: str
    visualization_type: str
    recommendation: ChartRecommendation
    chart: dict[str, Any]
    metadata: dict[str, Any]
