from pathlib import Path

import pandas as pd
from bson import ObjectId
from fastapi import HTTPException

from app.config import settings
from app.database import datasets_collection


def get_dataset(dataset_id: str, user_id: str):
    try:
        object_id = ObjectId(dataset_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one({"_id": object_id})

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    owner = dataset.get("user_id") or dataset.get("owner_id")

    if owner and str(owner) != str(user_id):
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

    path = Path(settings.dataset_storage_path) / filename

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset file not found: {filename}",
        )

    suffix = path.suffix.lower()

    try:
        if suffix == ".csv":
            dataframe = pd.read_csv(path)

        elif suffix in {".xlsx", ".xls"}:
            dataframe = pd.read_excel(path)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported dataset type: {suffix}",
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read dataset: {exc}",
        )

    return dataframe, dataset
