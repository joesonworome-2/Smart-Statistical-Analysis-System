import httpx
import pandas as pd

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
)

from app.schemas.correlation_analysis import (
    CorrelationAnalysisRequest,
)

from app.services.correlation_engine import (
    json_safe,
    run_correlation_analysis,
)

from app.services.correlation_explanation import (
    build_correlation_explanation,
)


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/statistics/correlation-analysis",
    tags=["Correlation Analysis"],
)


# ==========================================================
# DATASET SERVICE
# ==========================================================

DATASET_SERVICE_URL = (
    "http://dataset-service:8003"
)


# ==========================================================
# LOAD COMPLETE DATASET
# ==========================================================

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


            # ----------------------------------------------
            # DATASET SERVICE ERROR
            # ----------------------------------------------

            if response.status_code != 200:

                try:
                    response_data = (
                        response.json()
                    )

                    detail = (
                        response_data.get(
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


            # ----------------------------------------------
            # READ DATA
            # ----------------------------------------------

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


            rows = (
                payload.get(
                    "rows",
                    [],
                )
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


            # ----------------------------------------------
            # SAFETY BREAK
            # ----------------------------------------------

            if returned == 0:
                break


            offset += returned


    # ======================================================
    # EMPTY DATASET
    # ======================================================

    if not all_rows:
        raise HTTPException(
            status_code=400,
            detail=(
                "The dataset contains no rows."
            ),
        )


    # ======================================================
    # CREATE DATAFRAME
    # ======================================================

    try:
        dataframe = pd.DataFrame(
            all_rows,
            columns=(
                columns or None
            ),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to convert dataset "
                "into a statistical dataframe: "
                f"{str(exc)}"
            ),
        )


    return dataframe


# ==========================================================
# CORRELATION ANALYSIS
# ==========================================================

@router.post(
    "/{dataset_id}",
)
async def calculate_correlation(
    dataset_id: str,
    request: CorrelationAnalysisRequest,
    authorization: str = Header(...),
):
    """
    Perform correlation analysis.

    Supported methods:

    - Auto recommendation
    - Pearson correlation
    - Spearman correlation
    - Kendall correlation

    The result contains:

    - selected method
    - recommendation
    - correlation matrix
    - significance table
    - diagnostics
    - short interpretation
    - detailed explanation
    - APA-style result
    """

    # ======================================================
    # LOAD DATASET
    # ======================================================

    dataframe = (
        await load_dataset_dataframe(
            dataset_id=dataset_id,
            authorization=authorization,
        )
    )


    # ======================================================
    # VERIFY VARIABLES
    # ======================================================

    missing = [
        variable
        for variable in request.variables
        if variable
        not in dataframe.columns
    ]


    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                "Dataset does not contain: "
                +
                ", ".join(
                    missing
                )
            ),
        )


    # ======================================================
    # REQUIRE AT LEAST TWO VARIABLES
    # ======================================================

    if len(
        request.variables
    ) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                "Select at least two "
                "variables for correlation."
            ),
        )


    # ======================================================
    # CALCULATE
    # ======================================================

    try:

        result = (
            run_correlation_analysis(
                dataframe=dataframe,

                variables=(
                    request.variables
                ),

                requested_method=(
                    request.method
                ),

                alpha=(
                    request.alpha
                ),

                confidence_level=(
                    request
                    .confidence_level
                ),
            )
        )


        # ==================================================
        # DETAILED EXPLANATION
        # ==================================================

        detailed_explanation = (
            build_correlation_explanation(
                result
            )
        )


        result[
            "detailed_explanation"
        ] = (
            detailed_explanation
        )


        # ==================================================
        # COMPLETE RESPONSE
        # ==================================================

        response_data = {
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
        }


        # ==================================================
        # CONVERT NUMPY TYPES
        # ==================================================

        return json_safe(
            response_data
        )


    # ======================================================
    # STATISTICAL / INPUT ERROR
    # ======================================================

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


    # ======================================================
    # EXISTING FASTAPI ERROR
    # ======================================================

    except HTTPException:
        raise


    # ======================================================
    # UNEXPECTED ERROR
    # ======================================================

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Correlation analysis failed: "
                f"{str(exc)}"
            ),
        )
