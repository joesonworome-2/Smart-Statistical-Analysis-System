import uuid
from pathlib import Path

import pandas as pd

from bson import ObjectId

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.config import settings
from app.database import datasets_collection
from app.models.dataset import create_dataset_document

from app.schemas.dataset import (
    DatasetListResponse,
    DatasetResponse,
)

from app.security.dependencies import (
    get_current_user,
)


router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"],
)


ALLOWED_EXTENSIONS = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "xls",
}


# ============================================================
# Helpers
# ============================================================

def dataset_to_response(
    dataset,
) -> DatasetResponse:
    """
    Convert a MongoDB dataset document
    into the API response schema.
    """

    return DatasetResponse(
        id=str(dataset["_id"]),

        user_id=dataset["user_id"],

        filename=dataset["filename"],

        original_filename=dataset[
            "original_filename"
        ],

        file_type=dataset["file_type"],

        file_size=dataset["file_size"],

        row_count=dataset["row_count"],

        column_count=dataset[
            "column_count"
        ],

        columns=dataset.get(
            "columns",
            [],
        ),

        status=dataset["status"],

        is_derived=dataset.get(
            "is_derived",
            False,
        ),

        source_dataset_id=dataset.get(
            "source_dataset_id"
        ),

        preparation_steps=dataset.get(
            "preparation_steps",
            [],
        ),

        created_at=dataset[
            "created_at"
        ],

        updated_at=dataset[
            "updated_at"
        ],
    )


def get_owned_dataset(
    dataset_id: str,
    user_id: str,
):
    """
    Return a dataset only when it belongs
    to the authenticated user.
    """

    try:
        object_id = ObjectId(
            dataset_id
        )

    except Exception:
        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Invalid dataset ID.",
        )

    dataset = (
        datasets_collection
        .find_one(
            {
                "_id": object_id,
                "user_id": user_id,
            }
        )
    )

    if not dataset:
        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Dataset not found.",
        )

    return dataset


def dataset_file_path(
    dataset,
):
    """
    Return the physical storage path
    of a dataset.
    """

    return (
        Path(
            settings.upload_directory
        )
        / dataset["filename"]
    )


def read_dataset_file(
    dataset,
):
    """
    Read a stored CSV or Excel dataset
    into a Pandas DataFrame.
    """

    file_path = dataset_file_path(
        dataset
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Dataset file not found.",
        )

    extension = (
        file_path
        .suffix
        .lower()
    )

    try:

        if extension == ".csv":
            dataframe = pd.read_csv(
                file_path
            )

        elif extension in {
            ".xlsx",
            ".xls",
        }:
            dataframe = pd.read_excel(
                file_path
            )

        else:
            raise HTTPException(
                status_code=
                    status
                    .HTTP_400_BAD_REQUEST,

                detail=
                    (
                        "Unsupported "
                        "dataset format."
                    ),
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=
                status
                .HTTP_400_BAD_REQUEST,

            detail=(
                "Unable to read "
                "dataset: "
                f"{str(exc)}"
            ),
        )

    return dataframe


def json_safe_value(
    value,
):
    """
    Convert Pandas/NumPy values into
    values that FastAPI can safely
    serialize as JSON.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.isoformat()

    # Convert NumPy scalar values
    # such as int64/float64.
    if hasattr(
        value,
        "item",
    ):
        try:
            return value.item()
        except Exception:
            pass

    # Python datetime/date objects
    if hasattr(
        value,
        "isoformat",
    ):
        try:
            return value.isoformat()
        except Exception:
            pass

    return value


def dataframe_rows_to_json(
    dataframe,
):
    """
    Convert DataFrame rows into
    JSON-safe dictionaries.
    """

    rows = []

    for _, row in dataframe.iterrows():

        record = {}

        for column in dataframe.columns:

            record[
                str(column)
            ] = json_safe_value(
                row[column]
            )

        rows.append(record)

    return rows


# ============================================================
# Upload Dataset
# ============================================================

@router.post(
    "/upload",
    response_model=DatasetResponse,
    status_code=
        status.HTTP_201_CREATED,
)
async def upload_dataset(
    file: UploadFile = File(...),

    current_user=Depends(
        get_current_user
    ),
):
    """
    Upload a CSV or Excel dataset.
    """

    original_filename = (
        file.filename or ""
    )

    extension = (
        Path(
            original_filename
        )
        .suffix
        .lower()
    )

    if (
        extension
        not in ALLOWED_EXTENSIONS
    ):
        raise HTTPException(
            status_code=
                status
                .HTTP_400_BAD_REQUEST,

            detail=(
                "Unsupported file type. "
                "Only CSV and Excel "
                "files are allowed."
            ),
        )

    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    contents = await file.read()

    file_size = len(
        contents
    )

    max_size = (
        settings.max_upload_size_mb
        * 1024
        * 1024
    )

    if file_size > max_size:
        raise HTTPException(
            status_code=
                status
                .HTTP_413_REQUEST_ENTITY_TOO_LARGE,

            detail=(
                "File is too large. "
                "Maximum allowed size is "
                f"{settings.max_upload_size_mb} MB."
            ),
        )

    # --------------------------------------------------------
    # Generate safe unique filename
    # --------------------------------------------------------

    unique_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    upload_directory = Path(
        settings.upload_directory
    )

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = (
        upload_directory
        / unique_filename
    )

    try:

        # ----------------------------------------------------
        # Save physical file
        # ----------------------------------------------------

        with open(
            file_path,
            "wb",
        ) as destination:

            destination.write(
                contents
            )

        # ----------------------------------------------------
        # Read and inspect dataset
        # ----------------------------------------------------

        if extension == ".csv":

            dataframe = pd.read_csv(
                file_path
            )

        elif extension in {
            ".xlsx",
            ".xls",
        }:

            dataframe = pd.read_excel(
                file_path
            )

        else:
            raise HTTPException(
                status_code=400,

                detail=
                    "Unsupported file type.",
            )

        row_count = len(
            dataframe
        )

        column_count = len(
            dataframe.columns
        )

        columns = [
            str(column)
            for column
            in dataframe.columns
        ]

        # ----------------------------------------------------
        # Create MongoDB metadata
        # ----------------------------------------------------

        document = (
            create_dataset_document(
                user_id=
                    current_user[
                        "user_id"
                    ],

                filename=
                    unique_filename,

                original_filename=
                    original_filename,

                file_type=
                    ALLOWED_EXTENSIONS[
                        extension
                    ],

                file_size=
                    file_size,

                row_count=
                    row_count,

                column_count=
                    column_count,

                columns=
                    columns,
            )
        )

        result = (
            datasets_collection
            .insert_one(
                document
            )
        )

        document["_id"] = (
            result.inserted_id
        )

        return dataset_to_response(
            document
        )

    except HTTPException:

        if file_path.exists():
            file_path.unlink()

        raise

    except Exception as exc:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=
                status
                .HTTP_400_BAD_REQUEST,

            detail=(
                "Unable to process "
                "dataset: "
                f"{str(exc)}"
            ),
        )


# ============================================================
# List User Datasets
# ============================================================

@router.get(
    "",
    response_model=
        DatasetListResponse,
)
def get_my_datasets(
    current_user=Depends(
        get_current_user
    ),
):
    """
    Return all datasets belonging
    to the authenticated user.
    """

    datasets = (
        datasets_collection
        .find(
            {
                "user_id":
                    current_user[
                        "user_id"
                    ]
            }
        )
        .sort(
            "created_at",
            -1,
        )
    )

    dataset_list = [
        dataset_to_response(
            dataset
        )
        for dataset in datasets
    ]

    return DatasetListResponse(
        datasets=
            dataset_list,

        total=
            len(dataset_list),
    )


# ============================================================
# Dataset Spreadsheet Data
# ============================================================

@router.get(
    "/{dataset_id}/data"
)
def get_dataset_data(
    dataset_id: str,

    offset: int = Query(
        default=0,
        ge=0,
    ),

    limit: int = Query(
        default=200,
        ge=1,
        le=5000,
    ),

    current_user=Depends(
        get_current_user
    ),
):
    """
    Return dataset rows for the
    SSAS spreadsheet-style workspace.

    This endpoint is used for:

    - Viewing uploaded datasets
    - Spreadsheet-style data display
    - Measurement-level selection
    - Descriptive analysis workspace
    - Copy/paste style workflows
    """

    dataset = get_owned_dataset(
        dataset_id,
        current_user["user_id"],
    )

    dataframe = read_dataset_file(
        dataset
    )

    total_rows = len(
        dataframe
    )

    end = (
        offset
        + limit
    )

    page = (
        dataframe
        .iloc[
            offset:end
        ]
        .copy()
    )

    rows = (
        dataframe_rows_to_json(
            page
        )
    )

    return {
        "dataset_id":
            dataset_id,

        "dataset":
            dataset.get(
                "original_filename"
            ),

        "columns": [
            str(column)
            for column
            in dataframe.columns
        ],

        "rows":
            rows,

        "offset":
            offset,

        "limit":
            limit,

        "returned_rows":
            len(rows),

        "total":
            total_rows,

        "has_more":
            end < total_rows,
    }


# ============================================================
# Get One Dataset
# ============================================================

@router.get(
    "/{dataset_id}",
    response_model=
        DatasetResponse,
)
def get_dataset(
    dataset_id: str,

    current_user=Depends(
        get_current_user
    ),
):
    """
    Get metadata for one dataset.
    """

    dataset = get_owned_dataset(
        dataset_id,
        current_user["user_id"],
    )

    return dataset_to_response(
        dataset
    )


# ============================================================
# Delete Dataset
# ============================================================

@router.delete(
    "/{dataset_id}",
)
def delete_dataset(
    dataset_id: str,

    current_user=Depends(
        get_current_user
    ),
):
    """
    Delete a dataset owned by the
    authenticated user.
    """

    dataset = get_owned_dataset(
        dataset_id,
        current_user["user_id"],
    )

    # --------------------------------------------------------
    # Delete physical dataset file
    # --------------------------------------------------------

    file_path = dataset_file_path(
        dataset
    )

    if file_path.exists():
        file_path.unlink()

    # --------------------------------------------------------
    # Delete MongoDB metadata
    # --------------------------------------------------------

    datasets_collection.delete_one(
        {
            "_id":
                dataset["_id"],

            "user_id":
                current_user[
                    "user_id"
                ],
        }
    )

    return {
        "message":
            "Dataset deleted successfully.",

        "dataset_id":
            dataset_id,
    }
