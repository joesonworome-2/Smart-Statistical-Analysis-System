from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


# ============================================================
# Utility functions
# ============================================================

def _safe_float(value):
    if value is None:
        return None

    value = float(value)

    if np.isnan(value) or np.isinf(value):
        return None

    return value


def _prepare_regression_data(
    dataframe: pd.DataFrame,
    response_variable: str,
    predictor_variables: list[str],
):
    """
    Validate and prepare regression variables.
    """

    if not predictor_variables:
        raise ValueError(
            "At least one predictor variable is required."
        )

    if response_variable in predictor_variables:
        raise ValueError(
            "The response variable cannot also be a predictor."
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

    data = dataframe[variables].copy()

    for variable in variables:
        data[variable] = pd.to_numeric(
            data[variable],
            errors="coerce",
        )

    original_rows = len(data)

    data = data.dropna()

    removed_rows = original_rows - len(data)

    if len(data) < 4:
        raise ValueError(
            "At least four complete observations are required "
            "for regression diagnostics."
        )

    return data, removed_rows


def _fit_ols(
    dataframe: pd.DataFrame,
    response_variable: str,
    predictor_variables: list[str],
):
    """
    Fit an Ordinary Least Squares model using NumPy.
    """

    X = dataframe[
        predictor_variables
    ].to_numpy(dtype=float)

    y = dataframe[
        response_variable
    ].to_numpy(dtype=float)

    X_design = np.column_stack(
        [
            np.ones(len(X)),
            X,
        ]
    )

    coefficients, _, rank, singular_values = np.linalg.lstsq(
        X_design,
        y,
        rcond=None,
    )

    predictions = (
        X_design @ coefficients
    )

    residuals = (
        y - predictions
    )

    return {
        "X": X,
        "X_design": X_design,
        "y": y,
        "coefficients": coefficients,
        "predictions": predictions,
        "residuals": residuals,
        "rank": rank,
        "singular_values": singular_values,
    }


# ============================================================
# Residual summary
# ============================================================

def residual_summary(
    residuals: np.ndarray,
) -> dict[str, Any]:

    count = len(residuals)

    mean = np.mean(residuals)

    std = (
        np.std(residuals, ddof=1)
        if count > 1
        else 0
    )

    return {
        "count": int(count),

        "mean": _safe_float(mean),

        "standard_deviation": _safe_float(std),

        "minimum": _safe_float(
            np.min(residuals)
        ),

        "maximum": _safe_float(
            np.max(residuals)
        ),

        "median": _safe_float(
            np.median(residuals)
        ),

        "q1": _safe_float(
            np.quantile(
                residuals,
                0.25,
            )
        ),

        "q3": _safe_float(
            np.quantile(
                residuals,
                0.75,
            )
        ),

        "sum": _safe_float(
            np.sum(residuals)
        ),

        "sum_of_squared_residuals": _safe_float(
            np.sum(
                residuals ** 2
            )
        ),
    }


# ============================================================
# Standardized residuals and outliers
# ============================================================

def standardized_residual_analysis(
    residuals: np.ndarray,
) -> dict[str, Any]:

    residual_std = np.std(
        residuals,
        ddof=1,
    )

    if residual_std == 0:
        standardized = np.zeros(
            len(residuals)
        )
    else:
        standardized = (
            residuals
            / residual_std
        )

    outliers_2 = []

    outliers_3 = []

    values = []

    for index, value in enumerate(
        standardized
    ):
        value = float(value)

        values.append(
            {
                "observation": index + 1,
                "standardized_residual": value,
            }
        )

        if abs(value) > 2:
            outliers_2.append(
                {
                    "observation": index + 1,
                    "standardized_residual": value,
                }
            )

        if abs(value) > 3:
            outliers_3.append(
                {
                    "observation": index + 1,
                    "standardized_residual": value,
                }
            )

    return {
        "standardized_residuals": values,

        "potential_outliers_above_2": (
            outliers_2
        ),

        "extreme_outliers_above_3": (
            outliers_3
        ),

        "outlier_count_above_2": len(
            outliers_2
        ),

        "outlier_count_above_3": len(
            outliers_3
        ),
    }


# ============================================================
# Shapiro-Wilk normality test
# ============================================================

def residual_normality_test(
    residuals: np.ndarray,
    alpha: float = 0.05,
) -> dict[str, Any]:

    if len(residuals) < 3:
        raise ValueError(
            "At least three residual observations "
            "are required for Shapiro-Wilk."
        )

    statistic, p_value = stats.shapiro(
        residuals
    )

    if p_value < alpha:
        decision = (
            "Reject the null hypothesis."
        )

        interpretation = (
            "The residuals show evidence of "
            "departing from normality."
        )

        assumption_met = False

    else:
        decision = (
            "Fail to reject the null hypothesis."
        )

        interpretation = (
            "There is insufficient evidence to "
            "conclude that the residuals are "
            "not normally distributed."
        )

        assumption_met = True

    return {
        "test": (
            "Shapiro-Wilk Residual "
            "Normality Test"
        ),

        "statistic": float(
            statistic
        ),

        "p_value": float(
            p_value
        ),

        "alpha": alpha,

        "null_hypothesis": (
            "The regression residuals are "
            "normally distributed."
        ),

        "alternative_hypothesis": (
            "The regression residuals are "
            "not normally distributed."
        ),

        "decision": decision,

        "assumption_met": assumption_met,

        "interpretation": interpretation,
    }


# ============================================================
# Breusch-Pagan style homoscedasticity test
# ============================================================

def breusch_pagan_test(
    residuals: np.ndarray,
    predictor_matrix: np.ndarray,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """
    Basic Breusch-Pagan implementation.

    Regress squared residuals against predictors.

    LM statistic = n * auxiliary R²
    """

    n = len(residuals)

    if n < 4:
        raise ValueError(
            "Not enough observations for "
            "heteroscedasticity testing."
        )

    squared_residuals = (
        residuals ** 2
    )

    X_aux = np.column_stack(
        [
            np.ones(n),
            predictor_matrix,
        ]
    )

    auxiliary_coefficients, _, _, _ = (
        np.linalg.lstsq(
            X_aux,
            squared_residuals,
            rcond=None,
        )
    )

    predicted_squared = (
        X_aux
        @ auxiliary_coefficients
    )

    ss_residual = np.sum(
        (
            squared_residuals
            - predicted_squared
        ) ** 2
    )

    ss_total = np.sum(
        (
            squared_residuals
            - np.mean(squared_residuals)
        ) ** 2
    )

    if ss_total == 0:
        auxiliary_r_squared = 0.0

    else:
        auxiliary_r_squared = (
            1
            - (
                ss_residual
                / ss_total
            )
        )

    lm_statistic = (
        n
        * auxiliary_r_squared
    )

    degrees_of_freedom = (
        predictor_matrix.shape[1]
    )

    p_value = stats.chi2.sf(
        lm_statistic,
        degrees_of_freedom,
    )

    if p_value < alpha:
        decision = (
            "Reject the null hypothesis."
        )

        interpretation = (
            "There is evidence of "
            "heteroscedasticity."
        )

        assumption_met = False

    else:
        decision = (
            "Fail to reject the null hypothesis."
        )

        interpretation = (
            "There is insufficient evidence "
            "of heteroscedasticity."
        )

        assumption_met = True

    return {
        "test": (
            "Breusch-Pagan "
            "Homoscedasticity Test"
        ),

        "lm_statistic": float(
            lm_statistic
        ),

        "degrees_of_freedom": int(
            degrees_of_freedom
        ),

        "p_value": float(
            p_value
        ),

        "alpha": alpha,

        "null_hypothesis": (
            "The residual variance is constant "
            "(homoscedasticity)."
        ),

        "alternative_hypothesis": (
            "The residual variance is not "
            "constant (heteroscedasticity)."
        ),

        "decision": decision,

        "assumption_met": assumption_met,

        "interpretation": interpretation,
    }


# ============================================================
# VIF
# ============================================================

def calculate_vif(
    dataframe: pd.DataFrame,
    predictor_variables: list[str],
) -> dict[str, Any]:

    if len(predictor_variables) < 2:
        return {
            "available": False,
            "message": (
                "VIF requires at least two "
                "predictor variables."
            ),
            "variables": {},
        }

    X = dataframe[
        predictor_variables
    ].to_numpy(dtype=float)

    vif_results = {}

    for target_index, variable in enumerate(
        predictor_variables
    ):

        y_target = X[
            :,
            target_index
        ]

        other_indexes = [
            index
            for index in range(
                len(predictor_variables)
            )
            if index != target_index
        ]

        X_other = X[
            :,
            other_indexes
        ]

        X_design = np.column_stack(
            [
                np.ones(len(X_other)),
                X_other,
            ]
        )

        coefficients, _, _, _ = np.linalg.lstsq(
            X_design,
            y_target,
            rcond=None,
        )

        predicted = (
            X_design
            @ coefficients
        )

        ss_residual = np.sum(
            (
                y_target
                - predicted
            ) ** 2
        )

        ss_total = np.sum(
            (
                y_target
                - np.mean(y_target)
            ) ** 2
        )

        if ss_total == 0:
            r_squared = 1.0

        else:
            r_squared = (
                1
                - (
                    ss_residual
                    / ss_total
                )
            )

        denominator = (
            1
            - r_squared
        )

        if denominator <= 1e-12:
            vif = float("inf")

        else:
            vif = (
                1
                / denominator
            )

        if np.isinf(vif):
            interpretation = (
                "Severe multicollinearity."
            )

        elif vif >= 10:
            interpretation = (
                "High multicollinearity."
            )

        elif vif >= 5:
            interpretation = (
                "Moderate multicollinearity."
            )

        else:
            interpretation = (
                "Acceptable multicollinearity."
            )

        vif_results[
            variable
        ] = {
            "r_squared_against_other_predictors": (
                _safe_float(
                    r_squared
                )
            ),

            "vif": (
                None
                if np.isinf(vif)
                else float(vif)
            ),

            "is_infinite": bool(
                np.isinf(vif)
            ),

            "interpretation": interpretation,
        }

    return {
        "available": True,
        "variables": vif_results,
    }


# ============================================================
# Predictor correlations
# ============================================================

def predictor_correlation_analysis(
    dataframe: pd.DataFrame,
    predictor_variables: list[str],
) -> dict[str, Any]:

    if len(predictor_variables) < 2:
        return {
            "available": False,
            "correlations": {},
        }

    correlation_matrix = dataframe[
        predictor_variables
    ].corr(
        method="pearson"
    )

    matrix = {}

    high_correlations = []

    for row in correlation_matrix.index:

        matrix[row] = {}

        for column in correlation_matrix.columns:

            value = float(
                correlation_matrix.loc[
                    row,
                    column,
                ]
            )

            matrix[row][
                column
            ] = value

    for i in range(
        len(predictor_variables)
    ):

        for j in range(
            i + 1,
            len(predictor_variables)
        ):

            variable_1 = (
                predictor_variables[i]
            )

            variable_2 = (
                predictor_variables[j]
            )

            correlation = float(
                correlation_matrix.loc[
                    variable_1,
                    variable_2,
                ]
            )

            if abs(correlation) >= 0.8:

                high_correlations.append(
                    {
                        "variable_1": variable_1,
                        "variable_2": variable_2,
                        "correlation": correlation,
                        "warning": (
                            "Strong predictor "
                            "correlation detected."
                        ),
                    }
                )

    return {
        "available": True,

        "correlation_matrix": matrix,

        "high_correlations": (
            high_correlations
        ),
    }


# ============================================================
# Complete diagnostics
# ============================================================

def analyze_regression_diagnostics(
    dataframe: pd.DataFrame,
    response_variable: str,
    predictor_variables: list[str],
    alpha: float = 0.05,
) -> dict[str, Any]:

    if not 0 < alpha < 1:
        raise ValueError(
            "Alpha must be between 0 and 1."
        )

    data, removed_rows = (
        _prepare_regression_data(
            dataframe,
            response_variable,
            predictor_variables,
        )
    )

    fitted = _fit_ols(
        data,
        response_variable,
        predictor_variables,
    )

    residuals = fitted[
        "residuals"
    ]

    predictions = fitted[
        "predictions"
    ]

    X = fitted[
        "X"
    ]

    # ---------------------------------------------------------
    # Individual diagnostics
    # ---------------------------------------------------------

    residual_results = residual_summary(
        residuals
    )

    standardized_results = (
        standardized_residual_analysis(
            residuals
        )
    )

    normality_results = (
        residual_normality_test(
            residuals,
            alpha,
        )
    )

    homoscedasticity_results = (
        breusch_pagan_test(
            residuals,
            X,
            alpha,
        )
    )

    vif_results = calculate_vif(
        data,
        predictor_variables,
    )

    predictor_correlations = (
        predictor_correlation_analysis(
            data,
            predictor_variables,
        )
    )

    # ---------------------------------------------------------
    # Overall assumption status
    # ---------------------------------------------------------

    warnings = []

    if not normality_results[
        "assumption_met"
    ]:
        warnings.append(
            "Residual normality assumption "
            "may be violated."
        )

    if not homoscedasticity_results[
        "assumption_met"
    ]:
        warnings.append(
            "Homoscedasticity assumption "
            "may be violated."
        )

    if (
        standardized_results[
            "outlier_count_above_3"
        ]
        > 0
    ):
        warnings.append(
            "Extreme standardized residual "
            "outliers were detected."
        )

    elif (
        standardized_results[
            "outlier_count_above_2"
        ]
        > 0
    ):
        warnings.append(
            "Potential residual outliers "
            "were detected."
        )

    if vif_results[
        "available"
    ]:

        for (
            variable,
            vif_information,
        ) in vif_results[
            "variables"
        ].items():

            if (
                vif_information[
                    "is_infinite"
                ]
                or (
                    vif_information[
                        "vif"
                    ]
                    is not None
                    and vif_information[
                        "vif"
                    ]
                    >= 5
                )
            ):

                warnings.append(
                    f"Potential multicollinearity "
                    f"detected for '{variable}'."
                )

    assumptions_met = (
        len(warnings) == 0
    )

    # ---------------------------------------------------------
    # Prediction / residual table
    # ---------------------------------------------------------

    observations = []

    residual_std = np.std(
        residuals,
        ddof=1,
    )

    for index in range(
        len(data)
    ):

        standardized = (
            residuals[index]
            / residual_std
            if residual_std != 0
            else 0
        )

        observations.append(
            {
                "observation": index + 1,

                "actual": float(
                    fitted[
                        "y"
                    ][index]
                ),

                "predicted": float(
                    predictions[index]
                ),

                "residual": float(
                    residuals[index]
                ),

                "standardized_residual": float(
                    standardized
                ),
            }
        )

    # ---------------------------------------------------------
    # Final response
    # ---------------------------------------------------------

    return {
        "analysis": (
            "Regression Diagnostics "
            "and Assumption Testing"
        ),

        "response_variable": (
            response_variable
        ),

        "predictor_variables": (
            predictor_variables
        ),

        "sample_information": {
            "complete_observations": int(
                len(data)
            ),

            "rows_removed_due_to_missing_values": (
                int(removed_rows)
            ),
        },

        "residual_summary": (
            residual_results
        ),

        "normality_test": (
            normality_results
        ),

        "homoscedasticity_test": (
            homoscedasticity_results
        ),

        "outlier_analysis": (
            standardized_results
        ),

        "multicollinearity": {
            "vif": vif_results,

            "predictor_correlations": (
                predictor_correlations
            ),
        },

        "observations": observations,

        "assumption_summary": {
            "all_checked_assumptions_met": (
                assumptions_met
            ),

            "warning_count": len(
                warnings
            ),

            "warnings": warnings,

            "interpretation": (
                "No major regression assumption "
                "violations were detected."
                if assumptions_met
                else
                "One or more potential regression "
                "assumption issues were detected. "
                "Review the warnings before "
                "interpreting the model."
            ),
        },
    }
