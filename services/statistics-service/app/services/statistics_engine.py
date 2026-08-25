import math

import numpy as np
import pandas as pd
from scipy import stats


def clean_number(value):
    if value is None:
        return None

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating, float)):
        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    return value


def numeric_columns(df: pd.DataFrame):
    return df.select_dtypes(include=np.number).columns.tolist()


def descriptive_statistics(df: pd.DataFrame):
    result = {}

    for column in numeric_columns(df):
        series = pd.to_numeric(df[column], errors="coerce").dropna()

        if series.empty:
            continue

        modes = series.mode()

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        result[column] = {
            "count": int(series.count()),
            "missing": int(df[column].isna().sum()),
            "mean": clean_number(series.mean()),
            "median": clean_number(series.median()),
            "mode": clean_number(modes.iloc[0]) if not modes.empty else None,
            "minimum": clean_number(series.min()),
            "maximum": clean_number(series.max()),
            "range": clean_number(series.max() - series.min()),
            "variance": clean_number(series.var(ddof=1)) if len(series) > 1 else None,
            "standard_deviation": (
                clean_number(series.std(ddof=1))
                if len(series) > 1
                else None
            ),
            "q1": clean_number(q1),
            "q3": clean_number(q3),
            "iqr": clean_number(q3 - q1),
            "skewness": (
                clean_number(stats.skew(series, bias=False))
                if len(series) > 2
                else None
            ),
            "kurtosis": (
                clean_number(stats.kurtosis(series, bias=False))
                if len(series) > 3
                else None
            ),
        }

    return result


def correlation_matrix(
    df: pd.DataFrame,
    columns=None,
    method="pearson",
):
    numeric = df.select_dtypes(include=np.number)

    if columns:
        missing = [c for c in columns if c not in numeric.columns]

        if missing:
            raise ValueError(
                "Non-numeric or missing columns: "
                + ", ".join(missing)
            )

        numeric = numeric[columns]

    if numeric.shape[1] < 2:
        raise ValueError(
            "At least two numeric columns are required."
        )

    matrix = numeric.corr(method=method)

    return {
        column: {
            other: clean_number(value)
            for other, value in values.items()
        }
        for column, values in matrix.to_dict().items()
    }


def one_sample_t_test(series, population_mean):
    x = pd.to_numeric(series, errors="coerce").dropna()

    statistic, p_value = stats.ttest_1samp(
        x,
        popmean=population_mean,
    )

    return {
        "test": "One-Sample t-test",
        "sample_size": len(x),
        "sample_mean": clean_number(x.mean()),
        "population_mean": population_mean,
        "t_statistic": clean_number(statistic),
        "p_value": clean_number(p_value),
        "significant_0_05": bool(p_value < 0.05),
    }


def independent_t_test(
    df,
    column,
    group_column,
    group1,
    group2,
):
    x = pd.to_numeric(
        df.loc[df[group_column] == group1, column],
        errors="coerce",
    ).dropna()

    y = pd.to_numeric(
        df.loc[df[group_column] == group2, column],
        errors="coerce",
    ).dropna()

    statistic, p_value = stats.ttest_ind(
        x,
        y,
        equal_var=False,
    )

    return {
        "test": "Independent Samples t-test",
        "group1": str(group1),
        "group2": str(group2),
        "group1_n": len(x),
        "group2_n": len(y),
        "group1_mean": clean_number(x.mean()),
        "group2_mean": clean_number(y.mean()),
        "t_statistic": clean_number(statistic),
        "p_value": clean_number(p_value),
        "significant_0_05": bool(p_value < 0.05),
    }


def paired_t_test(df, column1, column2):
    paired = df[[column1, column2]].apply(
        pd.to_numeric,
        errors="coerce",
    ).dropna()

    statistic, p_value = stats.ttest_rel(
        paired[column1],
        paired[column2],
    )

    return {
        "test": "Paired Samples t-test",
        "sample_size": len(paired),
        "t_statistic": clean_number(statistic),
        "p_value": clean_number(p_value),
        "significant_0_05": bool(p_value < 0.05),
    }


def chi_square_test(df, column1, column2):
    table = pd.crosstab(df[column1], df[column2])

    statistic, p_value, dof, expected = stats.chi2_contingency(
        table
    )

    return {
        "test": "Chi-Square Test of Independence",
        "chi_square": clean_number(statistic),
        "p_value": clean_number(p_value),
        "degrees_of_freedom": int(dof),
        "significant_0_05": bool(p_value < 0.05),
        "observed": table.to_dict(),
        "expected": np.asarray(expected).tolist(),
    }


def shapiro_test(series):
    x = pd.to_numeric(series, errors="coerce").dropna()

    statistic, p_value = stats.shapiro(x)

    return {
        "test": "Shapiro-Wilk Normality Test",
        "sample_size": len(x),
        "w_statistic": clean_number(statistic),
        "p_value": clean_number(p_value),
        "normally_distributed_0_05": bool(p_value > 0.05),
    }


def mann_whitney_test(
    df,
    column,
    group_column,
    group1,
    group2,
):
    x = pd.to_numeric(
        df.loc[df[group_column] == group1, column],
        errors="coerce",
    ).dropna()

    y = pd.to_numeric(
        df.loc[df[group_column] == group2, column],
        errors="coerce",
    ).dropna()

    statistic, p_value = stats.mannwhitneyu(
        x,
        y,
        alternative="two-sided",
    )

    return {
        "test": "Mann-Whitney U Test",
        "u_statistic": clean_number(statistic),
        "p_value": clean_number(p_value),
        "significant_0_05": bool(p_value < 0.05),
    }


def wilcoxon_test(df, column1, column2):
    paired = df[[column1, column2]].apply(
        pd.to_numeric,
        errors="coerce",
    ).dropna()

    statistic, p_value = stats.wilcoxon(
        paired[column1],
        paired[column2],
    )

    return {
        "test": "Wilcoxon Signed-Rank Test",
        "statistic": clean_number(statistic),
        "p_value": clean_number(p_value),
        "significant_0_05": bool(p_value < 0.05),
    }


def kruskal_wallis_test(
    df,
    value_column,
    group_column,
):
    groups = []

    group_names = []

    for group_name, group_df in df.groupby(group_column):
        values = pd.to_numeric(
            group_df[value_column],
            errors="coerce",
        ).dropna()

        if len(values):
            groups.append(values)
            group_names.append(str(group_name))

    if len(groups) < 2:
        raise ValueError(
            "At least two groups are required."
        )

    statistic, p_value = stats.kruskal(*groups)

    return {
        "test": "Kruskal-Wallis H Test",
        "groups": group_names,
        "h_statistic": clean_number(statistic),
        "p_value": clean_number(p_value),
        "significant_0_05": bool(p_value < 0.05),
    }


def one_way_anova(
    df,
    value_column,
    group_column,
):
    groups = []
    group_information = {}

    for group_name, group_df in df.groupby(group_column):
        values = pd.to_numeric(
            group_df[value_column],
            errors="coerce",
        ).dropna()

        if len(values):
            groups.append(values)

            group_information[str(group_name)] = {
                "n": len(values),
                "mean": clean_number(values.mean()),
                "std": (
                    clean_number(values.std(ddof=1))
                    if len(values) > 1
                    else None
                ),
            }

    if len(groups) < 2:
        raise ValueError(
            "ANOVA requires at least two groups."
        )

    statistic, p_value = stats.f_oneway(*groups)

    return {
        "test": "One-Way ANOVA",
        "groups": group_information,
        "f_statistic": clean_number(statistic),
        "p_value": clean_number(p_value),
        "significant_0_05": bool(p_value < 0.05),
    }


def confidence_interval(
    series,
    confidence=0.95,
):
    x = pd.to_numeric(series, errors="coerce").dropna()

    n = len(x)

    if n < 2:
        raise ValueError(
            "At least two observations are required."
        )

    mean = x.mean()
    sem = stats.sem(x)

    interval = stats.t.interval(
        confidence,
        df=n - 1,
        loc=mean,
        scale=sem,
    )

    return {
        "sample_size": n,
        "confidence_level": confidence,
        "mean": clean_number(mean),
        "standard_error": clean_number(sem),
        "lower_bound": clean_number(interval[0]),
        "upper_bound": clean_number(interval[1]),
    }
