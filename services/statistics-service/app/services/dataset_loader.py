import httpx
import pandas as pd

from fastapi import HTTPException


DATASET_SERVICE_URL = (
    "http://dataset-service:8003"
)


async def load_dataset_dataframe(
    dataset_id: str,
    authorization: str,
) -> tuple[pd.DataFrame, dict]:
    """
    Load all rows belonging to the authenticated
    user's dataset from Dataset Service.

    Returns:
        dataframe
        dataset metadata
    """

    all_rows = []

    columns = []

    offset = 0

    limit = 5000

    has_more = True

    dataset_name = None

    total_rows = None


    async with httpx.AsyncClient(
        timeout=90.0,
    ) as client:

        while has_more:

            response = await client.get(
                (
                    f"{DATASET_SERVICE_URL}"
                    f"/datasets/"
                    f"{dataset_id}/data"
                ),
                params={
                    "offset": offset,
                    "limit": limit,
                },
                headers={
                    "Authorization":
                        authorization,
                },
            )


            if response.status_code != 200:

                try:
                    payload = (
                        response.json()
                    )

                    detail = (
                        payload.get(
                            "detail",
                            "Unable to load dataset.",
                        )
                    )

                except Exception:

                    detail = (
                        "Unable to load dataset."
                    )


                raise HTTPException(
                    status_code=(
                        response.status_code
                    ),
                    detail=detail,
                )


            payload = response.json()


            if not columns:
                columns = (
                    payload.get(
                        "columns",
                        [],
                    )
                )


            if not dataset_name:
                dataset_name = (
                    payload.get(
                        "dataset"
                    )
                )


            if total_rows is None:
                total_rows = (
                    payload.get(
                        "total"
                    )
                )


            rows = payload.get(
                "rows",
                [],
            )


            all_rows.extend(
                rows
            )


            returned = (
                payload.get(
                    "returned_rows",
                    len(rows),
                )
            )


            has_more = bool(
                payload.get(
                    "has_more",
                    False,
                )
            )


            if returned == 0:
                break


            offset += returned


    if not all_rows:
        raise HTTPException(
            status_code=400,
            detail=(
                "The dataset contains no rows."
            ),
        )


    dataframe = pd.DataFrame(
        all_rows,
        columns=(
            columns or None
        ),
    )


    metadata = {
        "dataset_id":
            dataset_id,

        "dataset":
            dataset_name,

        "row_count":
            total_rows
            if total_rows is not None
            else len(dataframe),

        "column_count":
            len(dataframe.columns),

        "columns":
            list(
                dataframe.columns
            ),
    }


    return (
        dataframe,
        metadata,
    )
