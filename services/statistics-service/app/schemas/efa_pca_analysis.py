from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class EfaPcaAnalysisRequest(BaseModel):
    variables: list[str]

    method: Literal[
        "pca",
        "efa",
    ] = "pca"

    n_factors: int | None = Field(
        default=None,
        ge=1,
        le=50,
    )

    rotation: Literal[
        "none",
        "varimax",
    ] = "varimax"

    alpha: float = Field(
        default=0.05,
        ge=0.001,
        le=0.20,
    )

    loading_threshold: float = Field(
        default=0.40,
        ge=0.10,
        le=0.90,
    )


    @model_validator(
        mode="after"
    )
    def validate_configuration(
        self,
    ):
        self.variables = [
            str(
                variable
            ).strip()
            for variable
            in self.variables
            if str(
                variable
            ).strip()
        ]


        if len(
            self.variables
        ) < 2:
            raise ValueError(
                "Select at least two variables."
            )


        if len(
            self.variables
        ) != len(
            set(
                self.variables
            )
        ):
            raise ValueError(
                "Duplicate variables are not allowed."
            )


        if (
            self.n_factors
            is not None
            and
            self.n_factors
            >
            len(
                self.variables
            )
        ):
            raise ValueError(
                "The number of factors/components "
                "cannot exceed the number of variables."
            )


        return self
