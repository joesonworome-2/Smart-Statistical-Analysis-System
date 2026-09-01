from typing import Literal

from pydantic import BaseModel, Field


MeasurementLevel = Literal[
    "metric",
    "ordinal",
    "nominal",
]


class NormalityRequest(BaseModel):
    column: str

    methods: list[
        Literal[
            "shapiro",
            "anderson",
            "ks",
        ]
    ] = [
        "shapiro",
        "anderson",
        "ks",
    ]

    alpha: float = Field(
        default=0.05,
        gt=0,
        lt=1,
    )


class EffectSizeRequest(BaseModel):
    test: Literal[
        "independent_t",
        "paired_t",
        "anova",
        "chi_square",
        "correlation",
    ]

    column: str | None = None
    group_column: str | None = None

    group1: str | int | float | None = None
    group2: str | int | float | None = None

    column1: str | None = None
    column2: str | None = None

    method: Literal[
        "pearson",
        "spearman",
        "kendall",
    ] = "pearson"


class RecommendationRequest(BaseModel):
    goal: Literal[
        "compare_groups",
        "relationship",
        "prediction",
        "distribution",
    ]

    outcome: str | None = None

    group: str | None = None

    variables: list[str] | None = None

    predictors: list[str] | None = None

    paired_column: str | None = None

    alpha: float = Field(
        default=0.05,
        gt=0,
        lt=1,
    )

    measurement_levels: dict[
        str,
        MeasurementLevel,
    ] | None = None
