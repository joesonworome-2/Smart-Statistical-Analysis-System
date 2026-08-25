from typing import Literal

from pydantic import BaseModel, Field


class CorrelationRequest(BaseModel):
    columns: list[str] | None = None
    method: Literal["pearson", "spearman", "kendall"] = "pearson"


class OneSampleTTestRequest(BaseModel):
    column: str
    population_mean: float


class IndependentTTestRequest(BaseModel):
    column: str
    group_column: str
    group1: str | int | float
    group2: str | int | float


class PairedTTestRequest(BaseModel):
    column1: str
    column2: str


class ChiSquareRequest(BaseModel):
    column1: str
    column2: str


class ShapiroRequest(BaseModel):
    column: str


class MannWhitneyRequest(BaseModel):
    column: str
    group_column: str
    group1: str | int | float
    group2: str | int | float


class WilcoxonRequest(BaseModel):
    column1: str
    column2: str


class KruskalWallisRequest(BaseModel):
    value_column: str
    group_column: str


class AnovaRequest(BaseModel):
    value_column: str
    group_column: str


class ConfidenceIntervalRequest(BaseModel):
    column: str
    confidence: float = Field(default=0.95, gt=0, lt=1)
