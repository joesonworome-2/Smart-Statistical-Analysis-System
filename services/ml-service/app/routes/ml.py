from pathlib import Path

import pandas as pd
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.database import ml_results_collection
from app.schemas.ml import (
    ClassificationTrainRequest,
    ClusteringTrainRequest,
    PredictionRequest,
    RegressionTrainRequest,
)
from app.security.dependencies import get_current_user
from app.services.dataset_reader import read_dataset
from app.services.ml_engine import (
    load_model_artifact,
    train_classification,
    train_clustering,
    train_regression,
)


router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"],
)


def identifier_columns(df):
    identifiers = []

    exact_names = {
        "id",
        "name",
        "full_name",
        "first_name",
        "last_name",
        "student_name",
        "username",
        "email",
        "phone",
    }

    for column in df.columns:
        lower = column.lower()

        if (
            lower in exact_names
            or lower.endswith("_id")
            or lower.startswith("id_")
            or lower.endswith("_uuid")
        ):
            identifiers.append(column)

    return identifiers


@router.get("/types")
def available_ml_types():
    return {
        "supervised_learning": {
            "regression": [
                "linear_regression",
                "random_forest_regression",
            ],
            "classification": [
                "logistic_regression",
                "random_forest_classification",
            ],
        },
        "unsupervised_learning": {
            "clustering": [
                "kmeans",
            ]
        },
        "evaluation": {
            "regression": [
                "r2",
                "mae",
                "mse",
                "rmse",
            ],
            "classification": [
                "accuracy",
                "precision",
                "recall",
                "f1_score",
                "confusion_matrix",
            ],
            "clustering": [
                "inertia",
                "silhouette_score",
            ],
        },
    }


@router.get("/profile/{dataset_id}")
def profile_dataset(
    dataset_id: str,
    current_user=Depends(get_current_user),
):
    df, dataset = read_dataset(
        dataset_id,
        current_user["id"],
    )

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = df.select_dtypes(
        include=[
            "object",
            "category",
            "bool",
        ]
    ).columns.tolist()

    identifiers = identifier_columns(df)

    missing_values = {
        column: int(count)
        for column, count
        in df.isnull().sum().items()
        if count > 0
    }

    classification_candidates = []

    threshold = min(
        20,
        max(
            2,
            int(len(df) * 0.20),
        ),
    )

    for column in df.columns:
        if column in identifiers:
            continue

        unique_count = df[column].nunique(
            dropna=True
        )

        if 2 <= unique_count <= threshold:
            classification_candidates.append(
                column
            )

    regression_candidates = [
        column
        for column in numeric_columns
        if column not in identifiers
        and df[column].nunique(
            dropna=True
        ) > 2
    ]

    warnings = []

    if len(df) < 10:
        warnings.append(
            "Very small dataset: ML results may be unstable."
        )

    elif len(df) < 30:
        warnings.append(
            "Small dataset: model evaluation should be interpreted cautiously."
        )

    return {
        "dataset_id": dataset_id,
        "dataset": dataset.get(
            "original_filename"
        ),
        "rows": len(df),
        "columns": len(df.columns),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "identifier_columns": identifiers,
        "missing_values": missing_values,
        "possible_targets": {
            "regression": regression_candidates,
            "classification": classification_candidates,
        },
        "ml_capabilities": {
            "regression": (
                len(numeric_columns) >= 2
            ),
            "classification": (
                len(classification_candidates) > 0
            ),
            "clustering": (
                len(numeric_columns) >= 2
            ),
        },
        "warnings": warnings,
    }


@router.post("/train/regression/{dataset_id}")
def regression(
    dataset_id: str,
    request: RegressionTrainRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    try:
        return train_regression(
            df=df,
            user_id=current_user["id"],
            dataset_id=dataset_id,
            features=request.features,
            target=request.target,
            algorithm=request.algorithm,
            test_size=request.test_size,
            random_state=request.random_state,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/train/classification/{dataset_id}")
def classification(
    dataset_id: str,
    request: ClassificationTrainRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    try:
        return train_classification(
            df=df,
            user_id=current_user["id"],
            dataset_id=dataset_id,
            features=request.features,
            target=request.target,
            algorithm=request.algorithm,
            test_size=request.test_size,
            random_state=request.random_state,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/train/clustering/{dataset_id}")
def clustering(
    dataset_id: str,
    request: ClusteringTrainRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    try:
        return train_clustering(
            df=df,
            user_id=current_user["id"],
            dataset_id=dataset_id,
            features=request.features,
            algorithm=request.algorithm,
            n_clusters=request.n_clusters,
            random_state=request.random_state,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/models")
def models(
    current_user=Depends(get_current_user),
):
    records = ml_results_collection.find(
        {
            "user_id": current_user["id"]
        }
    ).sort(
        "created_at",
        -1,
    )

    results = []

    for record in records:
        results.append({
            "model_id": str(record["_id"]),
            "dataset_id": record.get(
                "dataset_id"
            ),
            "task": record.get("task"),
            "algorithm": record.get(
                "algorithm"
            ),
            "features": record.get(
                "features"
            ),
            "target": record.get(
                "target"
            ),
            "metrics": record.get(
                "metrics"
            ),
            "created_at": (
                record["created_at"].isoformat()
                if record.get("created_at")
                else None
            ),
        })

    return {
        "count": len(results),
        "models": results,
    }


@router.get("/models/{model_id}")
def model_details(
    model_id: str,
    current_user=Depends(get_current_user),
):
    try:
        oid = ObjectId(model_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid model ID.",
        )

    record = ml_results_collection.find_one({
        "_id": oid,
        "user_id": current_user["id"],
    })

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    return {
        "model_id": str(record["_id"]),
        "dataset_id": record.get(
            "dataset_id"
        ),
        "task": record.get("task"),
        "algorithm": record.get(
            "algorithm"
        ),
        "features": record.get(
            "features"
        ),
        "target": record.get(
            "target"
        ),
        "metrics": record.get(
            "metrics"
        ),
        "created_at": (
            record["created_at"].isoformat()
            if record.get("created_at")
            else None
        ),
    }


@router.post("/predict/{model_id}")
def predict(
    model_id: str,
    request: PredictionRequest,
    current_user=Depends(get_current_user),
):
    try:
        oid = ObjectId(model_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid model ID.",
        )

    record = ml_results_collection.find_one({
        "_id": oid,
        "user_id": current_user["id"],
    })

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    if not request.rows:
        raise HTTPException(
            status_code=400,
            detail="At least one prediction row is required.",
        )

    try:
        artifact = load_model_artifact(
            record["model_path"]
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    features = artifact["features"]

    dataframe = pd.DataFrame(
        request.rows
    )

    missing = [
        feature
        for feature in features
        if feature not in dataframe.columns
    ]

    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                "Missing prediction features: "
                + ", ".join(missing)
            ),
        )

    pipeline = artifact["pipeline"]

    predictions = pipeline.predict(
        dataframe[features]
    )

    values = []

    for value in predictions:
        if hasattr(value, "item"):
            value = value.item()

        values.append(value)

    return {
        "model_id": model_id,
        "task": artifact["task"],
        "algorithm": artifact["algorithm"],
        "predictions": values,
    }
