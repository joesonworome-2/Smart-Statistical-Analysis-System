from pathlib import Path

import pandas as pd

from app.config import settings


def load_dataset(
    filename: str,
) -> pd.DataFrame:

    file_path = (
        Path(settings.upload_directory)
        / filename
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file '{filename}' "
            "could not be found."
        )

    extension = (
        file_path.suffix.lower()
    )

    if extension == ".csv":

        dataframe = pd.read_csv(
            file_path
        )

    elif extension in [
        ".xlsx",
        ".xls",
    ]:

        dataframe = pd.read_excel(
            file_path
        )

    else:

        raise ValueError(
            "Unsupported dataset format. "
            "Only CSV and Excel files "
            "are currently supported."
        )

    return dataframe
