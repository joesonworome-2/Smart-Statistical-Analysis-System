import pandas as pd

from fastapi import (
    APIRouter,
    HTTPException,
)

from app.schemas.predictive import (
    PredictiveMLRequest,
)

from app.services.predictive_engine import (
    json_safe,
    run_predictive_ml,
)


router = APIRouter(
    prefix="/ml/predictive",
    tags=[
        "Predictive Analytics"
    ],
)


@router.post(
    "/regression"
)
def predictive_regression(
    request:
        PredictiveMLRequest,
):
    try:
        dataframe = (
            pd.DataFrame(
                request.rows
            )
        )


        result = (
            run_predictive_ml(
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

                test_size=(
                    request
                    .test_size
                ),

                random_seed=(
                    request
                    .random_seed
                ),

                cv_folds=(
                    request
                    .cv_folds
                ),

                future_values=(
                    request
                    .future_values
                ),

                time_variable=(
                    request
                    .time_variable
                ),
            )
        )


        return json_safe(
            result
        )


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
                "Predictive ML analysis failed: "
                f"{str(exc)}"
            ),
        )
