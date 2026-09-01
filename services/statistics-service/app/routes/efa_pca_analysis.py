import httpx
import pandas as pd

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
)

from app.schemas.efa_pca_analysis import (
    EfaPcaAnalysisRequest,
)

from app.services.efa_pca_engine import (
    json_safe,
    run_efa_pca,
)

from app.services.efa_pca_explanation import (
    build_efa_pca_explanation,
)


router = APIRouter(
    prefix="/statistics/efa-pca-analysis",
    tags=[
        "EFA PCA"
    ],
)


DATASET_SERVICE_URL = (
    "http://dataset-service:8003"
)


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


@router.post(
    "/{dataset_id}",
)
async def efa_pca_analysis(
    dataset_id: str,

    request:
        EfaPcaAnalysisRequest,

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


        result = run_efa_pca(
            dataframe=(
                dataframe
            ),

            variables=(
                request
                .variables
            ),

            method=(
                request
                .method
            ),

            n_factors=(
                request
                .n_factors
            ),

            rotation=(
                request
                .rotation
            ),

            alpha=(
                request
                .alpha
            ),

            loading_threshold=(
                request
                .loading_threshold
            ),
        )


        result[
            "dataset_id"
        ] = dataset_id


        result[
            "detailed_explanation"
        ] = (
            build_efa_pca_explanation(
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
                "EFA/PCA analysis failed: "
                f"{str(exc)}"
            ),
        )
