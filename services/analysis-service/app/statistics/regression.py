from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def _interpret_correlation(r_squared: float) -> str:
    if r_squared >= 0.90:
        return "Extremely strong model fit."
    elif r_squared >= 0.70:
        return "Strong model fit."
    elif r_squared >= 0.50:
        return "Moderate model fit."
    elif r_squared >= 0.30:
        return "Weak model fit."
    return "Very weak model fit."


def _interpret_slope(slope: float) -> str:
    if slope > 0:
        return (
            "There is a positive relationship between the "
            "predictor and response variable."
        )

    if slope < 0:
        return (
            "There is a negative relationship between the "
            "predictor and response variable."
        )

    return (
        "There is no linear change in the response variable "
        "as the predictor changes."
    )


def simple_linear_regression(
    dataframe: pd.DataFrame,
    x_variable: str,
    y_variable: str,
    alpha: float = 0.05,
) -> dict[str, Any]:

    # ---------------------------------------------------------
    # Validate variables
    # ---------------------------------------------------------

    if x_variable not in dataframe.columns:
        raise ValueError(
            f"Predictor variable '{x_variable}' "
            "was not found in the dataset."
        )

    if y_variable not in dataframe.columns:
        raise ValueError(
            f"Response variable '{y_variable}' "
            "was not found in the dataset."
        )

    if x_variable == y_variable:
        raise ValueError(
            "Predictor and response variables must be different."
        )

    # ---------------------------------------------------------
    # Convert to numeric
    # ---------------------------------------------------------

    data = dataframe[[x_variable, y_variable]].copy()

    data[x_variable] = pd.to_numeric(
        data[x_variable],
        errors="coerce",
    )

    data[y_variable] = pd.to_numeric(
        data[y_variable],
        errors="coerce",
    )

    data = data.dropna()

    if len(data) < 3:
        raise ValueError(
            "At least 3 valid observations are required "
            "for linear regression."
        )

    x = data[x_variable].to_numpy(dtype=float)
    y = data[y_variable].to_numpy(dtype=float)

    # ---------------------------------------------------------
    # Regression
    # ---------------------------------------------------------

    regression = stats.linregress(x, y)

    slope = float(regression.slope)
    intercept = float(regression.intercept)
    r_value = float(regression.rvalue)
    r_squared = float(r_value ** 2)
    p_value = float(regression.pvalue)
    std_error = float(regression.stderr)

    # ---------------------------------------------------------
    # Adjusted R²
    # ---------------------------------------------------------

    n = len(x)
    predictors = 1

    if n > predictors + 1:
        adjusted_r_squared = float(
            1
            - (
                (1 - r_squared)
                * (n - 1)
                / (n - predictors - 1)
            )
        )
    else:
        adjusted_r_squared = None

    # ---------------------------------------------------------
    # Confidence interval for slope
    # ---------------------------------------------------------

    degrees_of_freedom = n - 2

    t_critical = float(
        stats.t.ppf(
            1 - alpha / 2,
            degrees_of_freedom,
        )
    )

    slope_margin = t_critical * std_error

    slope_ci_lower = slope - slope_margin
    slope_ci_upper = slope + slope_margin

    # ---------------------------------------------------------
    # Predictions
    # ---------------------------------------------------------

    predicted = intercept + slope * x

    residuals = y - predicted

    residual_sum_of_squares = float(
        np.sum(residuals ** 2)
    )

    total_sum_of_squares = float(
        np.sum((y - np.mean(y)) ** 2)
    )

    # ---------------------------------------------------------
    # Regression ANOVA
    # ---------------------------------------------------------

    regression_sum_of_squares = float(
        total_sum_of_squares
        - residual_sum_of_squares
    )

    df_regression = 1
    df_residual = n - 2
    df_total = n - 1

    mean_square_regression = (
        regression_sum_of_squares / df_regression
    )

    mean_square_residual = (
        residual_sum_of_squares / df_residual
    )

    f_statistic = (
        mean_square_regression
        / mean_square_residual
    )

    f_p_value = float(
        stats.f.sf(
            f_statistic,
            df_regression,
            df_residual,
        )
    )

    # ---------------------------------------------------------
    # Decision
    # ---------------------------------------------------------

    if p_value < alpha:
        decision = "Reject the null hypothesis."
        significance = (
            f"Statistically significant "
            f"(p < {alpha})."
        )
    else:
        decision = "Fail to reject the null hypothesis."
        significance = (
            f"Not statistically significant "
            f"(p >= {alpha})."
        )

    # ---------------------------------------------------------
    # Regression equation
    # ---------------------------------------------------------

    sign = "+" if intercept >= 0 else "-"

    equation = (
        f"{y_variable} = "
        f"{slope:.6f} × {x_variable} "
        f"{sign} {abs(intercept):.6f}"
    )

    return {
        "test": "Simple Linear Regression",

        "predictor_variable": x_variable,
        "response_variable": y_variable,

        "sample_size": n,

        "regression_equation": equation,

        "coefficients": {
            "intercept": intercept,
            "slope": slope,
        },

        "model_statistics": {
            "r": r_value,
            "r_squared": r_squared,
            "adjusted_r_squared": adjusted_r_squared,
            "standard_error": std_error,
        },

        "anova": {
            "regression": {
                "sum_of_squares": regression_sum_of_squares,
                "degrees_of_freedom": df_regression,
                "mean_square": mean_square_regression,
            },
            "residual": {
                "sum_of_squares": residual_sum_of_squares,
                "degrees_of_freedom": df_residual,
                "mean_square": mean_square_residual,
            },
            "total": {
                "sum_of_squares": total_sum_of_squares,
                "degrees_of_freedom": df_total,
            },
            "f_statistic": float(f_statistic),
            "p_value": f_p_value,
        },

        "slope_inference": {
            "t_statistic": float(
                slope / std_error
            ),
            "p_value": p_value,
            "alpha": alpha,
            "confidence_interval": {
                "lower": float(slope_ci_lower),
                "upper": float(slope_ci_upper),
                "confidence_level": 1 - alpha,
            },
        },

        "null_hypothesis": (
            f"The slope of '{x_variable}' "
            "is equal to zero."
        ),

        "alternative_hypothesis": (
            f"The slope of '{x_variable}' "
            "is not equal to zero."
        ),

        "decision": decision,

        "significance": significance,

        "interpretation": (
            f"The regression model explains "
            f"{r_squared * 100:.2f}% of the variation "
            f"in '{y_variable}'. "
            f"{_interpret_correlation(r_squared)} "
            f"{_interpret_slope(slope)}"
        ),

        "residuals": {
            "mean": float(np.mean(residuals)),
            "sum_of_squared_errors": residual_sum_of_squares,
        },
    }
