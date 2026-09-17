from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import (
    BaseModel,
    Field,
)

from app.config import settings
from app.database import datasets_collection
from app.security.dependencies import (
    get_current_user,
)
from app.services.dataset_preparation import (
    get_owned_dataset,
    read_owned_dataset,
    save_derived_dataset,
)


router = APIRouter(
    prefix="/datasets",
    tags=[
        "Dataset Spreadsheet",
        "Guided Preparation",
    ],
)


# ============================================================
# Request models
# ============================================================

class DatasetDataUpdate(BaseModel):
    columns: list[str] = Field(
        min_length=1
    )

    rows: list[
        dict[str, Any]
    ]


class WorkflowPreparationRequest(BaseModel):
    remove_duplicates: bool = True
    trim_text: bool = True
    normalize_blank_strings: bool = True
    coerce_numeric_strings: bool = True

    missing_strategy: Literal[
        "keep",
        "drop_rows",
        "mean",
        "median",
        "mode",
    ] = "keep"

    outlier_action: Literal[
        "keep",
        "clip_iqr",
        "remove_iqr",
    ] = "keep"


# ============================================================
# Helpers
# ============================================================

def current_user_id(
    current_user: dict,
) -> str:
    user_id = (
        current_user.get(
            "user_id"
        )
        or current_user.get(
            "id"
        )
        or current_user.get(
            "_id"
        )
    )

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=(
                "Authenticated user ID "
                "is missing."
            ),
        )

    return str(user_id)


def clean_columns(
    columns: list[str],
) -> list[str]:
    cleaned = [
        str(column).strip()
        for column in columns
    ]

    blank_indexes = [
        str(index + 1)
        for index, column
        in enumerate(cleaned)
        if not column
    ]

    if blank_indexes:
        raise HTTPException(
            status_code=400,
            detail=(
                "Every spreadsheet column "
                "must have a name. Blank "
                "column positions: "
                + ", ".join(
                    blank_indexes
                )
            ),
        )

    duplicates = sorted(
        {
            column
            for column in cleaned
            if cleaned.count(column) > 1
        }
    )

    if duplicates:
        raise HTTPException(
            status_code=400,
            detail=(
                "Column names must be unique. "
                "Duplicate names: "
                + ", ".join(
                    duplicates
                )
            ),
        )

    return cleaned


def make_dataframe(
    request: DatasetDataUpdate,
) -> pd.DataFrame:
    columns = clean_columns(
        request.columns
    )

    normalized_rows = []

    for row in request.rows:
        normalized_rows.append(
            {
                column:
                    row.get(
                        column,
                        None,
                    )
                for column in columns
            }
        )

    dataframe = pd.DataFrame(
        normalized_rows,
        columns=columns,
    )

    # A completely empty spreadsheet row is not
    # meaningful data and should not be persisted.
    dataframe = dataframe.replace(
        r"^\s*$",
        np.nan,
        regex=True,
    )

    dataframe = dataframe.dropna(
        how="all"
    ).reset_index(
        drop=True
    )

    return dataframe


def write_dataframe_to_existing_dataset(
    dataframe: pd.DataFrame,
    dataset: dict,
):
    upload_directory = Path(
        settings.upload_directory
    )

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    current_path = (
        upload_directory
        / dataset["filename"]
    )

    suffix = current_path.suffix.lower()

    new_filename = dataset[
        "filename"
    ]

    new_file_type = dataset[
        "file_type"
    ]

    try:
        if suffix == ".csv":
            dataframe.to_csv(
                current_path,
                index=False,
            )

        elif suffix == ".xlsx":
            dataframe.to_excel(
                current_path,
                index=False,
            )

        elif suffix == ".xls":
            # Pandas' modern Excel writer does not
            # safely overwrite old XLS files without
            # an additional legacy writer. Migrate the
            # editable copy to XLSX while keeping the
            # original XLS file untouched.
            new_filename = (
                current_path.stem
                + ".xlsx"
            )

            migrated_path = (
                upload_directory
                / new_filename
            )

            dataframe.to_excel(
                migrated_path,
                index=False,
            )

            current_path = (
                migrated_path
            )

            new_file_type = "xlsx"

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This dataset format cannot "
                    "be edited in the spreadsheet."
                ),
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save spreadsheet "
                f"changes: {exc}"
            ),
        )

    return (
        current_path,
        new_filename,
        new_file_type,
    )


def trim_text_columns(
    dataframe: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    list[str],
]:
    result = dataframe.copy()
    changed_columns = []

    for column in result.columns:
        series = result[column]

        if not (
            pd.api.types.is_object_dtype(
                series
            )
            or pd.api.types.is_string_dtype(
                series
            )
        ):
            continue

        before = series.copy()

        result[column] = series.map(
            lambda value:
                value.strip()
                if isinstance(
                    value,
                    str,
                )
                else value
        )

        try:
            changed = not result[
                column
            ].equals(before)
        except Exception:
            changed = True

        if changed:
            changed_columns.append(
                str(column)
            )

    return result, changed_columns


def coerce_mostly_numeric_text(
    dataframe: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    list[str],
]:
    result = dataframe.copy()
    converted_columns = []

    for column in result.columns:
        series = result[column]

        if not (
            pd.api.types.is_object_dtype(
                series
            )
            or pd.api.types.is_string_dtype(
                series
            )
        ):
            continue

        non_missing = series.dropna()

        if non_missing.empty:
            continue

        parsed = pd.to_numeric(
            non_missing,
            errors="coerce",
        )

        parse_ratio = (
            parsed.notna().sum()
            / len(non_missing)
        )

        # 80% numeric-like values is a practical
        # signal that the column probably contains
        # numeric data with a few entry errors.
        if parse_ratio >= 0.80:
            result[column] = pd.to_numeric(
                series,
                errors="coerce",
            )

            converted_columns.append(
                str(column)
            )

    return result, converted_columns


def fill_missing_values(
    dataframe: pd.DataFrame,
    strategy: str,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    result = dataframe.copy()

    before_rows = len(result)
    before_missing = int(
        result.isna()
        .sum()
        .sum()
    )

    filled_columns = []

    if strategy == "keep":
        pass

    elif strategy == "drop_rows":
        result = result.dropna()

    elif strategy in {
        "mean",
        "median",
        "mode",
    }:
        for column in result.columns:
            series = result[column]

            if not series.isna().any():
                continue

            fill_value = None

            if (
                strategy
                in {
                    "mean",
                    "median",
                }
                and pd.api.types
                    .is_numeric_dtype(
                        series
                    )
            ):
                if series.dropna().empty:
                    continue

                if strategy == "mean":
                    fill_value = (
                        series.mean()
                    )
                else:
                    fill_value = (
                        series.median()
                    )

            else:
                modes = series.mode(
                    dropna=True
                )

                if modes.empty:
                    continue

                fill_value = (
                    modes.iloc[0]
                )

            result[column] = (
                series.fillna(
                    fill_value
                )
            )

            filled_columns.append(
                str(column)
            )

    else:
        raise ValueError(
            "Unsupported missing-value strategy."
        )

    return result, {
        "strategy": strategy,
        "missing_before": before_missing,
        "missing_after": int(
            result.isna()
            .sum()
            .sum()
        ),
        "rows_before": before_rows,
        "rows_after": len(result),
        "rows_removed": (
            before_rows
            - len(result)
        ),
        "filled_columns": (
            filled_columns
        ),
    }


def process_iqr_outliers(
    dataframe: pd.DataFrame,
    action: str,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    result = dataframe.copy()

    details = {}
    combined_mask = pd.Series(
        False,
        index=result.index,
    )

    numeric_columns = (
        result.select_dtypes(
            include=np.number
        ).columns
    )

    for column in numeric_columns:
        series = pd.to_numeric(
            result[column],
            errors="coerce",
        )

        valid = series.dropna()

        if len(valid) < 4:
            details[
                str(column)
            ] = {
                "outlier_count": 0,
                "lower_bound": None,
                "upper_bound": None,
                "reason": (
                    "Too few valid values "
                    "for stable IQR detection."
                ),
            }

            continue

        q1 = valid.quantile(
            0.25
        )
        q3 = valid.quantile(
            0.75
        )
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        mask = (
            (series < lower)
            | (series > upper)
        ).fillna(False)

        outlier_count = int(
            mask.sum()
        )

        details[
            str(column)
        ] = {
            "outlier_count":
                outlier_count,
            "lower_bound":
                float(lower),
            "upper_bound":
                float(upper),
        }

        if action == "clip_iqr":
            result[column] = (
                series.clip(
                    lower=lower,
                    upper=upper,
                )
            )

        elif action == "remove_iqr":
            combined_mask = (
                combined_mask
                | mask
            )

    rows_before = len(result)

    if action == "remove_iqr":
        result = result.loc[
            ~combined_mask
        ].copy()

    elif action not in {
        "keep",
        "clip_iqr",
    }:
        raise ValueError(
            "Unsupported outlier action."
        )

    return result, {
        "action": action,
        "rows_before": rows_before,
        "rows_after": len(result),
        "rows_removed": (
            rows_before
            - len(result)
        ),
        "total_flagged": int(
            sum(
                item.get(
                    "outlier_count",
                    0,
                )
                for item
                in details.values()
            )
        ),
        "columns": details,
    }


# ============================================================
# PUT: overwrite an existing dataset with spreadsheet edits
# ============================================================

@router.put(
    "/{dataset_id}/data"
)
def update_dataset_data(
    dataset_id: str,
    request: DatasetDataUpdate,
    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    dataset = get_owned_dataset(
        dataset_id,
        user_id,
    )

    dataframe = make_dataframe(
        request
    )

    if not len(dataframe.columns):
        raise HTTPException(
            status_code=400,
            detail=(
                "The spreadsheet must "
                "contain at least one column."
            ),
        )

    (
        file_path,
        filename,
        file_type,
    ) = write_dataframe_to_existing_dataset(
        dataframe,
        dataset,
    )

    columns = [
        str(column)
        for column in dataframe.columns
    ]

    current_metadata = (
        dataset.get(
            "variable_metadata",
            []
        )
    )

    filtered_metadata = [
        item
        for item in current_metadata
        if item.get("name")
        in columns
    ]

    updated_at = datetime.now(
        timezone.utc
    )

    datasets_collection.update_one(
        {
            "_id": dataset["_id"],
            "user_id": user_id,
        },
        {
            "$set": {
                "filename": filename,
                "file_type": file_type,
                "file_size": (
                    file_path.stat()
                    .st_size
                ),
                "row_count": len(
                    dataframe
                ),
                "column_count": len(
                    columns
                ),
                "columns": columns,
                "variable_metadata": (
                    filtered_metadata
                ),
                "updated_at": updated_at,
            }
        },
    )

    return {
        "message": (
            "Spreadsheet changes "
            "saved successfully."
        ),
        "dataset_id": dataset_id,
        "filename": filename,
        "file_type": file_type,
        "row_count": len(
            dataframe
        ),
        "column_count": len(
            columns
        ),
        "columns": columns,
        "updated_at": (
            updated_at.isoformat()
        ),
    }


# ============================================================
# POST: one guided preparation pass
# ============================================================

@router.post(
    "/{dataset_id}/prepare/workflow"
)
def prepare_dataset_workflow(
    dataset_id: str,
    request: WorkflowPreparationRequest,
    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    dataframe, dataset = (
        read_owned_dataset(
            dataset_id,
            user_id,
        )
    )

    result = dataframe.copy()

    rows_original = len(result)
    missing_original = int(
        result.isna()
        .sum()
        .sum()
    )

    details: dict[
        str,
        Any,
    ] = {
        "rows_original":
            rows_original,
        "columns_original":
            len(result.columns),
        "missing_original":
            missing_original,
    }

    # --------------------------------------------------------
    # Blank strings
    # --------------------------------------------------------

    if request.normalize_blank_strings:
        before_missing = int(
            result.isna()
            .sum()
            .sum()
        )

        result = result.replace(
            r"^\s*$",
            np.nan,
            regex=True,
        )

        after_missing = int(
            result.isna()
            .sum()
            .sum()
        )

        details[
            "blank_strings_normalized"
        ] = max(
            after_missing
            - before_missing,
            0,
        )

    else:
        details[
            "blank_strings_normalized"
        ] = 0

    # --------------------------------------------------------
    # Trim text
    # --------------------------------------------------------

    if request.trim_text:
        (
            result,
            trimmed_columns,
        ) = trim_text_columns(
            result
        )
    else:
        trimmed_columns = []

    details[
        "trimmed_text_columns"
    ] = trimmed_columns

    # --------------------------------------------------------
    # Numeric-like text correction
    # --------------------------------------------------------

    if request.coerce_numeric_strings:
        (
            result,
            converted_columns,
        ) = coerce_mostly_numeric_text(
            result
        )
    else:
        converted_columns = []

    details[
        "numeric_columns_corrected"
    ] = converted_columns

    # --------------------------------------------------------
    # Empty rows
    # --------------------------------------------------------

    before_empty_cleanup = len(
        result
    )

    result = result.dropna(
        how="all"
    ).reset_index(
        drop=True
    )

    details[
        "empty_rows_removed"
    ] = (
        before_empty_cleanup
        - len(result)
    )

    # --------------------------------------------------------
    # Duplicates
    # --------------------------------------------------------

    duplicate_count = int(
        result.duplicated()
        .sum()
    )

    details[
        "duplicates_detected"
    ] = duplicate_count

    if request.remove_duplicates:
        result = result.drop_duplicates(
            keep="first"
        ).reset_index(
            drop=True
        )

        details[
            "duplicates_removed"
        ] = duplicate_count
    else:
        details[
            "duplicates_removed"
        ] = 0

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    try:
        (
            result,
            missing_details,
        ) = fill_missing_values(
            result,
            request.missing_strategy,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    details[
        "missing_values"
    ] = missing_details

    # --------------------------------------------------------
    # Outliers
    # --------------------------------------------------------

    try:
        (
            result,
            outlier_details,
        ) = process_iqr_outliers(
            result,
            request.outlier_action,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    details[
        "outliers"
    ] = outlier_details

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    result = result.reset_index(
        drop=True
    )

    if result.empty:
        raise HTTPException(
            status_code=400,
            detail=(
                "The selected preparation "
                "options removed every row. "
                "Change the preparation "
                "options and try again."
            ),
        )

    details[
        "rows_final"
    ] = len(result)

    details[
        "columns_final"
    ] = len(result.columns)

    details[
        "missing_final"
    ] = int(
        result.isna()
        .sum()
        .sum()
    )

    details[
        "configuration"
    ] = request.model_dump()

    # --------------------------------------------------------
    # Save as a derived dataset to preserve raw data
    # --------------------------------------------------------

    try:
        derived = save_derived_dataset(
            result,
            dataset,
            user_id,
            "workflow",
            details,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "The dataset was prepared, "
                "but SSAS could not save the "
                f"prepared copy: {exc}"
            ),
        )

    return {
        "message": (
            "Data preparation completed. "
            "The original dataset was "
            "preserved and a prepared copy "
            "was created."
        ),
        "source_dataset_id": dataset_id,
        "summary": details,
        "derived_dataset": derived,
    }
