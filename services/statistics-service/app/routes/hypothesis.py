import httpx
import pandas as pd

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
)

from app.schemas.hypothesis import (
    HypothesisRequest,
)

from app.services.hypothesis_engine import (
    run_hypothesis_test,
)


router = APIRouter(
    prefix="/statistics/hypothesis",
    tags=["Hypothesis Tests"],
)


DATASET_SERVICE_URL = (
    "http://dataset-service:8003"
)


async def load_dataset_dataframe(
    dataset_id: str,
    authorization: str,
):
    all_rows = []

    columns = []

    offset = 0
    limit = 5000

    has_more = True

    async with httpx.AsyncClient(
        timeout=60.0
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
                    "Authorization": (
                        authorization
                    )
                },
            )

            if response.status_code != 200:
                try:
                    detail = (
                        response.json()
                        .get(
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

            rows = payload.get(
                "rows",
                [],
            )

            all_rows.extend(
                rows
            )

            returned = payload.get(
                "returned_rows",
                len(rows),
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

    return pd.DataFrame(
        all_rows,
        columns=columns or None,
    )


@router.post(
    "/{dataset_id}",
)
async def calculate_hypothesis(
    dataset_id: str,
    request: HypothesisRequest,
    authorization: str = Header(...),
):
    dataframe = (
        await load_dataset_dataframe(
            dataset_id,
            authorization,
        )
    )

    required_columns = (
        request.metric_variables
        +
        request.categorical_variables
    )

    missing = [
        column
        for column
        in required_columns
        if column
        not in dataframe.columns
    ]

    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                "Dataset does not contain: "
                + ", ".join(missing)
            ),
        )

    try:
        result = run_hypothesis_test(
            df=dataframe,
            family=request.family,
            metric_variables=(
                request.metric_variables
            ),
            categorical_variables=(
                request
                .categorical_variables
            ),
            test_value=(
                request.test_value
            ),
            alternative=(
                request.alternative
            ),
            alpha=request.alpha,
        )

        return {
            "dataset_id": dataset_id,
            **result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Hypothesis test failed: "
                f"{str(exc)}"
            ),
        )
