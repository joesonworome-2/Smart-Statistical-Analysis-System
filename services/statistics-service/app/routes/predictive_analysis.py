import httpx

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
)

from app.schemas.predictive_analysis import (
    PredictiveAnalysisRequest,
)


router = APIRouter(
    prefix="/statistics/predictive-analysis",
    tags=["Predictive Analytics"],
)


DATASET_SERVICE_URL = (
    "http://dataset-service:8003"
)

ML_SERVICE_URL = (
    "http://ml-service:8006"
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

    has_more = True


    async with httpx.AsyncClient(
        timeout=120.0,
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


    return rows


# ==========================================================
# SMART PREDICTIVE ANALYTICS
# ==========================================================

@router.post(
    "/{dataset_id}",
)
async def smart_predictive_analysis(
    dataset_id: str,
    request:
        PredictiveAnalysisRequest,
    authorization:
        str = Header(...),
):

    rows = await load_dataset(
        dataset_id,
        authorization,
    )


    # ======================================================
    # SEND DATA TO ML SERVICE
    # ======================================================

    payload = {
        "dependent_variable":
            request
            .dependent_variable,

        "predictors":
            request
            .predictors,

        "rows":
            rows,

        "test_size":
            request
            .test_size,

        "random_seed":
            request
            .random_seed,

        "cv_folds":
            getattr(
                request,
                "cv_folds",
                5,
            ),

        "future_values":
            getattr(
                request,
                "future_values",
                None,
            ),

        "time_variable":
            getattr(
                request,
                "time_variable",
                None,
            ),
    }


    try:

        async with httpx.AsyncClient(
            timeout=180.0,
        ) as client:

            response = await client.post(
                (
                    f"{ML_SERVICE_URL}"
                    f"/ml/predictive/regression"
                ),
                json=payload,
            )


        if response.status_code != 200:

            try:
                detail = (
                    response.json()
                    .get(
                        "detail",
                        (
                            "ML Service could not "
                            "complete prediction."
                        ),
                    )
                )

            except Exception:
                detail = (
                    "ML Service could not "
                    "complete prediction."
                )


            raise HTTPException(
                status_code=(
                    response.status_code
                ),
                detail=detail,
            )


        ml_result = (
            response.json()
        )


        # ==================================================
        # NORMALIZED SSAS TABLES
        # ==================================================

        tables = [
            {
                "title":
                    "Model Comparison",

                "columns": [
                    "Model",
                    "CV RMSE",
                    "CV R²",
                    "Train R²",
                    "Test R²",
                    "Test RMSE",
                    "Test MAE",
                    "Test MAPE %",
                ],

                "rows":
                    ml_result.get(
                        "model_comparison",
                        [],
                    ),
            },

            {
                "title":
                    "Feature Importance",

                "columns": [
                    "Predictor",
                    "Importance",
                    "Relative Importance %",
                ],

                "rows":
                    ml_result.get(
                        "feature_importance",
                        [],
                    ),
            },

            {
                "title":
                    "Future Scenario",

                "columns": [
                    "Variable",
                    "Value",
                ],

                "rows": [
                    {
                        "Variable":
                            key,

                        "Value":
                            value,
                    }
                    for key, value
                    in (
                        ml_result
                        .get(
                            "future_scenario",
                            {},
                        )
                        .items()
                    )
                ],
            },

            {
                "title":
                    "Sensitivity Analysis",

                "columns": [
                    "Predictor",
                    "Current Value",
                    "+5% Scenario",
                    "Predicted Outcome (+5%)",
                    "Outcome Change (+5%)",
                    "-5% Scenario",
                    "Predicted Outcome (-5%)",
                    "Outcome Change (-5%)",
                ],

                "rows":
                    ml_result.get(
                        "sensitivity_analysis",
                        [],
                    ),
            },

            {
                "title":
                    "Recommendations",

                "columns": [
                    "Priority",
                    "Recommendation",
                ],

                "rows":
                    ml_result.get(
                        "recommendations",
                        [],
                    ),
            },

            {
                "title":
                    "Holdout Predictions",

                "columns": [
                    "Case",
                    "Actual",
                    "Predicted",
                    "Residual",
                    "Absolute Error",
                ],

                "rows":
                    ml_result.get(
                        "holdout_predictions",
                        [],
                    ),
            },
        ]


        best_model = (
            ml_result.get(
                "best_model",
                "Unknown",
            )
        )


        future_prediction = (
            ml_result.get(
                "future_prediction"
            )
        )


        historical_average = (
            ml_result.get(
                "historical_average"
            )
        )


        test_metrics = (
            ml_result.get(
                "test_metrics",
                {},
            )
        )


        interpretation = (
            f"SSAS compared multiple machine-learning "
            f"models and automatically selected "
            f"{best_model}. "
            f"The future scenario produces a predicted "
            f"{request.dependent_variable} value of "
            f"{future_prediction:.4f}. "
            f"The historical training average is "
            f"{historical_average:.4f}. "
            f"On held-out data, the selected model "
            f"achieved R² = "
            f"{test_metrics.get('R²', 0):.4f}, "
            f"RMSE = "
            f"{test_metrics.get('RMSE', 0):.4f}, "
            f"and MAE = "
            f"{test_metrics.get('MAE', 0):.4f}."
        )


        detailed_explanation = {
            "title":
                (
                    "Detailed Explanation — "
                    "Smart Predictive Analytics"
                ),

            "introduction":
                (
                    "SSAS compared several predictive "
                    "models, selected the strongest model "
                    "using cross-validation, evaluated it "
                    "on held-out observations, predicted "
                    "the supplied future scenario and "
                    "generated model-based recommendations."
                ),

            "sections": [
                {
                    "title":
                        "1. Models compared",

                    "paragraphs": [
                        (
                            "SSAS compared Linear Regression, "
                            "Decision Tree, Random Forest and "
                            "Gradient Boosting."
                        ),
                        (
                            "Using several models allows SSAS "
                            "to determine whether a simple "
                            "linear relationship or a more "
                            "complex nonlinear relationship "
                            "better represents the data."
                        ),
                    ],
                },

                {
                    "title":
                        "2. How the best model was selected",

                    "paragraphs": [
                        ml_result.get(
                            "model_selection_reason",
                            (
                                "The best model was selected "
                                "using cross-validation."
                            ),
                        ),
                        (
                            "Cross-validation evaluates each "
                            "model repeatedly on different "
                            "subsets of the training data. "
                            "This provides a more reliable "
                            "basis for model selection than "
                            "choosing the model that happens "
                            "to perform best on one holdout set."
                        ),
                    ],
                },

                {
                    "title":
                        "3. Selected model",

                    "paragraphs": [
                        (
                            f"The automatically selected "
                            f"model is {best_model}."
                        ),
                    ],
                },

                {
                    "title":
                        "4. Predictive performance",

                    "paragraphs": [
                        (
                            f"Test R² = "
                            f"{test_metrics.get('R²')}."
                        ),
                        (
                            f"Test RMSE = "
                            f"{test_metrics.get('RMSE')}."
                        ),
                        (
                            f"Test MAE = "
                            f"{test_metrics.get('MAE')}."
                        ),
                        (
                            "Performance on held-out data is "
                            "more important than training "
                            "performance because it estimates "
                            "how the model behaves on unseen data."
                        ),
                    ],
                },

                {
                    "title":
                        "5. Future prediction",

                    "paragraphs": [
                        (
                            f"For the supplied future scenario, "
                            f"SSAS predicts "
                            f"{request.dependent_variable} = "
                            f"{future_prediction}."
                        ),
                        (
                            f"The historical training average "
                            f"was {historical_average}."
                        ),
                    ],
                },

                {
                    "title":
                        "6. Feature importance",

                    "paragraphs": [
                        (
                            "Feature importance identifies the "
                            "predictors that contribute most to "
                            "the predictive performance of the "
                            "selected model."
                        ),
                        (
                            "Importance describes predictive "
                            "usefulness; it does not prove that "
                            "the predictor causes the outcome."
                        ),
                    ],
                },

                {
                    "title":
                        "7. Sensitivity analysis",

                    "paragraphs": [
                        (
                            "SSAS changes each predictor by "
                            "approximately ±5% while holding "
                            "the remaining future scenario "
                            "values constant."
                        ),
                        (
                            "The resulting change in predicted "
                            "outcome provides a model-based "
                            "indication of how sensitive the "
                            "prediction is to that variable."
                        ),
                    ],
                },

                {
                    "title":
                        "8. Recommendations",

                    "paragraphs": [
                        (
                            "Recommendations are generated from "
                            "the predicted outcome, historical "
                            "baseline, feature importance and "
                            "scenario sensitivity."
                        ),
                        (
                            "Recommendations should support "
                            "decision-making rather than replace "
                            "professional or domain-specific "
                            "judgement."
                        ),
                    ],
                },

                {
                    "title":
                        "9. Important limitation",

                    "paragraphs": [
                        (
                            "Prediction is not causation. "
                            "Changing an influential predictor "
                            "does not necessarily cause the "
                            "predicted outcome to change by the "
                            "amount estimated by the model."
                        ),
                        (
                            "Predictions are most reliable when "
                            "future conditions are reasonably "
                            "similar to the historical data used "
                            "to train the model."
                        ),
                    ],
                },

                {
                    "title":
                        "10. Final conclusion",

                    "paragraphs": [
                        interpretation,
                    ],
                },
            ],
        }


        return {
            "dataset_id":
                dataset_id,

            "analysis_name":
                "Smart Predictive Analytics",

            "best_model":
                best_model,

            "configuration": {
                "dependent_variable":
                    request
                    .dependent_variable,

                "predictors":
                    request
                    .predictors,

                "test_size":
                    request
                    .test_size,

                "random_seed":
                    request
                    .random_seed,

                "future_values":
                    getattr(
                        request,
                        "future_values",
                        None,
                    ),

                "time_variable":
                    getattr(
                        request,
                        "time_variable",
                        None,
                    ),
            },

            "prediction": {
                "future_prediction":
                    future_prediction,

                "historical_average":
                    historical_average,

                "best_model":
                    best_model,

                "split_method":
                    ml_result.get(
                        "split_method"
                    ),
            },

            "metrics":
                test_metrics,

            "tables":
                tables,

            "recommendations":
                ml_result.get(
                    "recommendations",
                    [],
                ),

            "interpretation":
                interpretation,

            "detailed_explanation":
                detailed_explanation,

            "apa":
                (
                    f"Multiple predictive models were "
                    f"compared using cross-validation. "
                    f"{best_model} produced the strongest "
                    f"cross-validated performance and achieved "
                    f"R² = "
                    f"{test_metrics.get('R²', 0):.3f}, "
                    f"RMSE = "
                    f"{test_metrics.get('RMSE', 0):.3f}, "
                    f"and MAE = "
                    f"{test_metrics.get('MAE', 0):.3f} "
                    f"on the holdout sample."
                ),
        }


    except HTTPException:
        raise


    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Smart predictive analysis failed: "
                f"{str(exc)}"
            ),
        )
