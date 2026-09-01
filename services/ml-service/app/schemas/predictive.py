from typing import Any

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class PredictiveMLRequest(BaseModel):
    dependent_variable: str

    predictors: list[str]

    rows: list[
        dict[
            str,
            Any
        ]
    ]

    test_size: float = Field(
        default=0.20,
        ge=0.10,
        le=0.40,
    )

    random_seed: int = 42

    cv_folds: int = Field(
        default=5,
        ge=3,
        le=10,
    )

    future_values: dict[
        str,
        float
    ] | None = None

    time_variable: str | None = None


    @field_validator(
        "dependent_variable"
    )
    @classmethod
    def validate_outcome(
        cls,
        value,
    ):
        value = str(
            value
        ).strip()

        if not value:
            raise ValueError(
                "A dependent variable is required."
            )

        return value


    @field_validator(
        "predictors"
    )
    @classmethod
    def validate_predictors(
        cls,
        value,
    ):
        cleaned = [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

        if not cleaned:
            raise ValueError(
                "At least one predictor is required."
            )

        if len(
            cleaned
        ) != len(
            set(cleaned)
        ):
            raise ValueError(
                "Predictors must be unique."
            )

        return cleaned
