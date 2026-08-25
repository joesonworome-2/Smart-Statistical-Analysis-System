import numpy as np
import pandas as pd
from scipy import stats


def multiple_linear_regression(
    dataframe: pd.DataFrame,
    predictor_variables: list[str],
    response_variable: str,
):
    """
    Perform Multiple Linear Regression using Ordinary Least Squares.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Dataset to analyze.

    predictor_variables : list[str]
        Independent/predictor variables.

    response_variable : str
        Dependent/response variable.

    Returns
    -------
    dict
        Complete multiple linear regression results.
    """

    # ---------------------------------------------------------
    # Validate variables
    # ---------------------------------------------------------

    if not predictor_variables:
        raise ValueError(
            "At least two predictor variables are required."
        )

    if len(predictor_variables) < 2:
        raise ValueError(
            "Multiple linear regression requires at least two predictor variables."
        )

    variables = predictor_variables + [response_variable]

    missing_variables = [
        variable
        for variable in variables
        if variable not in dataframe.columns
    ]

    if missing_variables:
        raise ValueError(
            f"Variables not found in dataset: {missing_variables}"
        )

    if response_variable in predictor_variables:
        raise ValueError(
            "Response variable cannot also be a predictor variable."
        )

    # ---------------------------------------------------------
    # Select and clean data
    # ---------------------------------------------------------

    data = dataframe[variables].copy()

    for variable in variables:
        data[variable] = pd.to_numeric(
            data[variable],
            errors="coerce",
        )

    data = data.dropna()

    sample_size = len(data)

    number_of_predictors = len(predictor_variables)

    if sample_size <= number_of_predictors:
        raise ValueError(
            "Not enough observations for multiple linear regression."
        )

    if sample_size <= number_of_predictors + 1:
        raise ValueError(
            "Not enough observations to calculate reliable regression statistics."
        )

    # ---------------------------------------------------------
    # Prepare matrices
    # ---------------------------------------------------------

    X = data[predictor_variables].to_numpy(dtype=float)

    y = data[response_variable].to_numpy(dtype=float)

    # Add intercept
    X_design = np.column_stack(
        [np.ones(len(X)), X]
    )

    # ---------------------------------------------------------
    # Calculate coefficients using least squares
    # ---------------------------------------------------------

    coefficients, residuals, rank, singular_values = np.linalg.lstsq(
        X_design,
        y,
        rcond=None,
    )

    intercept = coefficients[0]

    slopes = coefficients[1:]

    # ---------------------------------------------------------
    # Predictions and residuals
    # ---------------------------------------------------------

    predictions = X_design @ coefficients

    residual_errors = y - predictions

    # ---------------------------------------------------------
    # Sum of squares
    # ---------------------------------------------------------

    y_mean = np.mean(y)

    total_sum_of_squares = np.sum(
        (y - y_mean) ** 2
    )

    residual_sum_of_squares = np.sum(
        residual_errors ** 2
    )

    regression_sum_of_squares = (
        total_sum_of_squares
        - residual_sum_of_squares
    )

    # ---------------------------------------------------------
    # Degrees of freedom
    # ---------------------------------------------------------

    df_regression = number_of_predictors

    df_residual = (
        sample_size
        - number_of_predictors
        - 1
    )

    df_total = sample_size - 1

    # ---------------------------------------------------------
    # Mean squares
    # ---------------------------------------------------------

    mean_square_regression = (
        regression_sum_of_squares
        / df_regression
    )

    mean_square_residual = (
        residual_sum_of_squares
        / df_residual
    )

    # ---------------------------------------------------------
    # R-squared
    # ---------------------------------------------------------

    if total_sum_of_squares == 0:
        r_squared = 0.0
    else:
        r_squared = (
            1
            - (
                residual_sum_of_squares
                / total_sum_of_squares
            )
        )

    # ---------------------------------------------------------
    # Adjusted R-squared
    # ---------------------------------------------------------

    adjusted_r_squared = (
        1
        - (
            (1 - r_squared)
            * (sample_size - 1)
            / df_residual
        )
    )

    # ---------------------------------------------------------
    # Multiple correlation coefficient
    # ---------------------------------------------------------

    multiple_r = np.sqrt(
        max(0.0, r_squared)
    )

    # ---------------------------------------------------------
    # Standard error of regression
    # ---------------------------------------------------------

    standard_error = np.sqrt(
        mean_square_residual
    )

    # ---------------------------------------------------------
    # F-statistic
    # ---------------------------------------------------------

    if mean_square_residual == 0:
        f_statistic = float("inf")
        f_p_value = 0.0
    else:
        f_statistic = (
            mean_square_regression
            / mean_square_residual
        )

        f_p_value = stats.f.sf(
            f_statistic,
            df_regression,
            df_residual,
        )

    # ---------------------------------------------------------
    # Coefficient inference
    # ---------------------------------------------------------

    # Variance-covariance matrix
    xtx_inverse = np.linalg.pinv(
        X_design.T @ X_design
    )

    covariance_matrix = (
        mean_square_residual
        * xtx_inverse
    )

    standard_errors = np.sqrt(
        np.maximum(
            np.diag(covariance_matrix),
            0,
        )
    )

    t_statistics = np.divide(
        coefficients,
        standard_errors,
        out=np.zeros_like(coefficients),
        where=standard_errors != 0,
    )

    p_values = (
        2
        * stats.t.sf(
            np.abs(t_statistics),
            df_residual,
        )
    )

    # ---------------------------------------------------------
    # Confidence intervals
    # ---------------------------------------------------------

    alpha = 0.05

    t_critical = stats.t.ppf(
        1 - alpha / 2,
        df_residual,
    )

    confidence_lower = (
        coefficients
        - t_critical * standard_errors
    )

    confidence_upper = (
        coefficients
        + t_critical * standard_errors
    )

    # ---------------------------------------------------------
    # Build coefficient results
    # ---------------------------------------------------------

    coefficient_results = {
        "intercept": {
            "coefficient": float(intercept),
            "standard_error": float(
                standard_errors[0]
            ),
            "t_statistic": float(
                t_statistics[0]
            ),
            "p_value": float(
                p_values[0]
            ),
            "confidence_interval": {
                "lower": float(
                    confidence_lower[0]
                ),
                "upper": float(
                    confidence_upper[0]
                ),
                "confidence_level": 0.95,
            },
        }
    }

    for index, variable in enumerate(
        predictor_variables,
        start=1,
    ):
        coefficient_results[variable] = {
            "coefficient": float(
                coefficients[index]
            ),
            "standard_error": float(
                standard_errors[index]
            ),
            "t_statistic": float(
                t_statistics[index]
            ),
            "p_value": float(
                p_values[index]
            ),
            "confidence_interval": {
                "lower": float(
                    confidence_lower[index]
                ),
                "upper": float(
                    confidence_upper[index]
                ),
                "confidence_level": 0.95,
            },
        }

    # ---------------------------------------------------------
    # Regression equation
    # ---------------------------------------------------------

    equation = (
        f"{response_variable} = "
        f"{intercept:.6f}"
    )

    for coefficient, variable in zip(
        slopes,
        predictor_variables,
    ):
        sign = "+" if coefficient >= 0 else "-"

        equation += (
            f" {sign} "
            f"{abs(coefficient):.6f} × {variable}"
        )

    # ---------------------------------------------------------
    # Hypothesis testing
    # ---------------------------------------------------------

    if f_p_value < alpha:
        decision = "Reject the null hypothesis."
        significance = (
            "Statistically significant (p < 0.05)."
        )
        interpretation = (
            "The overall regression model is "
            "statistically significant."
        )
    else:
        decision = "Fail to reject the null hypothesis."
        significance = (
            "Not statistically significant (p >= 0.05)."
        )
        interpretation = (
            "There is insufficient evidence that "
            "the overall regression model is "
            "statistically significant."
        )

    # ---------------------------------------------------------
    # Return complete results
    # ---------------------------------------------------------

    return {
        "test": "Multiple Linear Regression",

        "predictor_variables": predictor_variables,

        "response_variable": response_variable,

        "sample_size": sample_size,

        "number_of_predictors": number_of_predictors,

        "regression_equation": equation,

        "coefficients": coefficient_results,

        "model_statistics": {
            "multiple_r": float(multiple_r),
            "r_squared": float(r_squared),
            "adjusted_r_squared": float(
                adjusted_r_squared
            ),
            "standard_error": float(
                standard_error
            ),
        },

        "anova": {
            "regression": {
                "sum_of_squares": float(
                    regression_sum_of_squares
                ),
                "degrees_of_freedom": int(
                    df_regression
                ),
                "mean_square": float(
                    mean_square_regression
                ),
            },

            "residual": {
                "sum_of_squares": float(
                    residual_sum_of_squares
                ),
                "degrees_of_freedom": int(
                    df_residual
                ),
                "mean_square": float(
                    mean_square_residual
                ),
            },

            "total": {
                "sum_of_squares": float(
                    total_sum_of_squares
                ),
                "degrees_of_freedom": int(
                    df_total
                ),
            },

            "f_statistic": float(
                f_statistic
            ),

            "p_value": float(
                f_p_value
            ),
        },

        "hypothesis_test": {
            "alpha": alpha,

            "null_hypothesis": (
                "All regression coefficients "
                "for the predictors are equal to zero."
            ),

            "alternative_hypothesis": (
                "At least one regression coefficient "
                "is different from zero."
            ),

            "decision": decision,

            "significance": significance,

            "interpretation": interpretation,
        },

        "residuals": {
            "mean": float(
                np.mean(residual_errors)
            ),
            "sum_of_squared_errors": float(
                residual_sum_of_squares
            ),
        },
    }
