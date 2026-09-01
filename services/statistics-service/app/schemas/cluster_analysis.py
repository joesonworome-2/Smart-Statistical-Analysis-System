from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ClusterAnalysisRequest(BaseModel):
    variables: list[str]

    method: Literal[
        "kmeans",
        "hierarchical",
    ] = "kmeans"

    n_clusters: int | None = Field(
        default=None,
        ge=2,
        le=20,
    )

    standardize: bool = True

    max_auto_clusters: int = Field(
        default=8,
        ge=2,
        le=20,
    )

    @model_validator(mode="after")
    def validate_request(self):
        self.variables = [
            str(item).strip()
            for item in self.variables
            if str(item).strip()
        ]

        if len(self.variables) < 2:
            raise ValueError(
                "Select at least two numeric variables."
            )

        if len(self.variables) != len(set(self.variables)):
            raise ValueError(
                "Duplicate variables are not allowed."
            )

        return self
