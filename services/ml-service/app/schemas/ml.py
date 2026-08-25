from typing import Any, Literal

from pydantic import BaseModel, Field


class RegressionTrainRequest(BaseModel):
    target: str
    features: list[str]
    algorithm: Literal[
        "linear_regression",
        "random_forest_regression"
    ] = "linear_regression"
    test_size: float = Field(default=0.4, gt=0.0, lt=1.0)
    random_state: int = 42


class ClassificationTrainRequest(BaseModel):
    target: str
    features: list[str]
    algorithm: Literal[
        "logistic_regression",
        "random_forest_classification"
    ] = "logistic_regression"
    test_size: float = Field(default=0.4, gt=0.0, lt=1.0)
    random_state: int = 42


class ClusteringTrainRequest(BaseModel):
    features: list[str]
    algorithm: Literal["kmeans"] = "kmeans"
    n_clusters: int = Field(default=2, ge=2)
    random_state: int = 42


class PredictionRequest(BaseModel):
    rows: list[dict[str, Any]]
