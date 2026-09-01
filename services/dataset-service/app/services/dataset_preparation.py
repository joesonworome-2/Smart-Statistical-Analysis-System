import math
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from bson import ObjectId
from fastapi import HTTPException

from app.config import settings
from app.database import datasets_collection
from app.models.dataset import create_dataset_document


# ============================================================
# Dataset access
# ============================================================

def get_owned_dataset(
    dataset_id: str,
    user_id: str,
):
    try:
        object_id = ObjectId(dataset_id)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one(
        {
            "_id": object_id,
            "user_id": user_id,
        }
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    return dataset


def get_dataset_path(dataset):
    return (
        Path(settings.upload_directory)
        / dataset["filename"]
    )


def read_owned_dataset(
    dataset_id: str,
    user_id: str,
):
    dataset = get_owned_dataset(
        dataset_id,
        user_id,
    )

    path = get_dataset_path(dataset)

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found.",
        )

    suffix = path.suffix.lower()

    try:
        if suffix == ".csv":
            df = pd.read_csv(path)

        elif suffix in {
            ".xlsx",
            ".xls",
        }:
            df = pd.read_excel(path)

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported dataset "
                    f"type: {suffix}"
                ),
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to read dataset: "
                f"{exc}"
            ),
        )

    return df, dataset


# ============================================================
# JSON conversion
# ============================================================

def clean_value(value):
    if pd.isna(value):
        return None

    if isinstance(
        value,
        (np.integer,),
    ):
        return int(value)

    if isinstance(
        value,
        (np.floating,),
    ):
        value = float(value)

        if (
            math.isnan(value)
            or math.isinf(value)
        ):
            return None

        return value

    if isinstance(
        value,
        (pd.Timestamp,),
    ):
        return value.isoformat()

    return value


# ============================================================
# Variable metadata
# ============================================================

def normalized_name(name: str):
    return (
        str(name)
        .lower()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
    )


def infer_variable_metadata(
    column: str,
    series: pd.Series,
):
    non_missing = series.dropna()

    unique_count = int(
        non_missing.nunique()
    )

    row_count = len(series)

    unique_ratio = (
        unique_count
        / len(non_missing)
        if len(non_missing)
        else 0
    )

    name = normalized_name(column)

    possible_identifier = (
        name.endswith("id")
        or name == "id"
        or "uuid" in name
        or name.endswith("code")
    )

    # Identifier
    if (
        possible_identifier
        and unique_ratio >= 0.8
    ):
        return {
            "measurement_level":
                "nominal",
            "semantic_role":
                "identifier",
            "exclude_from_recommendations":
                True,
            "confidence":
                "high",
            "reason":
                "High-cardinality identifier "
                "column.",
        }

    # Date / time
    if pd.api.types.is_datetime64_any_dtype(
        series
    ):
        return {
            "measurement_level":
                "metric",
            "semantic_role":
                "datetime",
            "exclude_from_recommendations":
                False,
            "confidence":
                "high",
            "reason":
                "Date/time variable.",
        }

    # Boolean
    if pd.api.types.is_bool_dtype(
        series
    ):
        return {
            "measurement_level":
                "nominal",
            "semantic_role":
                "group",
            "exclude_from_recommendations":
                False,
            "confidence":
                "high",
            "reason":
                "Boolean categorical "
                "variable.",
        }

    # Numeric
    if pd.api.types.is_numeric_dtype(
        series
    ):
        if unique_count <= 2:
            return {
                "measurement_level":
                    "nominal",
                "semantic_role":
                    "group",
                "exclude_from_recommendations":
                    False,
                "confidence":
                    "medium",
                "reason":
                    "Binary numeric variable.",
            }

        return {
            "measurement_level":
                "metric",
            "semantic_role":
                "feature",
            "exclude_from_recommendations":
                False,
            "confidence":
                "high",
            "reason":
                "Numeric variable with "
                "multiple values.",
        }

    # High-cardinality text
    if unique_ratio >= 0.8:
        return {
            "measurement_level":
                "nominal",
            "semantic_role":
                (
                    "identifier"
                    if possible_identifier
                    else "feature"
                ),
            "exclude_from_recommendations":
                possible_identifier,
            "confidence":
                "medium",
            "reason":
                "High-cardinality text "
                "variable.",
        }

    # Normal categorical
    return {
        "measurement_level":
            "nominal",
        "semantic_role":
            "group"
            if unique_count <= 20
            else "feature",
        "exclude_from_recommendations":
            False,
        "confidence":
            "medium",
        "reason":
            "Categorical variable.",
    }


def stored_metadata_map(dataset):
    return {
        item["name"]: item
        for item in dataset.get(
            "variable_metadata",
            [],
        )
        if item.get("name")
    }


def variable_metadata(
    df: pd.DataFrame,
    dataset,
):
    stored = stored_metadata_map(
        dataset
    )

    result = []

    for column in df.columns:
        series = df[column]

        detected = (
            infer_variable_metadata(
                str(column),
                series,
            )
        )

        override = stored.get(
            str(column),
            {},
        )

        effective = {
            **detected,
            **{
                key: value
                for key, value
                in override.items()
                if (
                    key != "name"
                    and value is not None
                )
            },
        }

        result.append(
            {
                "name":
                    str(column),

                "pandas_dtype":
                    str(series.dtype),

                "missing_count":
                    int(
                        series
                        .isna()
                        .sum()
                    ),

                "missing_percent":
                    round(
                        (
                            series
                            .isna()
                            .sum()
                            / len(series)
                            * 100
                        )
                        if len(series)
                        else 0,
                        2,
                    ),

                "unique_count":
                    int(
                        series
                        .dropna()
                        .nunique()
                    ),

                **effective,

                "user_override":
                    bool(override),
            }
        )

    return result


def update_variable_metadata(
    dataset_id,
    user_id,
    column,
    request,
):
    dataset = get_owned_dataset(
        dataset_id,
        user_id,
    )

    if column not in dataset.get(
        "columns",
        [],
    ):
        raise ValueError(
            f"Unknown column: {column}"
        )

    metadata = dataset.get(
        "variable_metadata",
        [],
    )

    existing = None

    for item in metadata:
        if item.get("name") == column:
            existing = item
            break

    updates = request.model_dump(
        exclude_none=True
    )

    if existing is None:
        existing = {
            "name": column,
        }

        metadata.append(existing)

    existing.update(updates)

    datasets_collection.update_one(
        {
            "_id": dataset["_id"],
            "user_id": user_id,
        },
        {
            "$set": {
                "variable_metadata":
                    metadata,

                "updated_at":
                    datetime.now(
                        timezone.utc
                    ),
            }
        },
    )

    return existing


# ============================================================
# Dataset profile
# ============================================================

def dataset_profile(df):
    numeric = df.select_dtypes(
        include=np.number
    )

    datetime_columns = [
        column
        for column in df.columns
        if pd.api.types.is_datetime64_any_dtype(
            df[column]
        )
    ]

    missing_by_column = {
        str(column):
            int(df[column].isna().sum())
        for column in df.columns
    }

    total_missing = int(
        df.isna().sum().sum()
    )

    total_cells = (
        len(df)
        * len(df.columns)
    )

    return {
        "row_count":
            len(df),

        "column_count":
            len(df.columns),

        "duplicate_rows":
            int(
                df.duplicated().sum()
            ),

        "total_missing_values":
            total_missing,

        "missing_percent":
            round(
                (
                    total_missing
                    / total_cells
                    * 100
                )
                if total_cells
                else 0,
                2,
            ),

        "numeric_columns":
            len(numeric.columns),

        "datetime_columns":
            len(datetime_columns),

        "other_columns":
            (
                len(df.columns)
                - len(numeric.columns)
                - len(datetime_columns)
            ),

        "missing_by_column":
            missing_by_column,
    }


# ============================================================
# Missing values
# ============================================================

def missing_value_summary(df):
    result = []

    for column in df.columns:
        missing = int(
            df[column]
            .isna()
            .sum()
        )

        result.append(
            {
                "column":
                    str(column),

                "missing_count":
                    missing,

                "missing_percent":
                    round(
                        (
                            missing
                            / len(df)
                            * 100
                        )
                        if len(df)
                        else 0,
                        2,
                    ),

                "non_missing_count":
                    int(
                        df[column]
                        .notna()
                        .sum()
                    ),
            }
        )

    return result


def prepare_missing_values(
    df,
    request,
):
    columns = request.columns

    if not columns:
        raise ValueError(
            "At least one column "
            "is required."
        )

    missing = [
        column
        for column in columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Unknown columns: "
            + ", ".join(missing)
        )

    result = df.copy()

    before = len(result)

    if request.strategy == "drop_rows":
        result = result.dropna(
            subset=columns
        )

    else:
        for column in columns:

            if request.strategy in {
                "mean",
                "median",
            }:
                numeric = pd.to_numeric(
                    result[column],
                    errors="coerce",
                )

                if (
                    numeric
                    .dropna()
                    .empty
                ):
                    raise ValueError(
                        f"{column} is not "
                        "suitable for "
                        f"{request.strategy} "
                        "imputation."
                    )

                if request.strategy == "mean":
                    fill = numeric.mean()
                else:
                    fill = numeric.median()

                result[column] = (
                    numeric.fillna(fill)
                )

            elif request.strategy == "mode":
                mode = (
                    result[column]
                    .mode(
                        dropna=True
                    )
                )

                if mode.empty:
                    raise ValueError(
                        f"No mode exists "
                        f"for {column}."
                    )

                result[column] = (
                    result[column]
                    .fillna(
                        mode.iloc[0]
                    )
                )

            elif request.strategy == "constant":
                if request.fill_value is None:
                    raise ValueError(
                        "fill_value is "
                        "required for "
                        "constant imputation."
                    )

                result[column] = (
                    result[column]
                    .fillna(
                        request.fill_value
                    )
                )

    return result, {
        "strategy":
            request.strategy,

        "columns":
            columns,

        "rows_before":
            before,

        "rows_after":
            len(result),

        "rows_removed":
            before - len(result),
    }


# ============================================================
# Outliers
# ============================================================

def outlier_information(
    df,
    column,
    method="iqr",
    threshold=1.5,
):
    if column not in df.columns:
        raise ValueError(
            f"Unknown column: {column}"
        )

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    )

    valid = values.dropna()

    if valid.empty:
        raise ValueError(
            "Outlier detection requires "
            "a numeric column."
        )

    if method == "iqr":
        q1 = valid.quantile(0.25)
        q3 = valid.quantile(0.75)

        iqr = q3 - q1

        lower = (
            q1
            - threshold * iqr
        )

        upper = (
            q3
            + threshold * iqr
        )

        mask = (
            (values < lower)
            | (values > upper)
        )

    elif method == "zscore":
        mean = valid.mean()
        std = valid.std(ddof=1)

        if (
            std == 0
            or pd.isna(std)
        ):
            raise ValueError(
                "Z-score cannot be "
                "calculated because the "
                "standard deviation is zero."
            )

        lower = (
            mean
            - threshold * std
        )

        upper = (
            mean
            + threshold * std
        )

        mask = (
            (values < lower)
            | (values > upper)
        )

    else:
        raise ValueError(
            "Unsupported outlier method."
        )

    indexes = (
        df.index[mask.fillna(False)]
        .tolist()
    )

    return {
        "method":
            method,

        "threshold":
            threshold,

        "column":
            column,

        "lower_bound":
            clean_value(lower),

        "upper_bound":
            clean_value(upper),

        "outlier_count":
            len(indexes),

        "outlier_percent":
            round(
                (
                    len(indexes)
                    / len(df)
                    * 100
                )
                if len(df)
                else 0,
                2,
            ),

        "row_indexes":
            indexes[:100],
    }


def prepare_outliers(
    df,
    request,
):
    information = (
        outlier_information(
            df,
            request.column,
            request.method,
            request.threshold,
        )
    )

    result = df.copy()

    values = pd.to_numeric(
        result[
            request.column
        ],
        errors="coerce",
    )

    lower = information[
        "lower_bound"
    ]

    upper = information[
        "upper_bound"
    ]

    mask = (
        (values < lower)
        | (values > upper)
    )

    mask = mask.fillna(False)

    before = len(result)

    if request.action == "remove":
        result = result.loc[
            ~mask
        ].copy()

    elif request.action == "clip":
        result[
            request.column
        ] = values.clip(
            lower=lower,
            upper=upper,
        )

    return result, {
        **information,

        "action":
            request.action,

        "rows_before":
            before,

        "rows_after":
            len(result),
    }


# ============================================================
# Transformations
# ============================================================

def transform_dataset(
    df,
    request,
):
    if request.column not in df.columns:
        raise ValueError(
            f"Unknown column: "
            f"{request.column}"
        )

    result = df.copy()

    target = (
        request.new_column
        or (
            request.column
            + "_"
            + request.transformation
        )
    )

    if request.transformation in {
        "standardize",
        "normalize",
        "log1p",
    }:
        values = pd.to_numeric(
            result[
                request.column
            ],
            errors="coerce",
        )

        if values.dropna().empty:
            raise ValueError(
                "Transformation requires "
                "a numeric column."
            )

        if (
            request.transformation
            == "standardize"
        ):
            mean = values.mean()
            std = values.std(
                ddof=1
            )

            if (
                std == 0
                or pd.isna(std)
            ):
                raise ValueError(
                    "Cannot standardize "
                    "a zero-variance "
                    "variable."
                )

            result[target] = (
                values - mean
            ) / std

        elif (
            request.transformation
            == "normalize"
        ):
            minimum = values.min()
            maximum = values.max()

            difference = (
                maximum - minimum
            )

            if difference == 0:
                raise ValueError(
                    "Cannot normalize "
                    "a constant variable."
                )

            result[target] = (
                values - minimum
            ) / difference

        elif (
            request.transformation
            == "log1p"
        ):
            if (
                values
                .dropna()
                .min()
                <= -1
            ):
                raise ValueError(
                    "log1p requires "
                    "values greater than -1."
                )

            result[target] = (
                np.log1p(values)
            )

    elif request.transformation == "recode":
        if not request.mapping:
            raise ValueError(
                "A mapping is required "
                "for recoding."
            )

        result[target] = (
            result[
                request.column
            ]
            .map(
                lambda value:
                    request.mapping.get(
                        str(value),
                        value,
                    )
            )
        )

    return result, {
        "source_column":
            request.column,

        "new_column":
            target,

        "transformation":
            request.transformation,
    }


# ============================================================
# Filtering
# ============================================================

def filter_dataset(
    df,
    request,
):
    if request.column not in df.columns:
        raise ValueError(
            f"Unknown column: "
            f"{request.column}"
        )

    series = df[request.column]

    operator = request.operator

    if operator == "eq":
        mask = (
            series == request.value
        )

    elif operator == "ne":
        mask = (
            series != request.value
        )

    elif operator == "gt":
        mask = (
            series > request.value
        )

    elif operator == "gte":
        mask = (
            series >= request.value
        )

    elif operator == "lt":
        mask = (
            series < request.value
        )

    elif operator == "lte":
        mask = (
            series <= request.value
        )

    elif operator == "in":
        if not isinstance(
            request.value,
            list,
        ):
            raise ValueError(
                "'in' requires a list "
                "as value."
            )

        mask = series.isin(
            request.value
        )

    elif operator == "contains":
        mask = (
            series
            .astype(str)
            .str.contains(
                str(
                    request.value
                ),
                case=False,
                na=False,
            )
        )

    elif operator == "between":
        if request.value2 is None:
            raise ValueError(
                "'between' requires "
                "value and value2."
            )

        mask = series.between(
            request.value,
            request.value2,
        )

    else:
        raise ValueError(
            "Unsupported filter operator."
        )

    result = df.loc[
        mask.fillna(False)
    ].copy()

    if result.empty:
        raise ValueError(
            "The filter produced "
            "an empty dataset."
        )

    return result, {
        "column":
            request.column,

        "operator":
            operator,

        "value":
            request.value,

        "value2":
            request.value2,

        "rows_before":
            len(df),

        "rows_after":
            len(result),

        "rows_removed":
            len(df) - len(result),
    }


# ============================================================
# Save derived dataset
# ============================================================

def save_derived_dataset(
    df,
    source_dataset,
    user_id,
    operation,
    details,
):
    upload_directory = Path(
        settings.upload_directory
    )

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_name = (
        source_dataset.get(
            "original_filename",
            "dataset"
        )
    )

    source_stem = (
        Path(source_name).stem
    )

    unique_id = (
        uuid.uuid4().hex
    )

    # Excel source -> derived XLSX
    if (
        source_dataset.get(
            "file_type"
        )
        in {
            "xlsx",
            "xls",
        }
    ):
        extension = ".xlsx"

        filename = (
            unique_id
            + extension
        )

        path = (
            upload_directory
            / filename
        )

        df.to_excel(
            path,
            index=False,
        )

        file_type = "xlsx"

    else:
        extension = ".csv"

        filename = (
            unique_id
            + extension
        )

        path = (
            upload_directory
            / filename
        )

        df.to_csv(
            path,
            index=False,
        )

        file_type = "csv"

    original_filename = (
        source_stem
        + "_prepared_"
        + operation
        + extension
    )

    document = (
        create_dataset_document(
            user_id=user_id,
            filename=filename,
            original_filename=(
                original_filename
            ),
            file_type=file_type,
            file_size=path.stat().st_size,
            row_count=len(df),
            column_count=len(
                df.columns
            ),
            columns=[
                str(column)
                for column
                in df.columns
            ],
        )
    )

    document[
        "status"
    ] = "prepared"

    document[
        "is_derived"
    ] = True

    document[
        "source_dataset_id"
    ] = str(
        source_dataset["_id"]
    )

    previous_steps = (
        source_dataset.get(
            "preparation_steps",
            [],
        )
    )

    document[
        "preparation_steps"
    ] = [
        *previous_steps,
        {
            "operation":
                operation,

            "details":
                details,

            "created_at":
                datetime.now(
                    timezone.utc
                ),
        },
    ]

    document[
        "variable_metadata"
    ] = source_dataset.get(
        "variable_metadata",
        [],
    )

    try:
        inserted = (
            datasets_collection
            .insert_one(
                document
            )
        )

        document["_id"] = (
            inserted.inserted_id
        )

    except Exception:
        if path.exists():
            path.unlink()

        raise

    return {
        "id":
            str(
                document["_id"]
            ),

        "source_dataset_id":
            str(
                source_dataset["_id"]
            ),

        "original_filename":
            document[
                "original_filename"
            ],

        "filename":
            document[
                "filename"
            ],

        "file_type":
            document[
                "file_type"
            ],

        "row_count":
            document[
                "row_count"
            ],

        "column_count":
            document[
                "column_count"
            ],

        "columns":
            document[
                "columns"
            ],

        "status":
            document[
                "status"
            ],

        "is_derived":
            True,

        "operation":
            operation,

        "details":
            details,
    }
