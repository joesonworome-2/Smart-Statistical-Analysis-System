import httpx
import pandas as pd

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
)

from app.schemas.reliability_analysis import (
    ReliabilityAnalysisRequest,
)

from app.services.reliability_engine import (
    json_safe,
    run_reliability_analysis,
)

from app.services.reliability_explanation import (
    build_reliability_explanation,
)


router = APIRouter(
    prefix="/statistics/reliability-analysis",
    tags=[
        "Reliability Analysis"
    ],
)


DATASET_SERVICE_URL = (
    "http://dataset-service:8003"
)


# ==========================================================
# LOAD DATASET
# ==========================================================

async def load_dataset(
    dataset_id,
    authorization,
):
    rows = []

    offset = 0

    limit = 5000


    async with httpx.AsyncClient(
        timeout=120.0,
    ) as client:

        while True:

            response = await client.get(
                (
                    f"{DATASET_SERVICE_URL}"
                    f"/datasets/"
                    f"{dataset_id}/data"
                ),
                params={
                    "offset":
                        offset,

                    "limit":
                        limit,
                },
                headers={
                    "Authorization":
                        authorization,
                },
            )


            if (
                response.status_code
                !=
                200
            ):

                try:

                    detail = (
                        response
                        .json()
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


            payload = (
                response.json()
            )


            page_rows = (
                payload.get(
                    "rows",
                    [],
                )
            )


            rows.extend(
                page_rows
            )


            returned = int(
                payload.get(
                    "returned_rows",
                    len(
                        page_rows
                    ),
                )
            )


            has_more = bool(
                payload.get(
                    "has_more",
                    False,
                )
            )


            if (
                returned == 0
                or
                not has_more
            ):
                break


            offset += (
                returned
            )


    if not rows:

        raise HTTPException(
            status_code=400,
            detail=(
                "The dataset contains no rows."
            ),
        )


    return rows


# ==========================================================
# RELIABILITY ANALYSIS
# ==========================================================

@router.post(
    "/{dataset_id}",
)
async def reliability_analysis(
    dataset_id: str,

    request:
        ReliabilityAnalysisRequest,

    authorization:
        str = Header(...),
):
    try:

        rows = await load_dataset(
            dataset_id=(
                dataset_id
            ),

            authorization=(
                authorization
            ),
        )


        dataframe = pd.DataFrame(
            rows
        )


        result = (
            run_reliability_analysis(
                dataframe=(
                    dataframe
                ),

                variables=(
                    request
                    .variables
                ),

                alpha=(
                    request
                    .alpha
                ),

                item_total_threshold=(
                    request
                    .item_total_threshold
                ),
            )
        )


        result[
            "dataset_id"
        ] = dataset_id


        result[
            "detailed_explanation"
        ] = (
            build_reliability_explanation(
                result
            )
        )


        return json_safe(
            result
        )


    except HTTPException:

        raise


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        )


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Reliability analysis failed: "
                f"{str(exc)}"
            ),
        )
