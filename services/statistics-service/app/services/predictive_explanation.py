def number(
    value,
    digits=4,
):
    if value is None:
        return "not available"

    return (
        f"{float(value):.{digits}f}"
    )


def build_predictive_explanation(
    result,
):
    configuration = (
        result.get(
            "configuration",
            {}
        )
        or {}
    )

    metrics = (
        result.get(
            "metrics",
            {}
        )
        or {}
    )


    dependent = (
        configuration.get(
            "dependent_variable",
            "outcome"
        )
    )

    predictors = (
        configuration.get(
            "predictors",
            []
        )
        or []
    )

    test_size = (
        configuration.get(
            "test_size",
            0.20
        )
    )


    training = (
        metrics.get(
            "training",
            {}
        )
        or {}
    )

    testing = (
        metrics.get(
            "testing",
            {}
        )
        or {}
    )

    baseline = (
        metrics.get(
            "baseline",
            {}
        )
        or {}
    )


    test_r2 = (
        testing.get(
            "R²"
        )
    )

    train_r2 = (
        training.get(
            "R²"
        )
    )


    if (
        test_r2 is not None
        and
        test_r2 >= 0
    ):
        r2_interpretation = (
            f"The test R² is "
            f"{number(test_r2)}. "
            f"This means the model explains approximately "
            f"{number(test_r2 * 100, 2)}% of the variation "
            f"in {dependent} within the held-out test sample."
        )

    elif (
        test_r2 is not None
    ):
        r2_interpretation = (
            f"The test R² is "
            f"{number(test_r2)}. "
            f"Because it is negative, the model predicts "
            f"the held-out observations worse than a simple "
            f"mean-based baseline."
        )

    else:
        r2_interpretation = (
            "Test R² could not be calculated."
        )


    return {
        "title":
            (
                "Detailed Explanation — "
                "Predictive Analytics"
            ),

        "introduction":
            (
                "This explanation describes how SSAS trained "
                "the predictive model, evaluated it on unseen "
                "data and interpreted its prediction accuracy."
            ),

        "sections": [
            {
                "title":
                    "1. What predictive analysis was performed?",

                "paragraphs": [
                    (
                        f"SSAS created an OLS linear prediction "
                        f"model for {dependent} using "
                        f"{', '.join(predictors)}."
                    ),
                    (
                        "The purpose of predictive analytics is "
                        "to estimate how accurately a statistical "
                        "model can predict outcomes for observations "
                        "that were not used to fit the model."
                    ),
                ],
            },

            {
                "title":
                    "2. Training and testing data",

                "paragraphs": [
                    (
                        f"SSAS reserved approximately "
                        f"{test_size * 100:.0f}% of complete cases "
                        f"for testing and used the remaining data "
                        f"for model training."
                    ),
                    (
                        "The training sample is used to estimate "
                        "the regression coefficients. The testing "
                        "sample is kept separate and is used to "
                        "evaluate how well the model generalizes "
                        "to unseen observations."
                    ),
                    (
                        "Testing performance is more informative "
                        "than training performance when evaluating "
                        "predictive usefulness."
                    ),
                ],
            },

            {
                "title":
                    "3. Understanding R²",

                "paragraphs": [
                    r2_interpretation,
                    (
                        f"The training R² is "
                        f"{number(train_r2)}."
                    ),
                    (
                        "A large difference between training and "
                        "testing R² can indicate overfitting."
                    ),
                ],
            },

            {
                "title":
                    "4. Understanding RMSE",

                "paragraphs": [
                    (
                        f"The test RMSE is "
                        f"{number(testing.get('RMSE'))}."
                    ),
                    (
                        "Root Mean Squared Error represents the "
                        "typical size of prediction errors in the "
                        f"same measurement units as {dependent}. "
                        "Lower RMSE values indicate more accurate "
                        "predictions."
                    ),
                    (
                        "Because RMSE squares errors before "
                        "averaging them, large prediction errors "
                        "receive greater weight."
                    ),
                ],
            },

            {
                "title":
                    "5. Understanding MAE",

                "paragraphs": [
                    (
                        f"The test MAE is "
                        f"{number(testing.get('MAE'))}."
                    ),
                    (
                        "Mean Absolute Error is the average absolute "
                        "difference between observed and predicted "
                        "values. It is often easier to interpret "
                        "than RMSE because each error contributes "
                        "linearly."
                    ),
                ],
            },

            {
                "title":
                    "6. Understanding MAPE",

                "paragraphs": [
                    (
                        f"The test MAPE is "
                        f"{number(testing.get('MAPE %'), 2)}%."
                    ),
                    (
                        "MAPE expresses prediction error as a "
                        "percentage of the actual value. It should "
                        "be interpreted cautiously when actual "
                        "values are zero or very close to zero."
                    ),
                ],
            },

            {
                "title":
                    "7. Baseline comparison",

                "paragraphs": [
                    (
                        f"The baseline test RMSE is "
                        f"{number(baseline.get('RMSE'))}."
                    ),
                    (
                        "The baseline predicts every test case using "
                        "the average outcome from the training data. "
                        "A useful predictive model should normally "
                        "perform better than this simple baseline."
                    ),
                    (
                        f"SSAS estimates an RMSE improvement of "
                        f"{number(metrics.get('rmse_improvement_percent'), 2)}% "
                        f"relative to the baseline."
                    ),
                ],
            },

            {
                "title":
                    "8. Model coefficients",

                "paragraphs": [
                    (
                        "The Model Coefficients table shows the "
                        "estimated contribution of each predictor."
                    ),
                    (
                        "A positive coefficient indicates that the "
                        "predicted outcome increases as that predictor "
                        "increases, holding other predictors constant."
                    ),
                    (
                        "A negative coefficient indicates that the "
                        "predicted outcome decreases as that predictor "
                        "increases, holding the other predictors constant."
                    ),
                ],
            },

            {
                "title":
                    "9. Actual and predicted values",

                "paragraphs": [
                    (
                        "The Holdout Predictions table compares the "
                        "actual value with the value predicted by the "
                        "model for cases that were not used for training."
                    ),
                    (
                        "Residual equals Actual minus Predicted. "
                        "A positive residual means the model "
                        "underpredicted that case, while a negative "
                        "residual means it overpredicted it."
                    ),
                ],
            },

            {
                "title":
                    "10. Generalization and overfitting",

                "paragraphs": [
                    (
                        metrics.get(
                            "generalization_status",
                            "Generalization status unavailable."
                        )
                    ),
                    (
                        "Overfitting occurs when a model learns the "
                        "training data very well but performs poorly "
                        "on unseen observations."
                    ),
                    (
                        "The difference between training and testing "
                        "performance is therefore important when "
                        "evaluating predictive reliability."
                    ),
                ],
            },

            {
                "title":
                    "11. Prediction versus explanation",

                "paragraphs": [
                    (
                        "A model can be useful for prediction even "
                        "when individual coefficients are difficult "
                        "to interpret causally."
                    ),
                    (
                        "Predictive accuracy and causal explanation "
                        "are different objectives. A predictive "
                        "relationship does not establish that changing "
                        "a predictor causes the outcome to change."
                    ),
                ],
            },

            {
                "title":
                    "12. Limitations",

                "paragraphs": [
                    (
                        "Predictive performance depends on whether "
                        "future observations are similar to the data "
                        "used to develop the model."
                    ),
                    (
                        "Missing data, measurement error, extreme "
                        "observations, nonlinear relationships and "
                        "omitted predictors can reduce accuracy."
                    ),
                    (
                        "A single train-test split also contains some "
                        "random variation. Cross-validation can later "
                        "be added to SSAS for more robust model "
                        "performance estimation."
                    ),
                    (
                        "This statistical module currently supports "
                        "continuous numeric/date-like outcomes and "
                        "predictors. Advanced classification and "
                        "machine-learning algorithms remain part of "
                        "the separate AI/ML module."
                    ),
                ],
            },

            {
                "title":
                    "13. Final conclusion",

                "paragraphs": [
                    result.get(
                        "interpretation",
                        "No interpretation available."
                    ),
                ],
            },
        ],
    }
