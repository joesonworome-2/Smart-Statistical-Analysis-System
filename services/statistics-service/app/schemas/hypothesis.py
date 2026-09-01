from typing import Literal

from pydantic import BaseModel, Field


class HypothesisRequest(BaseModel):
    family: Literal[
        "parametric",
        "nonparametric",
    ] = "parametric"

    metric_variables: list[str] = []

    categorical_variables: list[str] = []

    test_value: float = 0.0

    alternative: Literal[
        "two-sided",
        "greater",
        "less",
    ] = "two-sided"

    alpha: float = Field(
        default=0.05,
        gt=0,
        lt=1,
    )
