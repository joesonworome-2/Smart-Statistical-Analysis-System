from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class AncovaAnalysisRequest(BaseModel):
    dependent_variable: str

    factor_variable: str

    covariates: list[str]

    alpha: float = Field(
        default=0.05,
        ge=0.001,
        le=0.20,
    )

    confidence_level: float = Field(
        default=0.95,
        ge=0.80,
        le=0.999,
    )


    @model_validator(
        mode="after"
    )
    def validate_configuration(
        self,
    ):
        self.dependent_variable = (
            self.dependent_variable
            .strip()
        )

        self.factor_variable = (
            self.factor_variable
            .strip()
        )

        self.covariates = [
            item.strip()
            for item
            in self.covariates
            if item.strip()
        ]


        if not self.dependent_variable:
            raise ValueError(
                "Select a dependent variable."
            )


        if not self.factor_variable:
            raise ValueError(
                "Select a factor variable."
            )


        if not self.covariates:
            raise ValueError(
                "Select at least one covariate."
            )


        if (
            self.dependent_variable
            ==
            self.factor_variable
        ):
            raise ValueError(
                "The dependent variable "
                "and factor variable must "
                "be different."
            )


        if (
            self.dependent_variable
            in
            self.covariates
        ):
            raise ValueError(
                "The dependent variable "
                "cannot also be a covariate."
            )


        if (
            self.factor_variable
            in
            self.covariates
        ):
            raise ValueError(
                "The factor variable "
                "cannot also be a covariate."
            )


        if len(
            self.covariates
        ) != len(
            set(
                self.covariates
            )
        ):
            raise ValueError(
                "Covariates must be unique."
            )


        return self
