from pathlib import Path
from datetime import datetime, timezone
import math

import joblib
import numpy as np
import pandas as pd
from bson import ObjectId

from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import (
    LinearRegression,
    LogisticRegression,
)
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.config import settings
from app.database import ml_results_collection


MODEL_DIR = Path(settings.model_storage_path)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def clean_number(value):
    if value is None:
        return None

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating, float)):
        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    return value


def validate_columns(df, features, target=None):
    requested = list(features)

    if target:
        requested.append(target)

    missing = [
        column
        for column in requested
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Unknown columns: " + ", ".join(missing)
        )

    if target and target in features:
        raise ValueError(
            "Target column cannot also be a feature."
        )

    if not features:
        raise ValueError(
            "At least one feature column is required."
        )


def build_preprocessor(X):
    numeric_columns = X.select_dtypes(
        include=np.number
    ).columns.tolist()

    categorical_columns = [
        column
        for column in X.columns
        if column not in numeric_columns
    ]

    transformers = []

    if numeric_columns:
        numeric_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ])

        transformers.append(
            (
                "numeric",
                numeric_pipeline,
                numeric_columns,
            )
        )

    if categorical_columns:
        categorical_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ])

        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical_columns,
            )
        )

    if not transformers:
        raise ValueError(
            "No usable feature columns were found."
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )


def save_model(
    pipeline,
    user_id,
    dataset_id,
    task,
    algorithm,
    features,
    target=None,
    metrics=None,
):
    model_id = ObjectId()

    model_path = MODEL_DIR / f"{model_id}.joblib"

    artifact = {
        "pipeline": pipeline,
        "task": task,
        "algorithm": algorithm,
        "features": features,
        "target": target,
    }

    joblib.dump(artifact, model_path)

    document = {
        "_id": model_id,
        "user_id": user_id,
        "dataset_id": dataset_id,
        "task": task,
        "algorithm": algorithm,
        "features": features,
        "target": target,
        "metrics": metrics or {},
        "model_path": str(model_path),
        "created_at": datetime.now(timezone.utc),
    }

    ml_results_collection.insert_one(document)

    return str(model_id), model_path


def train_regression(
    df,
    user_id,
    dataset_id,
    features,
    target,
    algorithm,
    test_size,
    random_state,
):
    validate_columns(
        df,
        features,
        target,
    )

    working = df[
        features + [target]
    ].copy()

    working[target] = pd.to_numeric(
        working[target],
        errors="coerce",
    )

    working = working.dropna(
        subset=[target]
    )

    if len(working) < 4:
        raise ValueError(
            "Regression requires at least 4 usable rows."
        )

    X = working[features]
    y = working[target]

    preprocessor = build_preprocessor(X)

    if algorithm == "linear_regression":
        estimator = LinearRegression()

    elif algorithm == "random_forest_regression":
        estimator = RandomForestRegressor(
            n_estimators=100,
            random_state=random_state,
        )

    else:
        raise ValueError(
            "Unsupported regression algorithm."
        )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    pipeline.fit(
        X_train,
        y_train,
    )

    predictions = pipeline.predict(X_test)

    mae = mean_absolute_error(
        y_test,
        predictions,
    )

    mse = mean_squared_error(
        y_test,
        predictions,
    )

    rmse = np.sqrt(mse)

    if len(y_test) >= 2:
        r2 = r2_score(
            y_test,
            predictions,
        )
    else:
        r2 = None

    metrics = {
        "r2": clean_number(r2),
        "mae": clean_number(mae),
        "mse": clean_number(mse),
        "rmse": clean_number(rmse),
        "training_rows": int(len(X_train)),
        "testing_rows": int(len(X_test)),
    }

    model_id, model_path = save_model(
        pipeline=pipeline,
        user_id=user_id,
        dataset_id=dataset_id,
        task="regression",
        algorithm=algorithm,
        features=features,
        target=target,
        metrics=metrics,
    )

    return {
        "model_id": model_id,
        "task": "regression",
        "algorithm": algorithm,
        "features": features,
        "target": target,
        "metrics": metrics,
        "model_saved": True,
        "model_path": str(model_path),
    }


def train_classification(
    df,
    user_id,
    dataset_id,
    features,
    target,
    algorithm,
    test_size,
    random_state,
):
    validate_columns(
        df,
        features,
        target,
    )

    working = df[
        features + [target]
    ].copy()

    working = working.dropna(
        subset=[target]
    )

    if len(working) < 4:
        raise ValueError(
            "Classification requires at least 4 usable rows."
        )

    X = working[features]
    y = working[target]

    if y.nunique() < 2:
        raise ValueError(
            "Classification requires at least two target classes."
        )

    preprocessor = build_preprocessor(X)

    if algorithm == "logistic_regression":
        estimator = LogisticRegression(
            max_iter=2000,
            random_state=random_state,
        )

    elif algorithm == "random_forest_classification":
        estimator = RandomForestClassifier(
            n_estimators=100,
            random_state=random_state,
        )

    else:
        raise ValueError(
            "Unsupported classification algorithm."
        )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

    stratify = None

    class_counts = y.value_counts()

    if (
        len(class_counts) >= 2
        and class_counts.min() >= 2
    ):
        stratify = y

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify,
        )

    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=None,
        )

    if y_train.nunique() < 2:
        raise ValueError(
            "Training split contains fewer than two classes. "
            "Use a larger dataset or change test_size."
        )

    pipeline.fit(
        X_train,
        y_train,
    )

    predictions = pipeline.predict(X_test)

    labels = sorted(
        list(
            set(y_test.tolist())
            | set(predictions.tolist())
        ),
        key=str,
    )

    metrics = {
        "accuracy": clean_number(
            accuracy_score(
                y_test,
                predictions,
            )
        ),
        "precision": clean_number(
            precision_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0,
            )
        ),
        "recall": clean_number(
            recall_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0,
            )
        ),
        "f1_score": clean_number(
            f1_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0,
            )
        ),
        "confusion_matrix": confusion_matrix(
            y_test,
            predictions,
            labels=labels,
        ).tolist(),
        "labels": [
            str(label)
            for label in labels
        ],
        "training_rows": int(len(X_train)),
        "testing_rows": int(len(X_test)),
    }

    model_id, model_path = save_model(
        pipeline=pipeline,
        user_id=user_id,
        dataset_id=dataset_id,
        task="classification",
        algorithm=algorithm,
        features=features,
        target=target,
        metrics=metrics,
    )

    return {
        "model_id": model_id,
        "task": "classification",
        "algorithm": algorithm,
        "features": features,
        "target": target,
        "metrics": metrics,
        "model_saved": True,
        "model_path": str(model_path),
    }


def train_clustering(
    df,
    user_id,
    dataset_id,
    features,
    algorithm,
    n_clusters,
    random_state,
):
    validate_columns(
        df,
        features,
    )

    X = df[features].copy()

    if len(X) <= n_clusters:
        raise ValueError(
            "Number of rows must be greater than n_clusters."
        )

    preprocessor = build_preprocessor(X)

    if algorithm != "kmeans":
        raise ValueError(
            "Unsupported clustering algorithm."
        )

    estimator = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=10,
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

    labels = pipeline.fit_predict(X)

    transformed = pipeline.named_steps[
        "preprocessor"
    ].transform(X)

    unique_labels = np.unique(labels)

    silhouette = None

    if (
        len(unique_labels) > 1
        and len(unique_labels) < len(X)
    ):
        silhouette = silhouette_score(
            transformed,
            labels,
        )

    cluster_counts = {
        str(cluster): int(count)
        for cluster, count in zip(
            *np.unique(
                labels,
                return_counts=True,
            )
        )
    }

    metrics = {
        "n_clusters": int(n_clusters),
        "inertia": clean_number(
            pipeline.named_steps["model"].inertia_
        ),
        "silhouette_score": clean_number(
            silhouette
        ),
        "cluster_counts": cluster_counts,
        "rows": int(len(X)),
    }

    model_id, model_path = save_model(
        pipeline=pipeline,
        user_id=user_id,
        dataset_id=dataset_id,
        task="clustering",
        algorithm=algorithm,
        features=features,
        metrics=metrics,
    )

    return {
        "model_id": model_id,
        "task": "clustering",
        "algorithm": algorithm,
        "features": features,
        "metrics": metrics,
        "model_saved": True,
        "model_path": str(model_path),
    }


def load_model_artifact(model_path):
    path = Path(model_path)

    if not path.exists():
        raise ValueError(
            "Saved model file was not found."
        )

    return joblib.load(path)
