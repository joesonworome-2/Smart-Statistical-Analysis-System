from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class CorrelationAnalysisRequest(
    BaseModel
):
    variables: list[str]

    method: Literal[
        "auto",
        "pearson",
        "spearman",
        "kendall",
    ] = "auto"

    alpha: float = Field(
        default=0.05,
        gt=0,
        lt=1,
    )

    confidence_level: float = Field(
        default=0.95,
        gt=0,
        lt=1,
    )

    @field_validator(
        "variables"
    )
    @classmethod
    def validate_variables(
        cls,
        value,
    ):
        cleaned = [
            str(variable).strip()
            for variable
            in value
            if str(
                variable
            ).strip()
        ]

        if len(cleaned) < 2:
            raise ValueError(
                (
                    "At least two "
                    "variables are required."
                )
            )

        if (
            len(
                set(cleaned)
            )
            !=
            len(cleaned)
        ):
            raise ValueError(
                (
                    "Duplicate variables "
                    "are not allowed."
                )
            )

        return cleaned
