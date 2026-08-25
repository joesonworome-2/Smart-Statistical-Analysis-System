from pathlib import Path

import pandas as pd
from bson import ObjectId
from fastapi import HTTPException

from app.config import settings
from app.database import datasets_collection


def get_dataset(dataset_id: str, user_id: str):
    try:
        dataset_object_id = ObjectId(dataset_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one(
        {"_id": dataset_object_id}
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    owner_id = dataset.get("user_id") or dataset.get("owner_id")

    if owner_id and str(owner_id) != str(user_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this dataset.",
        )

    return dataset


def read_dataset(dataset_id: str, user_id: str):
    dataset = get_dataset(dataset_id, user_id)

    filename = dataset.get("filename")

    if not filename:
        raise HTTPException(
            status_code=500,
            detail="Dataset filename is missing.",
        )

    file_path = Path(settings.dataset_storage_path) / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset file not found: {filename}",
        )

    extension = file_path.suffix.lower()

    try:
        if extension == ".csv":
            dataframe = pd.read_csv(file_path)

        elif extension in {".xlsx", ".xls"}:
            dataframe = pd.read_excel(file_path)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported dataset type: {extension}",
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read dataset: {exc}",
        )

    return dataframe, dataset
