def find_table(
    result,
    title,
):
    for table in (
        result.get(
            "tables",
            []
        )
        or []
    ):
        if (
            table.get(
                "title"
            )
            ==
            title
        ):
            return table

    return None


def format_number(
    value,
    digits=4,
):
    if value is None:
        return "not available"

    if isinstance(
        value,
        int,
    ):
        return str(
            value
        )

    return (
        f"{float(value):.{digits}f}"
    )


def format_p(
    value,
):
    if value is None:
        return "not available"

    if value < 0.001:
        return "p < 0.001"

    return (
        f"p = {value:.4f}"
    )


def build_regression_explanation(
    result,
):
    configuration = (
        result.get(
            "configuration",
            {}
        )
        or {}
    )

    dependent = (
        configuration.get(
            "dependent_variable",
            "dependent variable"
        )
    )

    predictors = (
        configuration.get(
            "predictors",
            []
        )
        or []
    )

    alpha = (
        configuration.get(
            "alpha",
            0.05
        )
    )


    model_table = (
        find_table(
            result,
            "Model Summary",
        )
    )

    anova_table = (
        find_table(
            result,
            "ANOVA",
        )
    )

    coefficient_table = (
        find_table(
            result,
            "Regression Coefficients",
        )
    )

    vif_table = (
        find_table(
            result,
            "Multicollinearity",
        )
    )


    model_row = (
        model_table[
            "rows"
        ][0]
        if (
            model_table
            and
            model_table.get(
                "rows"
            )
        )
        else {}
    )


    regression_row = {}

    if (
        anova_table
        and
        anova_table.get(
            "rows"
        )
    ):
        for row in (
            anova_table[
                "rows"
            ]
        ):
            if (
                row.get(
                    "Source"
                )
                ==
                "Regression"
            ):
                regression_row = (
                    row
                )
                break


    coefficient_rows = (
        coefficient_table.get(
            "rows",
            []
        )
        if coefficient_table
        else []
    )


    r_squared = (
        model_row.get(
            "R²"
        )
    )

    adjusted_r_squared = (
        model_row.get(
            "Adjusted R²"
        )
    )

    rmse = (
        model_row.get(
            "RMSE"
        )
    )

    f_statistic = (
        regression_row.get(
            "F"
        )
    )

    model_p = (
        regression_row.get(
            "p-value"
        )
    )


    coefficient_paragraphs = []


    for row in (
        coefficient_rows
    ):
        name = (
            row.get(
                "Predictor"
            )
        )

        coefficient = (
            row.get(
                "B"
            )
        )

        p_value = (
            row.get(
                "p-value"
            )
        )

        beta = (
            row.get(
                "Standardized Beta"
            )
        )

        lower = (
            row.get(
                "CI Lower"
            )
        )

        upper = (
            row.get(
                "CI Upper"
            )
        )


        if name == "Intercept":
            coefficient_paragraphs.append(
                (
                    f"The intercept is "
                    f"{format_number(coefficient)}. "
                    f"This represents the predicted value "
                    f"of {dependent} when all predictors "
                    f"equal zero. Its practical meaning "
                    f"depends on whether zero is meaningful "
                    f"for the predictors."
                )
            )

            continue


        direction = (
            "positive"
            if coefficient > 0
            else
            "negative"
        )


        paragraph = (
            f"{name}: B = "
            f"{format_number(coefficient)}, "
            f"{format_p(p_value)}. "
            f"The coefficient is {direction}. "
        )


        if coefficient > 0:
            paragraph += (
                f"Holding the other predictors constant, "
                f"a one-unit increase in {name} is associated "
                f"with an estimated increase of "
                f"{format_number(abs(coefficient))} units "
                f"in {dependent}. "
            )

        else:
            paragraph += (
                f"Holding the other predictors constant, "
                f"a one-unit increase in {name} is associated "
                f"with an estimated decrease of "
                f"{format_number(abs(coefficient))} units "
                f"in {dependent}. "
            )


        if beta is not None:
            paragraph += (
                f"The standardized beta is "
                f"{format_number(beta)}, allowing its relative "
                f"predictive contribution to be compared with "
                f"the other predictors. "
            )


        paragraph += (
            f"The confidence interval extends from "
            f"{format_number(lower)} to "
            f"{format_number(upper)}."
        )


        coefficient_paragraphs.append(
            paragraph
        )


    vif_paragraphs = []

    if vif_table:
        for row in (
            vif_table.get(
                "rows",
                []
            )
        ):
            vif_paragraphs.append(
                (
                    f"{row.get('Predictor')}: "
                    f"VIF = "
                    f"{format_number(row.get('VIF'))}, "
                    f"tolerance = "
                    f"{format_number(row.get('Tolerance'))}. "
                    f"SSAS status: "
                    f"{row.get('Status')}."
                )
            )


    diagnostics = (
        result.get(
            "diagnostics",
            {}
        )
        or {}
    )


    diagnostic_paragraphs = []

    for row in (
        diagnostics.get(
            "rows",
            []
        )
        or []
    ):
        diagnostic_paragraphs.append(
            (
                f"{row.get('Diagnostic')}: "
                f"statistic = "
                f"{format_number(row.get('Statistic'))}; "
                f"{format_p(row.get('p-value'))}. "
                f"{row.get('Interpretation')}."
            )
        )


    return {
        "title":
            (
                "Detailed Explanation — "
                f"{result.get('test_name', 'Regression Analysis')}"
            ),

        "introduction":
            (
                "This explanation describes the regression "
                "model, model fit, ANOVA result, coefficients, "
                "predictor significance, confidence intervals, "
                "multicollinearity and residual diagnostics."
            ),

        "sections": [
            {
                "title":
                    "1. What analysis was performed?",

                "paragraphs": [
                    (
                        f"SSAS used "
                        f"{result.get('test_name', 'linear regression')} "
                        f"to model {dependent} using "
                        f"{', '.join(predictors)} as predictor"
                        f"{'s' if len(predictors) != 1 else ''}."
                    ),
                    (
                        "Linear regression estimates how the "
                        "expected value of the dependent variable "
                        "changes as the predictors change."
                    ),
                ],
            },

            {
                "title":
                    "2. Dependent variable and predictors",

                "paragraphs": [
                    (
                        f"The dependent variable is {dependent}."
                    ),
                    (
                        f"The predictor variables are "
                        f"{', '.join(predictors)}."
                    ),
                    (
                        "In multiple regression, each predictor "
                        "coefficient is interpreted while holding "
                        "the remaining predictors constant."
                    ),
                ],
            },

            {
                "title":
                    "3. Model fit",

                "paragraphs": [
                    (
                        f"R² = {format_number(r_squared)}. "
                        f"This means the model explains approximately "
                        f"{format_number((r_squared or 0) * 100, 2)}% "
                        f"of the observed variation in {dependent}."
                    ),
                    (
                        f"Adjusted R² = "
                        f"{format_number(adjusted_r_squared)}. "
                        f"Adjusted R² penalizes the model for adding "
                        f"predictors that contribute little useful "
                        f"explanatory information."
                    ),
                    (
                        f"RMSE = {format_number(rmse)}. "
                        f"RMSE describes the typical size of the "
                        f"prediction errors in the units of "
                        f"{dependent}. Smaller values indicate "
                        f"predictions closer to the observed values."
                    ),
                ],
            },

            {
                "title":
                    "4. Overall model significance",

                "paragraphs": [
                    (
                        f"The regression F-statistic is "
                        f"{format_number(f_statistic)} with "
                        f"{format_p(model_p)}."
                    ),
                    (
                        f"SSAS compares the model p-value with "
                        f"α = {alpha}."
                    ),
                    (
                        (
                            "Because the model p-value is below alpha, "
                            "the regression model is statistically "
                            "significant. At least one regression "
                            "coefficient provides evidence of an "
                            "association with the dependent variable."
                        )
                        if (
                            model_p is not None
                            and
                            model_p < alpha
                        )
                        else
                        (
                            "The model p-value is not below alpha. "
                            "The available data therefore do not "
                            "provide sufficient evidence that the "
                            "predictors collectively explain variation "
                            "in the dependent variable."
                        )
                    ),
                ],
            },

            {
                "title":
                    "5. Regression coefficients",

                "paragraphs":
                    coefficient_paragraphs,
            },

            {
                "title":
                    "6. Statistical significance of predictors",

                "paragraphs": [
                    (
                        "Each predictor has its own t-test and p-value. "
                        "A predictor with p < α is statistically "
                        "significant after accounting for the other "
                        "predictors included in the model."
                    ),
                    (
                        "A nonsignificant predictor should not "
                        "automatically be considered useless. Sample "
                        "size, multicollinearity, measurement error, "
                        "theoretical importance and model specification "
                        "should also be considered."
                    ),
                ],
            },

            {
                "title":
                    "7. Confidence intervals",

                "paragraphs": [
                    (
                        "The coefficient confidence interval describes "
                        "a range of population coefficient values "
                        "compatible with the observed data and the "
                        "linear regression model."
                    ),
                    (
                        "If a confidence interval for a slope excludes "
                        "zero, that generally corresponds to statistical "
                        "significance at the matching two-sided alpha level."
                    ),
                ],
            },

            {
                "title":
                    "8. Multicollinearity",

                "paragraphs": [
                    (
                        "Variance Inflation Factor (VIF) measures how "
                        "strongly each predictor is explained by the "
                        "other predictors. Large VIF values indicate "
                        "multicollinearity, which can inflate standard "
                        "errors and make coefficients unstable."
                    ),
                    *vif_paragraphs,
                ],
            },

            {
                "title":
                    "9. Residual diagnostics",

                "paragraphs": [
                    (
                        "Regression assumptions are evaluated primarily "
                        "using the residuals rather than the raw dependent "
                        "variable."
                    ),
                    *diagnostic_paragraphs,
                    (
                        "Automated diagnostic tests should not be used "
                        "mechanically. Residual plots and the research "
                        "design should also be reviewed."
                    ),
                ],
            },

            {
                "title":
                    "10. Practical interpretation",

                "paragraphs": [
                    (
                        "Statistical significance does not necessarily "
                        "mean that the model is useful in practice. "
                        "R², RMSE, coefficient magnitudes, confidence "
                        "intervals and subject-matter requirements should "
                        "also be considered."
                    ),
                    (
                        "A model may be statistically significant but "
                        "still have weak predictive accuracy."
                    ),
                ],
            },

            {
                "title":
                    "11. Prediction versus causation",

                "paragraphs": [
                    (
                        "Regression can describe conditional associations "
                        "and can be used for prediction, but a regression "
                        "coefficient does not automatically establish that "
                        "changing a predictor will cause the dependent "
                        "variable to change."
                    ),
                    (
                        "Causal interpretation requires an appropriate "
                        "study design, temporal ordering and control of "
                        "alternative explanations."
                    ),
                ],
            },

            {
                "title":
                    "12. Limitations",

                "paragraphs": [
                    (
                        "Regression results can be affected by missing "
                        "values, influential observations, measurement "
                        "error, nonlinear relationships, omitted variables "
                        "and multicollinearity."
                    ),
                    (
                        "The model currently uses complete cases for the "
                        "selected variables."
                    ),
                    (
                        "The current SSAS implementation handles numeric "
                        "and date-like variables. Categorical predictor "
                        "encoding will be added separately."
                    ),
                ],
            },

            {
                "title":
                    "13. Final conclusion",

                "paragraphs": [
                    result.get(
                        "interpretation",
                        "No interpretation was available."
                    ),
                ],
            },
        ],
    }
