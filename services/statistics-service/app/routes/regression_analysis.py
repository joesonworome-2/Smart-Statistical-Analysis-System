import httpx
import pandas as pd

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
)

from app.schemas.regression_analysis import (
    RegressionAnalysisRequest,
)

from app.services.regression_engine import (
    json_safe,
    run_regression_analysis,
)

from app.services.regression_explanation import (
    build_regression_explanation,
)


router = APIRouter(
    prefix="/statistics/regression-analysis",
    tags=["Regression Analysis"],
)


DATASET_SERVICE_URL = (
    "http://dataset-service:8003"
)


# ==========================================================
# LOAD DATASET
# ==========================================================

async def load_dataset_dataframe(
    dataset_id: str,
    authorization: str,
):
    rows = []
    columns = []

    offset = 0
    limit = 5000
    has_more = True


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


            payload = (
                response.json()
            )


            if not columns:
                columns = (
                    payload.get(
                        "columns",
                        [],
                    )
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


            if returned == 0:
                break


            offset += returned


    if not rows:
        raise HTTPException(
            status_code=400,
            detail=(
                "The dataset contains no rows."
            ),
        )


    return pd.DataFrame(
        rows,
        columns=(
            columns or None
        ),
    )


# ==========================================================
# REGRESSION ENDPOINT
# ==========================================================

@router.post(
    "/{dataset_id}",
)
async def calculate_regression(
    dataset_id: str,
    request:
        RegressionAnalysisRequest,
    authorization:
        str = Header(...),
):
    dataframe = (
        await load_dataset_dataframe(
            dataset_id,
            authorization,
        )
    )


    try:
        result = (
            run_regression_analysis(
                dataframe=(
                    dataframe
                ),

                dependent_variable=(
                    request
                    .dependent_variable
                ),

                predictors=(
                    request
                    .predictors
                ),

                alpha=(
                    request.alpha
                ),

                confidence_level=(
                    request
                    .confidence_level
                ),

                include_intercept=(
                    request
                    .include_intercept
                ),
            )
        )


        result[
            "detailed_explanation"
        ] = (
            build_regression_explanation(
                result
            )
        )


        return json_safe({
            "dataset_id":
                dataset_id,

            "dataset_rows":
                int(
                    len(
                        dataframe
                    )
                ),

            "dataset_columns":
                int(
                    len(
                        dataframe.columns
                    )
                ),

            **result,
        })


    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        )


    except HTTPException:
        raise


    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Regression analysis failed: "
                f"{str(exc)}"
            ),
        )
