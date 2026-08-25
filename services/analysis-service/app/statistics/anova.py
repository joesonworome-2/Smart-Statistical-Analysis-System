from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def _interpret_f_statistic(
    p_value: float,
    alpha: float,
) -> tuple[str, str, str]:
    """
    Generate a statistical decision and interpretation.
    """

    if p_value < alpha:
        decision = "Reject the null hypothesis."
        significance = f"Statistically significant (p < {alpha})."
        interpretation = (
            "There is sufficient evidence to conclude that "
            "at least one group mean is significantly different "
            "from the others."
        )
    else:
        decision = "Fail to reject the null hypothesis."
        significance = f"Not statistically significant (p >= {alpha})."
        interpretation = (
            "There is insufficient evidence to conclude that "
            "the group means are significantly different."
        )

    return decision, significance, interpretation


def _interpret_effect_size(eta_squared: float) -> str:
    """
    Interpret eta-squared effect size.

    Common guideline:
        < 0.01  = negligible
        < 0.06  = small
        < 0.14  = medium
        >= 0.14 = large
    """

    if eta_squared < 0.01:
        return "Negligible effect."
    elif eta_squared < 0.06:
        return "Small effect."
    elif eta_squared < 0.14:
        return "Medium effect."
    else:
        return "Large effect."


def one_way_anova(
    dataframe: pd.DataFrame,
    value_variable: str,
    group_variable: str,
    alpha: float = 0.05,
) -> dict[str, Any]:

    # ---------------------------------------------------------
    # Validate variables
    # ---------------------------------------------------------

    if value_variable not in dataframe.columns:
        raise ValueError(
            f"Variable '{value_variable}' was not found in the dataset."
        )

    if group_variable not in dataframe.columns:
        raise ValueError(
            f"Group variable '{group_variable}' was not found in the dataset."
        )

    if value_variable == group_variable:
        raise ValueError(
            "The value variable and group variable must be different."
        )

    # ---------------------------------------------------------
    # Prepare data
    # ---------------------------------------------------------

    data = dataframe[[value_variable, group_variable]].copy()

    data[value_variable] = pd.to_numeric(
        data[value_variable],
        errors="coerce",
    )

    data = data.dropna()

    if data.empty:
        raise ValueError(
            "No valid observations were found for the selected variables."
        )

    # ---------------------------------------------------------
    # Identify groups
    # ---------------------------------------------------------

    groups = []

    group_names = []

    for group_name, group_data in data.groupby(
        group_variable,
        sort=False,
    ):

        values = group_data[value_variable].to_numpy(
            dtype=float
        )

        if len(values) >= 2:
            groups.append(values)
            group_names.append(str(group_name))

    if len(groups) < 2:
        raise ValueError(
            "One-Way ANOVA requires at least two groups "
            "with at least two observations each."
        )

    # ---------------------------------------------------------
    # Sample sizes
    # ---------------------------------------------------------

    sample_sizes = {
        group_names[index]: int(len(groups[index]))
        for index in range(len(groups))
    }

    # ---------------------------------------------------------
    # Group means
    # ---------------------------------------------------------

    group_means = {
        group_names[index]: float(np.mean(groups[index]))
        for index in range(len(groups))
    }

    # ---------------------------------------------------------
    # Group standard deviations
    # ---------------------------------------------------------

    group_standard_deviations = {
        group_names[index]: float(
            np.std(
                groups[index],
                ddof=1,
            )
        )
        for index in range(len(groups))
    }

    # ---------------------------------------------------------
    # One-Way ANOVA
    # ---------------------------------------------------------

    f_statistic, p_value = stats.f_oneway(
        *groups
    )

    # ---------------------------------------------------------
    # Overall statistics
    # ---------------------------------------------------------

    all_values = np.concatenate(groups)

    total_sample_size = len(all_values)

    overall_mean = float(
        np.mean(all_values)
    )

    number_of_groups = len(groups)

    # ---------------------------------------------------------
    # Degrees of freedom
    # ---------------------------------------------------------

    df_between = number_of_groups - 1

    df_within = total_sample_size - number_of_groups

    df_total = total_sample_size - 1

    # ---------------------------------------------------------
    # Sum of Squares
    # ---------------------------------------------------------

    ss_between = sum(
        len(group)
        * (np.mean(group) - overall_mean) ** 2
        for group in groups
    )

    ss_within = sum(
        np.sum(
            (group - np.mean(group)) ** 2
        )
        for group in groups
    )

    ss_total = ss_between + ss_within

    # ---------------------------------------------------------
    # Mean Squares
    # ---------------------------------------------------------

    ms_between = (
        ss_between / df_between
        if df_between > 0
        else 0.0
    )

    ms_within = (
        ss_within / df_within
        if df_within > 0
        else 0.0
    )

    # ---------------------------------------------------------
    # Eta Squared
    # ---------------------------------------------------------

    eta_squared = (
        ss_between / ss_total
        if ss_total > 0
        else 0.0
    )

    effect_interpretation = _interpret_effect_size(
        eta_squared
    )

    # ---------------------------------------------------------
    # Decision
    # ---------------------------------------------------------

    decision, significance, interpretation = (
        _interpret_f_statistic(
            float(p_value),
            alpha,
        )
    )

    # ---------------------------------------------------------
    # Return result
    # ---------------------------------------------------------

    return {
        "test": "One-Way ANOVA",

        "value_variable": value_variable,

        "group_variable": group_variable,

        "sample_size": total_sample_size,

        "number_of_groups": number_of_groups,

        "groups": group_names,

        "sample_sizes": sample_sizes,

        "group_means": group_means,

        "group_standard_deviations": (
            group_standard_deviations
        ),

        "overall_mean": overall_mean,

        "anova_table": {
            "between_groups": {
                "sum_of_squares": float(
                    ss_between
                ),
                "degrees_of_freedom": int(
                    df_between
                ),
                "mean_square": float(
                    ms_between
                ),
            },

            "within_groups": {
                "sum_of_squares": float(
                    ss_within
                ),
                "degrees_of_freedom": int(
                    df_within
                ),
                "mean_square": float(
                    ms_within
                ),
            },

            "total": {
                "sum_of_squares": float(
                    ss_total
                ),
                "degrees_of_freedom": int(
                    df_total
                ),
            },
        },

        "f_statistic": float(
            f_statistic
        ),

        "p_value": float(
            p_value
        ),

        "alpha": alpha,

        "eta_squared": float(
            eta_squared
        ),

        "effect_size": effect_interpretation,

        "null_hypothesis": (
            "All group means are equal."
        ),

        "alternative_hypothesis": (
            "At least one group mean is different."
        ),

        "decision": decision,

        "significance": significance,

        "interpretation": interpretation,
    }


def tukey_hsd(
    dataframe: pd.DataFrame,
    value_variable: str,
    group_variable: str,
    alpha: float = 0.05,
) -> dict[str, Any]:

    if value_variable not in dataframe.columns:
        raise ValueError(
            f"Variable '{value_variable}' was not found."
        )

    if group_variable not in dataframe.columns:
        raise ValueError(
            f"Group variable '{group_variable}' was not found."
        )

    data = dataframe[
        [value_variable, group_variable]
    ].copy()

    data[value_variable] = pd.to_numeric(
        data[value_variable],
        errors="coerce",
    )

    data = data.dropna()

    if data[group_variable].nunique() < 2:
        raise ValueError(
            "Tukey HSD requires at least two groups."
        )

    result = stats.tukey_hsd(
        *[
            group[value_variable].to_numpy(
                dtype=float
            )
            for _, group in data.groupby(
                group_variable,
                sort=False,
            )
        ]
    )

    groups = [
        str(group_name)
        for group_name in data[
            group_variable
        ].unique()
    ]

    comparisons = []

    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):

            p_value = float(
                result.pvalue[i, j]
            )

            mean_difference = float(
                result.statistic[i, j]
            )

            significant = (
                p_value < alpha
            )

            comparisons.append(
                {
                    "group_1": groups[i],
                    "group_2": groups[j],
                    "mean_difference": mean_difference,
                    "p_value": p_value,
                    "significant": significant,
                    "interpretation": (
                        "Significant difference between "
                        "the two groups."
                        if significant
                        else
                        "No statistically significant "
                        "difference between the two groups."
                    ),
                }
            )

    return {
        "test": "Tukey HSD Post-Hoc Test",

        "value_variable": value_variable,

        "group_variable": group_variable,

        "alpha": alpha,

        "comparisons": comparisons,
    }


def levene_test(
    dataframe: pd.DataFrame,
    value_variable: str,
    group_variable: str,
    alpha: float = 0.05,
) -> dict[str, Any]:

    if value_variable not in dataframe.columns:
        raise ValueError(
            f"Variable '{value_variable}' was not found."
        )

    if group_variable not in dataframe.columns:
        raise ValueError(
            f"Group variable '{group_variable}' was not found."
        )

    data = dataframe[
        [value_variable, group_variable]
    ].copy()

    data[value_variable] = pd.to_numeric(
        data[value_variable],
        errors="coerce",
    )

    data = data.dropna()

    groups = [
        group[value_variable].to_numpy(
            dtype=float
        )
        for _, group in data.groupby(
            group_variable,
            sort=False,
        )
        if len(group) >= 2
    ]

    if len(groups) < 2:
        raise ValueError(
            "Levene's test requires at least two groups."
        )

    statistic, p_value = stats.levene(
        *groups
    )

    if p_value < alpha:
        decision = (
            "Reject the null hypothesis."
        )

        interpretation = (
            "There is evidence that the group "
            "variances are significantly different."
        )

        significance = (
            f"Statistically significant (p < {alpha})."
        )

    else:
        decision = (
            "Fail to reject the null hypothesis."
        )

        interpretation = (
            "There is insufficient evidence to conclude "
            "that the group variances are different."
        )

        significance = (
            f"Not statistically significant (p >= {alpha})."
        )

    return {
        "test": "Levene's Test for Equality of Variances",

        "value_variable": value_variable,

        "group_variable": group_variable,

        "statistic": float(
            statistic
        ),

        "p_value": float(
            p_value
        ),

        "alpha": alpha,

        "null_hypothesis": (
            "The variances of all groups are equal."
        ),

        "alternative_hypothesis": (
            "At least one group has a different variance."
        ),

        "decision": decision,

        "significance": significance,

        "interpretation": interpretation,
    }
