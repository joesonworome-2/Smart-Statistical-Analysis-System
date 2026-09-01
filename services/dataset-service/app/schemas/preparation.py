from typing import Any, Literal

from pydantic import BaseModel, Field


MeasurementLevel = Literal[
    "metric",
    "ordinal",
    "nominal",
]

SemanticRole = Literal[
    "feature",
    "outcome",
    "group",
    "identifier",
    "datetime",
    "ignored",
]


class VariableMetadataUpdate(BaseModel):
    measurement_level: MeasurementLevel | None = None
    semantic_role: SemanticRole | None = None
    exclude_from_recommendations: bool | None = None


class MissingValuesRequest(BaseModel):
    columns: list[str]

    strategy: Literal[
        "drop_rows",
        "mean",
        "median",
        "mode",
        "constant",
    ]

    fill_value: Any | None = None


class OutlierRequest(BaseModel):
    column: str

    method: Literal[
        "iqr",
        "zscore",
    ] = "iqr"

    action: Literal[
        "remove",
        "clip",
    ] = "remove"

    threshold: float = Field(
        default=1.5,
        gt=0,
    )


class TransformRequest(BaseModel):
    column: str

    transformation: Literal[
        "standardize",
        "normalize",
        "log1p",
        "recode",
    ]

    new_column: str | None = None

    mapping: dict[str, Any] | None = None


class FilterRequest(BaseModel):
    column: str

    operator: Literal[
        "eq",
        "ne",
        "gt",
        "gte",
        "lt",
        "lte",
        "in",
        "contains",
        "between",
    ]

    value: Any

    value2: Any | None = None
