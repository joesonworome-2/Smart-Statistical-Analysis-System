import httpx
import pandas as pd

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
)

from app.schemas.ancova_analysis import (
    AncovaAnalysisRequest,
)

from app.services.ancova_engine import (
    json_safe,
    run_ancova,
)

from app.services.ancova_explanation import (
    build_ancova_explanation,
)


router = APIRouter(
    prefix="/statistics/ancova-analysis",
    tags=["ANCOVA"],
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


            if response.status_code != 200:

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
                    []
                )
            )


            rows.extend(
                page_rows
            )


            returned = (
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
# ANCOVA
# ==========================================================

@router.post(
    "/{dataset_id}",
)
async def ancova_analysis(
    dataset_id: str,

    request:
        AncovaAnalysisRequest,

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


        dataframe = (
            pd.DataFrame(
                rows
            )
        )


        result = run_ancova(
            dataframe=(
                dataframe
            ),

            dependent_variable=(
                request
                .dependent_variable
            ),

            factor_variable=(
                request
                .factor_variable
            ),

            covariates=(
                request
                .covariates
            ),

            alpha=(
                request
                .alpha
            ),

            confidence_level=(
                request
                .confidence_level
            ),
        )


        result[
            "dataset_id"
        ] = dataset_id


        result[
            "detailed_explanation"
        ] = (
            build_ancova_explanation(
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
                "ANCOVA analysis failed: "
                f"{str(exc)}"
            ),
        )
