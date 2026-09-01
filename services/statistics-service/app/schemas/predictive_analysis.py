from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class PredictiveAnalysisRequest(BaseModel):
    dependent_variable: str

    predictors: list[str]

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
    def validate_dependent(
        cls,
        value,
    ):
        value = str(
            value
        ).strip()

        if not value:
            raise ValueError(
                "Select an outcome variable."
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
                "Select at least one predictor."
            )

        if len(
            cleaned
        ) != len(
            set(cleaned)
        ):
            raise ValueError(
                "Duplicate predictors are not allowed."
            )

        return cleaned
