import os
import uuid
from pathlib import Path

import pandas as pd

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
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
from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"],
)


ALLOWED_EXTENSIONS = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "xls",
}


def dataset_to_response(dataset) -> DatasetResponse:
    return DatasetResponse(
        id=str(dataset["_id"]),
        user_id=dataset["user_id"],
        filename=dataset["filename"],
        original_filename=dataset["original_filename"],
        file_type=dataset["file_type"],
        file_size=dataset["file_size"],
        row_count=dataset["row_count"],
        column_count=dataset["column_count"],
        columns=dataset.get("columns", []),
        status=dataset["status"],
        created_at=dataset["created_at"],
        updated_at=dataset["updated_at"],
    )


@router.post(
    "/upload",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """
    Upload a CSV or Excel dataset.
    """

    original_filename = file.filename or ""

    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file type. "
                "Only CSV and Excel files are allowed."
            ),
        )

    # Read file into memory
    contents = await file.read()

    file_size = len(contents)

    max_size = settings.max_upload_size_mb * 1024 * 1024

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File is too large. Maximum allowed size is "
                f"{settings.max_upload_size_mb} MB."
            ),
        )

    # Generate unique filename
    unique_filename = (
        f"{uuid.uuid4().hex}{extension}"
    )

    upload_directory = Path(
        settings.upload_directory
    )

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = upload_directory / unique_filename

    try:
        # Save uploaded file
        with open(file_path, "wb") as destination:
            destination.write(contents)

        # Analyze dataset
        if extension == ".csv":
            dataframe = pd.read_csv(file_path)

        elif extension in {".xlsx", ".xls"}:
            dataframe = pd.read_excel(file_path)

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type.",
            )

        row_count = len(dataframe)
        column_count = len(dataframe.columns)

        columns = [
            str(column)
            for column in dataframe.columns
        ]

        # Create MongoDB document
        document = create_dataset_document(
            user_id=current_user["user_id"],
            filename=unique_filename,
            original_filename=original_filename,
            file_type=ALLOWED_EXTENSIONS[extension],
            file_size=file_size,
            row_count=row_count,
            column_count=column_count,
            columns=columns,
        )

        result = datasets_collection.insert_one(document)

        document["_id"] = result.inserted_id

        return dataset_to_response(document)

    except HTTPException:
        # Remove file if FastAPI error occurs
        if file_path.exists():
            file_path.unlink()

        raise

    except Exception as exc:
        # Remove file if processing fails
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to process dataset: {str(exc)}",
        )


@router.get(
    "",
    response_model=DatasetListResponse,
)
def get_my_datasets(
    current_user=Depends(get_current_user),
):
    """
    Get all datasets belonging to the authenticated user.
    """

    datasets = datasets_collection.find(
        {
            "user_id": current_user["user_id"]
        }
    ).sort(
        "created_at",
        -1,
    )

    dataset_list = [
        dataset_to_response(dataset)
        for dataset in datasets
    ]

    return DatasetListResponse(
        datasets=dataset_list,
        total=len(dataset_list),
    )


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
)
def get_dataset(
    dataset_id: str,
    current_user=Depends(get_current_user),
):
    """
    Get details of one dataset.
    """

    from bson import ObjectId

    try:
        object_id = ObjectId(dataset_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one(
        {
            "_id": object_id,
            "user_id": current_user["user_id"],
        }
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return dataset_to_response(dataset)


@router.delete(
    "/{dataset_id}",
)
def delete_dataset(
    dataset_id: str,
    current_user=Depends(get_current_user),
):
    """
    Delete a dataset owned by the authenticated user.
    """

    from bson import ObjectId

    try:
        object_id = ObjectId(dataset_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one(
        {
            "_id": object_id,
            "user_id": current_user["user_id"],
        }
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    # Delete physical file
    file_path = (
        Path(settings.upload_directory)
        / dataset["filename"]
    )

    if file_path.exists():
        file_path.unlink()

    # Delete MongoDB metadata
    datasets_collection.delete_one(
        {
            "_id": object_id,
            "user_id": current_user["user_id"],
        }
    )

    return {
        "message": "Dataset deleted successfully.",
        "dataset_id": dataset_id,
    }
