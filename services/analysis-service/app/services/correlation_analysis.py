from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr, kendalltau


def interpret_correlation(value: float) -> str:
    """
    Interpret the strength of a correlation coefficient.
    """

    absolute_value = abs(value)

    if absolute_value < 0.10:
        strength = "negligible"
    elif absolute_value < 0.30:
        strength = "weak"
    elif absolute_value < 0.50:
        strength = "moderate"
    elif absolute_value < 0.70:
        strength = "strong"
    elif absolute_value < 0.90:
        strength = "very strong"
    else:
        strength = "extremely strong"

    if value > 0:
        direction = "positive"
    elif value < 0:
        direction = "negative"
    else:
        direction = "no"

    if direction == "no":
        return "There is no linear relationship."

        article = "an" if strength[0].lower() in "aeiou" else "a"

        return f"There is {article} {strength} {direction} relationship."	

def interpret_significance(p_value: float) -> str:
    """
    Interpret statistical significance.
    """

    if p_value < 0.001:
        return "Highly statistically significant (p < 0.001)."

    if p_value < 0.01:
        return "Statistically significant (p < 0.01)."

    if p_value < 0.05:
        return "Statistically significant (p < 0.05)."

    return "Not statistically significant (p >= 0.05)."


def safe_float(value: Any):
    """
    Convert NumPy values into JSON-compatible Python floats.
    """

    if value is None:
        return None

    if isinstance(value, (np.floating, np.integer)):
        value = value.item()

    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            return None

    return value


def calculate_pairwise_correlation(
    dataframe: pd.DataFrame,
    column_x: str,
    column_y: str,
) -> dict[str, Any]:
    """
    Calculate Pearson, Spearman and Kendall correlations
    between two numeric columns.
    """

    pair = dataframe[[column_x, column_y]].copy()

    pair[column_x] = pd.to_numeric(
        pair[column_x],
        errors="coerce",
    )

    pair[column_y] = pd.to_numeric(
        pair[column_y],
        errors="coerce",
    )

    pair = pair.dropna()

    sample_size = len(pair)

    if sample_size < 2:
        raise ValueError(
            f"Not enough valid observations between "
            f"'{column_x}' and '{column_y}'."
        )

    x = pair[column_x]
    y = pair[column_y]

    # ---------------------------------------------------------
    # Check for constant variables
    # ---------------------------------------------------------

    if x.nunique() < 2:
        raise ValueError(
            f"Column '{column_x}' has no variation."
        )

    if y.nunique() < 2:
        raise ValueError(
            f"Column '{column_y}' has no variation."
        )

    # ---------------------------------------------------------
    # Pearson
    # ---------------------------------------------------------

    pearson_result = pearsonr(x, y)

    pearson_r = safe_float(pearson_result.statistic)
    pearson_p = safe_float(pearson_result.pvalue)

    # ---------------------------------------------------------
    # Spearman
    # ---------------------------------------------------------

    spearman_result = spearmanr(x, y)

    spearman_rho = safe_float(
        spearman_result.statistic
    )

    spearman_p = safe_float(
        spearman_result.pvalue
    )

    # ---------------------------------------------------------
    # Kendall
    # ---------------------------------------------------------

    kendall_result = kendalltau(x, y)

    kendall_tau = safe_float(
        kendall_result.statistic
    )

    kendall_p = safe_float(
        kendall_result.pvalue
    )

    # ---------------------------------------------------------
    # Return complete pairwise result
    # ---------------------------------------------------------

    return {
        "variable_x": column_x,
        "variable_y": column_y,
        "sample_size": sample_size,

        "pearson": {
            "coefficient": pearson_r,
            "p_value": pearson_p,
            "interpretation": (
                interpret_correlation(pearson_r)
                if pearson_r is not None
                else None
            ),
            "significance": (
                interpret_significance(pearson_p)
                if pearson_p is not None
                else None
            ),
        },

        "spearman": {
            "coefficient": spearman_rho,
            "p_value": spearman_p,
            "interpretation": (
                interpret_correlation(spearman_rho)
                if spearman_rho is not None
                else None
            ),
            "significance": (
                interpret_significance(spearman_p)
                if spearman_p is not None
                else None
            ),
        },

        "kendall": {
            "coefficient": kendall_tau,
            "p_value": kendall_p,
            "interpretation": (
                interpret_correlation(kendall_tau)
                if kendall_tau is not None
                else None
            ),
            "significance": (
                interpret_significance(kendall_p)
                if kendall_p is not None
                else None
            ),
        },
    }


def calculate_correlation_matrix(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Calculate Pearson, Spearman and Kendall
    correlation matrices for all numeric columns.
    """

    numeric_dataframe = dataframe.select_dtypes(
        include=["number"]
    ).copy()

    numeric_columns = list(
        numeric_dataframe.columns
    )

    if len(numeric_columns) < 2:
        raise ValueError(
            "At least two numeric columns are required "
            "for correlation analysis."
        )

    # ---------------------------------------------------------
    # Pearson matrix
    # ---------------------------------------------------------

    pearson_matrix = numeric_dataframe.corr(
        method="pearson"
    )

    # ---------------------------------------------------------
    # Spearman matrix
    # ---------------------------------------------------------

    spearman_matrix = numeric_dataframe.corr(
        method="spearman"
    )

    # ---------------------------------------------------------
    # Kendall matrix
    # ---------------------------------------------------------

    kendall_matrix = numeric_dataframe.corr(
        method="kendall"
    )

    def matrix_to_dict(matrix):
        result = {}

        for row in matrix.index:
            result[row] = {}

            for column in matrix.columns:
                result[row][column] = safe_float(
                    matrix.loc[row, column]
                )

        return result

    return {
        "variables": numeric_columns,

        "pearson": matrix_to_dict(
            pearson_matrix
        ),

        "spearman": matrix_to_dict(
            spearman_matrix
        ),

        "kendall": matrix_to_dict(
            kendall_matrix
        ),
    }


def analyze_correlation(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Perform complete correlation analysis.

    Includes:
    - Numeric variables
    - Pearson correlation
    - Spearman correlation
    - Kendall correlation
    - Correlation matrix
    - Pairwise analysis
    - Statistical significance
    - Interpretations
    """

    numeric_dataframe = dataframe.select_dtypes(
        include=["number"]
    ).copy()

    numeric_columns = list(
        numeric_dataframe.columns
    )

    if len(numeric_columns) < 2:
        raise ValueError(
            "Correlation analysis requires at least "
            "two numeric columns."
        )

    # ---------------------------------------------------------
    # Correlation matrix
    # ---------------------------------------------------------

    matrix = calculate_correlation_matrix(
        dataframe
    )

    # ---------------------------------------------------------
    # Pairwise correlations
    # ---------------------------------------------------------

    pairwise_results = []

    for i in range(len(numeric_columns)):

        for j in range(i + 1, len(numeric_columns)):

            column_x = numeric_columns[i]
            column_y = numeric_columns[j]

            try:
                result = calculate_pairwise_correlation(
                    dataframe,
                    column_x,
                    column_y,
                )

                pairwise_results.append(result)

            except ValueError:
                continue

    # ---------------------------------------------------------
    # Return results
    # ---------------------------------------------------------

    return {
        "summary": {
            "numeric_column_count": len(
                numeric_columns
            ),
            "numeric_columns": numeric_columns,
            "number_of_pairs": len(
                pairwise_results
            ),
        },

        "correlation_matrix": matrix,

        "pairwise_correlations": pairwise_results,
    }
