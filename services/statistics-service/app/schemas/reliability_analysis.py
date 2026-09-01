from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class ReliabilityAnalysisRequest(BaseModel):
    variables: list[str]

    alpha: float = Field(
        default=0.05,
        ge=0.001,
        le=0.20,
    )

    item_total_threshold: float = Field(
        default=0.30,
        ge=-1.0,
        le=1.0,
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
                "Select at least two scale items."
            )


        if len(
            self.variables
        ) != len(
            set(
                self.variables
            )
        ):
            raise ValueError(
                "Duplicate reliability items "
                "are not allowed."
            )


        return self
