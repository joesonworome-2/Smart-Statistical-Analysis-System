from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class RegressionAnalysisRequest(BaseModel):
    dependent_variable: str

    predictors: list[str]

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

    include_intercept: bool = True


    @field_validator(
        "dependent_variable"
    )
    @classmethod
    def validate_dependent_variable(
        cls,
        value,
    ):
        value = str(
            value
        ).strip()

        if not value:
            raise ValueError(
                "Select a dependent variable."
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
