from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class SurvivalAnalysisRequest(BaseModel):
    duration_variable: str

    event_variable: str

    event_value: str = "1"

    group_variable: Optional[str] = None

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
        self.duration_variable = (
            self.duration_variable
            .strip()
        )

        self.event_variable = (
            self.event_variable
            .strip()
        )

        self.event_value = (
            str(
                self.event_value
            )
            .strip()
        )

        if self.group_variable:
            self.group_variable = (
                self.group_variable
                .strip()
            )

        if not self.duration_variable:
            raise ValueError(
                "Select a duration variable."
            )

        if not self.event_variable:
            raise ValueError(
                "Select an event indicator variable."
            )

        if not self.event_value:
            raise ValueError(
                "Specify the value that represents an event."
            )

        if (
            self.duration_variable
            ==
            self.event_variable
        ):
            raise ValueError(
                "Duration and event variables "
                "must be different."
            )

        if (
            self.group_variable
            and
            self.group_variable
            ==
            self.duration_variable
        ):
            raise ValueError(
                "The grouping variable cannot "
                "also be the duration variable."
            )

        if (
            self.group_variable
            and
            self.group_variable
            ==
            self.event_variable
        ):
            raise ValueError(
                "The grouping variable cannot "
                "also be the event variable."
            )

        return self
