from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


DEFAULT_ALPHA = 0.05


def _decision(p_value: float, alpha: float) -> str:
    if p_value < alpha:
        return "Reject the null hypothesis."
    return "Fail to reject the null hypothesis."


def _significance(p_value: float, alpha: float) -> str:
    if p_value < alpha:
        return f"Statistically significant (p < {alpha})."
    return f"Not statistically significant (p >= {alpha})."


def _interpretation(
    p_value: float,
    alpha: float,
    significant_text: str,
    not_significant_text: str,
) -> str:
    if p_value < alpha:
        return significant_text
    return not_significant_text


def _validate_numeric_column(
    dataframe: pd.DataFrame,
    column: str,
) -> pd.Series:

    if column not in dataframe.columns:
        raise ValueError(
            f"Column '{column}' does not exist in the dataset."
        )

    series = pd.to_numeric(
        dataframe[column],
        errors="coerce",
    ).dropna()

    if len(series) < 2:
        raise ValueError(
            f"Column '{column}' does not contain enough numeric observations."
        )

    return series


# ============================================================
# One-Sample t-test
# ============================================================

def one_sample_t_test(
    dataframe: pd.DataFrame,
    column: str,
    population_mean: float,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:

    series = _validate_numeric_column(dataframe, column)

    statistic, p_value = stats.ttest_1samp(
        series,
        population_mean,
    )

    return {
        "test": "One-Sample t-test",
        "variable": column,
        "sample_size": int(len(series)),
        "sample_mean": float(series.mean()),
        "population_mean": float(population_mean),
        "standard_deviation": float(series.std(ddof=1)),
        "t_statistic": float(statistic),
        "degrees_of_freedom": int(len(series) - 1),
        "p_value": float(p_value),
        "alpha": alpha,
        "null_hypothesis": (
            f"The mean of '{column}' equals {population_mean}."
        ),
        "alternative_hypothesis": (
            f"The mean of '{column}' is different from {population_mean}."
        ),
        "decision": _decision(p_value, alpha),
        "significance": _significance(p_value, alpha),
        "interpretation": _interpretation(
            p_value,
            alpha,
            f"There is sufficient evidence that the mean of "
            f"'{column}' differs from {population_mean}.",
            f"There is insufficient evidence that the mean of "
            f"'{column}' differs from {population_mean}.",
        ),
    }


# ============================================================
# Independent Samples t-test
# ============================================================

def independent_t_test(
    dataframe: pd.DataFrame,
    value_column: str,
    group_column: str,
    group1: Any,
    group2: Any,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:

    if value_column not in dataframe.columns:
        raise ValueError(
            f"Column '{value_column}' does not exist."
        )

    if group_column not in dataframe.columns:
        raise ValueError(
            f"Column '{group_column}' does not exist."
        )

    data = dataframe[
        dataframe[group_column].isin([group1, group2])
    ].copy()

    data[value_column] = pd.to_numeric(
        data[value_column],
        errors="coerce",
    )

    group1_data = data[
        data[group_column] == group1
    ][value_column].dropna()

    group2_data = data[
        data[group_column] == group2
    ][value_column].dropna()

    if len(group1_data) < 2 or len(group2_data) < 2:
        raise ValueError(
            "Each group must contain at least two numeric observations."
        )

    statistic, p_value = stats.ttest_ind(
        group1_data,
        group2_data,
        equal_var=False,
    )

    return {
        "test": "Independent Samples t-test",
        "value_variable": value_column,
        "group_variable": group_column,
        "groups": {
            "group_1": str(group1),
            "group_2": str(group2),
        },
        "sample_sizes": {
            "group_1": int(len(group1_data)),
            "group_2": int(len(group2_data)),
        },
        "means": {
            "group_1": float(group1_data.mean()),
            "group_2": float(group2_data.mean()),
        },
        "standard_deviations": {
            "group_1": float(group1_data.std(ddof=1)),
            "group_2": float(group2_data.std(ddof=1)),
        },
        "t_statistic": float(statistic),
        "p_value": float(p_value),
        "alpha": alpha,
        "null_hypothesis": (
            "The means of the two groups are equal."
        ),
        "alternative_hypothesis": (
            "The means of the two groups are different."
        ),
        "decision": _decision(p_value, alpha),
        "significance": _significance(p_value, alpha),
        "interpretation": _interpretation(
            p_value,
            alpha,
            f"There is sufficient evidence of a difference "
            f"between the means of {group1} and {group2}.",
            f"There is insufficient evidence of a difference "
            f"between the means of {group1} and {group2}.",
        ),
    }


# ============================================================
# Paired Samples t-test
# ============================================================

def paired_t_test(
    dataframe: pd.DataFrame,
    column1: str,
    column2: str,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:

    if column1 not in dataframe.columns:
        raise ValueError(
            f"Column '{column1}' does not exist."
        )

    if column2 not in dataframe.columns:
        raise ValueError(
            f"Column '{column2}' does not exist."
        )

    paired = dataframe[
        [column1, column2]
    ].apply(
        pd.to_numeric,
        errors="coerce",
    ).dropna()

    if len(paired) < 2:
        raise ValueError(
            "At least two complete paired observations are required."
        )

    statistic, p_value = stats.ttest_rel(
        paired[column1],
        paired[column2],
    )

    differences = (
        paired[column1] - paired[column2]
    )

    return {
        "test": "Paired Samples t-test",
        "variables": [
            column1,
            column2,
        ],
        "sample_size": int(len(paired)),
        "means": {
            column1: float(paired[column1].mean()),
            column2: float(paired[column2].mean()),
        },
        "mean_difference": float(differences.mean()),
        "t_statistic": float(statistic),
        "degrees_of_freedom": int(len(paired) - 1),
        "p_value": float(p_value),
        "alpha": alpha,
        "null_hypothesis": (
            "The mean difference between the paired measurements is zero."
        ),
        "alternative_hypothesis": (
            "The mean difference between the paired measurements is not zero."
        ),
        "decision": _decision(p_value, alpha),
        "significance": _significance(p_value, alpha),
        "interpretation": _interpretation(
            p_value,
            alpha,
            f"There is sufficient evidence of a difference "
            f"between '{column1}' and '{column2}'.",
            f"There is insufficient evidence of a difference "
            f"between '{column1}' and '{column2}'.",
        ),
    }


# ============================================================
# One-Way ANOVA
# ============================================================

def one_way_anova(
    dataframe: pd.DataFrame,
    value_column: str,
    group_column: str,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:

    if value_column not in dataframe.columns:
        raise ValueError(
            f"Column '{value_column}' does not exist."
        )

    if group_column not in dataframe.columns:
        raise ValueError(
            f"Column '{group_column}' does not exist."
        )

    data = dataframe[
        [value_column, group_column]
    ].copy()

    data[value_column] = pd.to_numeric(
        data[value_column],
        errors="coerce",
    )

    data = data.dropna()

    groups = []

    group_statistics = {}

    for group_name, group_data in data.groupby(
        group_column
    ):

        values = group_data[value_column]

        if len(values) >= 2:
            groups.append(values)

            group_statistics[str(group_name)] = {
                "sample_size": int(len(values)),
                "mean": float(values.mean()),
                "standard_deviation": float(
                    values.std(ddof=1)
                ),
            }

    if len(groups) < 2:
        raise ValueError(
            "ANOVA requires at least two groups with sufficient observations."
        )

    statistic, p_value = stats.f_oneway(*groups)

    return {
        "test": "One-Way ANOVA",
        "value_variable": value_column,
        "group_variable": group_column,
        "number_of_groups": len(groups),
        "group_statistics": group_statistics,
        "f_statistic": float(statistic),
        "p_value": float(p_value),
        "alpha": alpha,
        "null_hypothesis": (
            "All group means are equal."
        ),
        "alternative_hypothesis": (
            "At least one group mean is different."
        ),
        "decision": _decision(p_value, alpha),
        "significance": _significance(p_value, alpha),
        "interpretation": _interpretation(
            p_value,
            alpha,
            "There is sufficient evidence that at least "
            "one group mean differs from another.",
            "There is insufficient evidence to conclude "
            "that the group means differ.",
        ),
    }


# ============================================================
# Chi-Square Test of Independence
# ============================================================

def chi_square_independence(
    dataframe: pd.DataFrame,
    column1: str,
    column2: str,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:

    if column1 not in dataframe.columns:
        raise ValueError(
            f"Column '{column1}' does not exist."
        )

    if column2 not in dataframe.columns:
        raise ValueError(
            f"Column '{column2}' does not exist."
        )

    data = dataframe[
        [column1, column2]
    ].dropna()

    contingency_table = pd.crosstab(
        data[column1],
        data[column2],
    )

    if contingency_table.shape[0] < 2:
        raise ValueError(
            "The first categorical variable must contain at least two categories."
        )

    if contingency_table.shape[1] < 2:
        raise ValueError(
            "The second categorical variable must contain at least two categories."
        )

    statistic, p_value, degrees_of_freedom, expected = (
        stats.chi2_contingency(
            contingency_table
        )
    )

    return {
        "test": "Chi-Square Test of Independence",
        "variables": [
            column1,
            column2,
        ],
        "sample_size": int(len(data)),
        "contingency_table": contingency_table.to_dict(),
        "chi_square_statistic": float(statistic),
        "degrees_of_freedom": int(degrees_of_freedom),
        "p_value": float(p_value),
        "alpha": alpha,
        "null_hypothesis": (
            f"'{column1}' and '{column2}' are independent."
        ),
        "alternative_hypothesis": (
            f"'{column1}' and '{column2}' are associated."
        ),
        "decision": _decision(p_value, alpha),
        "significance": _significance(p_value, alpha),
        "interpretation": _interpretation(
            p_value,
            alpha,
            f"There is sufficient evidence of an association "
            f"between '{column1}' and '{column2}'.",
            f"There is insufficient evidence of an association "
            f"between '{column1}' and '{column2}'.",
        ),
    }


# ============================================================
# Shapiro-Wilk Normality Test
# ============================================================

def shapiro_normality_test(
    dataframe: pd.DataFrame,
    column: str,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:

    series = _validate_numeric_column(
        dataframe,
        column,
    )

    if len(series) < 3:
        raise ValueError(
            "Shapiro-Wilk requires at least 3 observations."
        )

    statistic, p_value = stats.shapiro(series)

    return {
        "test": "Shapiro-Wilk Normality Test",
        "variable": column,
        "sample_size": int(len(series)),
        "statistic": float(statistic),
        "p_value": float(p_value),
        "alpha": alpha,
        "null_hypothesis": (
            "The data are normally distributed."
        ),
        "alternative_hypothesis": (
            "The data are not normally distributed."
        ),
        "decision": _decision(p_value, alpha),
        "significance": _significance(p_value, alpha),
        "interpretation": _interpretation(
            p_value,
            alpha,
            f"There is evidence that '{column}' is not normally distributed.",
            f"There is insufficient evidence to conclude that "
            f"'{column}' is not normally distributed.",
        ),
    }


# ============================================================
# Mann-Whitney U Test
# ============================================================

def mann_whitney_test(
    dataframe: pd.DataFrame,
    value_column: str,
    group_column: str,
    group1: Any,
    group2: Any,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:

    if value_column not in dataframe.columns:
        raise ValueError(
            f"Column '{value_column}' does not exist."
        )

    if group_column not in dataframe.columns:
        raise ValueError(
            f"Column '{group_column}' does not exist."
        )

    data = dataframe[
        dataframe[group_column].isin(
            [group1, group2]
        )
    ].copy()

    data[value_column] = pd.to_numeric(
        data[value_column],
        errors="coerce",
    )

    group1_data = data[
        data[group_column] == group1
    ][value_column].dropna()

    group2_data = data[
        data[group_column] == group2
    ][value_column].dropna()

    if len(group1_data) < 1 or len(group2_data) < 1:
        raise ValueError(
            "Both groups must contain observations."
        )

    statistic, p_value = stats.mannwhitneyu(
        group1_data,
        group2_data,
        alternative="two-sided",
    )

    return {
        "test": "Mann-Whitney U Test",
        "value_variable": value_column,
        "group_variable": group_column,
        "groups": {
            "group_1": str(group1),
            "group_2": str(group2),
        },
        "sample_sizes": {
            "group_1": int(len(group1_data)),
            "group_2": int(len(group2_data)),
        },
        "medians": {
            "group_1": float(group1_data.median()),
            "group_2": float(group2_data.median()),
        },
        "u_statistic": float(statistic),
        "p_value": float(p_value),
        "alpha": alpha,
        "null_hypothesis": (
            "The two groups come from the same distribution."
        ),
        "alternative_hypothesis": (
            "The two groups come from different distributions."
        ),
        "decision": _decision(p_value, alpha),
        "significance": _significance(p_value, alpha),
    }


# ============================================================
# Wilcoxon Signed-Rank Test
# ============================================================

def wilcoxon_test(
    dataframe: pd.DataFrame,
    column1: str,
    column2: str,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:

    if column1 not in dataframe.columns:
        raise ValueError(
            f"Column '{column1}' does not exist."
        )

    if column2 not in dataframe.columns:
        raise ValueError(
            f"Column '{column2}' does not exist."
        )

    paired = dataframe[
        [column1, column2]
    ].apply(
        pd.to_numeric,
        errors="coerce",
    ).dropna()

    if len(paired) < 2:
        raise ValueError(
            "At least two paired observations are required."
        )

    statistic, p_value = stats.wilcoxon(
        paired[column1],
        paired[column2],
    )

    return {
        "test": "Wilcoxon Signed-Rank Test",
        "variables": [
            column1,
            column2,
        ],
        "sample_size": int(len(paired)),
        "statistic": float(statistic),
        "p_value": float(p_value),
        "alpha": alpha,
        "null_hypothesis": (
            "The median difference between the paired measurements is zero."
        ),
        "alternative_hypothesis": (
            "The median difference between the paired measurements is not zero."
        ),
        "decision": _decision(p_value, alpha),
        "significance": _significance(p_value, alpha),
    }


# ============================================================
# Kruskal-Wallis Test
# ============================================================

def kruskal_wallis_test(
    dataframe: pd.DataFrame,
    value_column: str,
    group_column: str,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:

    if value_column not in dataframe.columns:
        raise ValueError(
            f"Column '{value_column}' does not exist."
        )

    if group_column not in dataframe.columns:
        raise ValueError(
            f"Column '{group_column}' does not exist."
        )

    data = dataframe[
        [value_column, group_column]
    ].copy()

    data[value_column] = pd.to_numeric(
        data[value_column],
        errors="coerce",
    )

    data = data.dropna()

    groups = []

    for _, group_data in data.groupby(
        group_column
    ):
        values = group_data[value_column]

        if len(values) >= 1:
            groups.append(values)

    if len(groups) < 2:
        raise ValueError(
            "Kruskal-Wallis requires at least two groups."
        )

    statistic, p_value = stats.kruskal(
        *groups
    )

    return {
        "test": "Kruskal-Wallis Test",
        "value_variable": value_column,
        "group_variable": group_column,
        "number_of_groups": len(groups),
        "h_statistic": float(statistic),
        "p_value": float(p_value),
        "alpha": alpha,
        "null_hypothesis": (
            "The distributions of all groups are the same."
        ),
        "alternative_hypothesis": (
            "At least one group has a different distribution."
        ),
        "decision": _decision(p_value, alpha),
        "significance": _significance(p_value, alpha),
    }
