from pathlib import Path

import pandas as pd

from app.config import settings


SUPPORTED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}


def find_dataset_file(filename: str) -> Path:
    storage_directory = Path(settings.upload_directory)

    file_path = storage_directory / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {filename}"
        )

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {file_path.suffix}"
        )

    return file_path


def load_dataset(filename: str) -> pd.DataFrame:
    file_path = find_dataset_file(filename)

    extension = file_path.suffix.lower()

    if extension == ".csv":
        return pd.read_csv(file_path)

    if extension in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)

    raise ValueError("Unsupported dataset format.")
