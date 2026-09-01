import math

import numpy as np
import pandas as pd
from scipy import stats


# ============================================================
# GENERAL UTILITIES
# ============================================================

def clean_number(value):
    """
    Convert NumPy/Pandas numeric values into
    JSON-safe Python values.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            np.integer,
            int,
        ),
    ):
        return int(value)

    if isinstance(
        value,
        (
            np.floating,
            float,
        ),
    ):
        value = float(value)

        if (
            math.isnan(value)
            or math.isinf(value)
        ):
            return None

        return value

    return value


def numeric_columns(
    df: pd.DataFrame,
):
    """
    Return all numeric columns from the DataFrame.
    """

    return (
        df
        .select_dtypes(
            include=np.number
        )
        .columns
        .tolist()
    )


# ============================================================
# DESCRIPTIVE STATISTICS
# ============================================================

def descriptive_statistics(
    df: pd.DataFrame,
):
    """
    Calculate descriptive statistics for every
    numeric/metric variable in the dataset.

    Used by the SSAS Descriptive / Charts workspace.
    """

    result = {}

    for column in numeric_columns(df):

        series = pd.to_numeric(
            df[column],
            errors="coerce",
        ).dropna()

        if series.empty:
            continue

        count = int(
            series.count()
        )

        missing = int(
            df[column]
            .isna()
            .sum()
        )

        total = int(
            len(df[column])
        )

        modes = series.mode()

        mean = series.mean()

        median = series.median()

        minimum = series.min()

        maximum = series.max()

        total_sum = series.sum()

        q1 = series.quantile(
            0.25
        )

        q2 = series.quantile(
            0.50
        )

        q3 = series.quantile(
            0.75
        )

        data_range = (
            maximum
            - minimum
        )

        iqr = (
            q3
            - q1
        )

        # ----------------------------------------------------
        # Variance / Standard Deviation
        # ----------------------------------------------------

        variance = None
        standard_deviation = None
        standard_error = None

        if count > 1:

            variance = series.var(
                ddof=1
            )

            standard_deviation = (
                series.std(
                    ddof=1
                )
            )

            standard_error = (
                standard_deviation
                / math.sqrt(count)
            )

        # ----------------------------------------------------
        # Median Absolute Deviation
        # ----------------------------------------------------

        median_absolute_deviation = (
            stats.median_abs_deviation(
                series,
                scale=1,
                nan_policy="omit",
            )
        )

        # ----------------------------------------------------
        # Skewness
        # ----------------------------------------------------

        skewness = None

        if count > 2:
            skewness = stats.skew(
                series,
                bias=False,
                nan_policy="omit",
            )

        # ----------------------------------------------------
        # Kurtosis
        # ----------------------------------------------------

        kurtosis = None

        if count > 3:
            kurtosis = stats.kurtosis(
                series,
                bias=False,
                nan_policy="omit",
            )

        # ----------------------------------------------------
        # 95% Confidence Interval for Mean
        # ----------------------------------------------------

        confidence_lower = None
        confidence_upper = None

        if (
            count > 1
            and standard_error is not None
            and standard_error > 0
        ):

            confidence_interval = (
                stats.t.interval(
                    confidence=0.95,
                    df=count - 1,
                    loc=mean,
                    scale=standard_error,
                )
            )

            confidence_lower = (
                confidence_interval[0]
            )

            confidence_upper = (
                confidence_interval[1]
            )

        # ----------------------------------------------------
        # Mean +/- Standard Deviation
        # ----------------------------------------------------

        mean_minus_std = None
        mean_plus_std = None

        if standard_deviation is not None:

            mean_minus_std = (
                mean
                - standard_deviation
            )

            mean_plus_std = (
                mean
                + standard_deviation
            )

        # ----------------------------------------------------
        # Coefficient of Variation
        # ----------------------------------------------------

        coefficient_of_variation = None

        if (
            standard_deviation
            is not None
            and mean != 0
        ):

            coefficient_of_variation = (
                standard_deviation
                / abs(mean)
                * 100
            )

        # ----------------------------------------------------
        # Missing Percentage
        # ----------------------------------------------------

        missing_percent = (
            missing
            / total
            * 100
            if total
            else 0
        )

        # ----------------------------------------------------
        # Build result
        # ----------------------------------------------------

        result[column] = {

            # Number of observations
            "count":
                count,

            "valid_count":
                count,

            "missing":
                missing,

            "missing_percent":
                clean_number(
                    missing_percent
                ),

            # Sum
            "sum":
                clean_number(
                    total_sum
                ),

            # Measures of central tendency
            "mean":
                clean_number(
                    mean
                ),

            "median":
                clean_number(
                    median
                ),

            "mode":
                (
                    clean_number(
                        modes.iloc[0]
                    )
                    if not modes.empty
                    else None
                ),

            # Minimum / Maximum
            "minimum":
                clean_number(
                    minimum
                ),

            "maximum":
                clean_number(
                    maximum
                ),

            "range":
                clean_number(
                    data_range
                ),

            # Dispersion
            "variance":
                (
                    clean_number(
                        variance
                    )
                    if variance
                    is not None
                    else None
                ),

            "standard_deviation":
                (
                    clean_number(
                        standard_deviation
                    )
                    if standard_deviation
                    is not None
                    else None
                ),

            "standard_error":
                (
                    clean_number(
                        standard_error
                    )
                    if standard_error
                    is not None
                    else None
                ),

            # Quartiles
            "q1":
                clean_number(
                    q1
                ),

            "q2":
                clean_number(
                    q2
                ),

            "q3":
                clean_number(
                    q3
                ),

            "iqr":
                clean_number(
                    iqr
                ),

            # Robust dispersion
            "median_absolute_deviation":
                clean_number(
                    median_absolute_deviation
                ),

            # Distribution shape
            "skewness":
                (
                    clean_number(
                        skewness
                    )
                    if skewness
                    is not None
                    else None
                ),

            "kurtosis":
                (
                    clean_number(
                        kurtosis
                    )
                    if kurtosis
                    is not None
                    else None
                ),

            # Confidence Interval
            "confidence_interval_95": {
                "lower":
                    clean_number(
                        confidence_lower
                    ),

                "upper":
                    clean_number(
                        confidence_upper
                    ),
            },

            # Mean +/- SD
            "mean_minus_std":
                (
                    clean_number(
                        mean_minus_std
                    )
                    if mean_minus_std
                    is not None
                    else None
                ),

            "mean_plus_std":
                (
                    clean_number(
                        mean_plus_std
                    )
                    if mean_plus_std
                    is not None
                    else None
                ),

            # Additional useful statistic
            "coefficient_of_variation_percent":
                (
                    clean_number(
                        coefficient_of_variation
                    )
                    if coefficient_of_variation
                    is not None
                    else None
                ),
        }

    return result


# ============================================================
# CORRELATION MATRIX
# ============================================================

def correlation_matrix(
    df: pd.DataFrame,
    columns=None,
    method="pearson",
):
    """
    Calculate Pearson, Spearman, or Kendall
    correlation matrix.
    """

    numeric = (
        df
        .select_dtypes(
            include=np.number
        )
    )

    if columns:

        missing = [
            column
            for column in columns
            if column
            not in numeric.columns
        ]

        if missing:
            raise ValueError(
                "Non-numeric or missing columns: "
                + ", ".join(missing)
            )

        numeric = numeric[
            columns
        ]

    if numeric.shape[1] < 2:
        raise ValueError(
            "At least two numeric columns are required."
        )

    matrix = numeric.corr(
        method=method
    )

    return {
        column: {
            other:
                clean_number(
                    value
                )
            for other, value
            in values.items()
        }
        for column, values
        in matrix.to_dict().items()
    }


# ============================================================
# ONE-SAMPLE T-TEST
# ============================================================

def one_sample_t_test(
    series,
    population_mean,
):
    """
    One-sample t-test.
    """

    x = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if len(x) < 2:
        raise ValueError(
            "At least two observations are required."
        )

    statistic, p_value = (
        stats.ttest_1samp(
            x,
            popmean=population_mean,
        )
    )

    return {
        "test":
            "One-Sample t-test",

        "sample_size":
            len(x),

        "sample_mean":
            clean_number(
                x.mean()
            ),

        "population_mean":
            clean_number(
                population_mean
            ),

        "t_statistic":
            clean_number(
                statistic
            ),

        "p_value":
            clean_number(
                p_value
            ),

        "significant_0_05":
            bool(
                p_value < 0.05
            ),
    }


# ============================================================
# INDEPENDENT SAMPLES T-TEST
# ============================================================

def independent_t_test(
    df,
    column,
    group_column,
    group1,
    group2,
):
    """
    Welch independent samples t-test.
    """

    x = pd.to_numeric(
        df.loc[
            df[group_column]
            == group1,
            column,
        ],
        errors="coerce",
    ).dropna()

    y = pd.to_numeric(
        df.loc[
            df[group_column]
            == group2,
            column,
        ],
        errors="coerce",
    ).dropna()

    if (
        len(x) < 2
        or len(y) < 2
    ):
        raise ValueError(
            "Both groups require at least two observations."
        )

    statistic, p_value = (
        stats.ttest_ind(
            x,
            y,
            equal_var=False,
        )
    )

    return {
        "test":
            "Independent Samples t-test",

        "group1":
            str(group1),

        "group2":
            str(group2),

        "group1_n":
            len(x),

        "group2_n":
            len(y),

        "group1_mean":
            clean_number(
                x.mean()
            ),

        "group2_mean":
            clean_number(
                y.mean()
            ),

        "t_statistic":
            clean_number(
                statistic
            ),

        "p_value":
            clean_number(
                p_value
            ),

        "significant_0_05":
            bool(
                p_value < 0.05
            ),
    }


# ============================================================
# PAIRED SAMPLES T-TEST
# ============================================================

def paired_t_test(
    df,
    column1,
    column2,
):
    """
    Paired samples t-test.
    """

    paired = (
        df[
            [
                column1,
                column2,
            ]
        ]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .dropna()
    )

    if len(paired) < 2:
        raise ValueError(
            "At least two paired observations are required."
        )

    statistic, p_value = (
        stats.ttest_rel(
            paired[column1],
            paired[column2],
        )
    )

    return {
        "test":
            "Paired Samples t-test",

        "sample_size":
            len(paired),

        "mean_difference":
            clean_number(
                (
                    paired[column1]
                    - paired[column2]
                ).mean()
            ),

        "t_statistic":
            clean_number(
                statistic
            ),

        "p_value":
            clean_number(
                p_value
            ),

        "significant_0_05":
            bool(
                p_value < 0.05
            ),
    }


# ============================================================
# CHI-SQUARE TEST OF INDEPENDENCE
# ============================================================

def chi_square_test(
    df,
    column1,
    column2,
):
    """
    Chi-square test of independence.
    """

    table = pd.crosstab(
        df[column1],
        df[column2],
    )

    if table.empty:
        raise ValueError(
            "Unable to create contingency table."
        )

    (
        statistic,
        p_value,
        dof,
        expected,
    ) = stats.chi2_contingency(
        table
    )

    expected_array = (
        np.asarray(
            expected
        )
    )

    cells_below_5 = int(
        (
            expected_array < 5
        ).sum()
    )

    total_cells = int(
        expected_array.size
    )

    percent_below_5 = (
        cells_below_5
        / total_cells
        * 100
        if total_cells
        else 0
    )

    return {
        "test":
            "Chi-Square Test of Independence",

        "chi_square":
            clean_number(
                statistic
            ),

        "p_value":
            clean_number(
                p_value
            ),

        "degrees_of_freedom":
            int(dof),

        "significant_0_05":
            bool(
                p_value < 0.05
            ),

        "observed":
            table.to_dict(),

        "expected":
            expected_array.tolist(),

        "assumptions": {
            "cells_expected_below_5":
                cells_below_5,

            "percent_expected_below_5":
                clean_number(
                    percent_below_5
                ),

            "minimum_expected_frequency":
                clean_number(
                    expected_array.min()
                ),

            "assumption_warning":
                bool(
                    percent_below_5 > 20
                    or
                    expected_array.min() < 1
                ),
        },
    }


# ============================================================
# SHAPIRO-WILK NORMALITY TEST
# ============================================================

def shapiro_test(
    series,
):
    """
    Shapiro-Wilk normality test.
    """

    x = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if len(x) < 3:
        raise ValueError(
            "At least three observations are required."
        )

    warning = None

    test_values = x

    if len(x) > 5000:

        test_values = x.sample(
            n=5000,
            random_state=42,
        )

        warning = (
            "Shapiro-Wilk was calculated "
            "using a reproducible sample of "
            "5,000 observations."
        )

    statistic, p_value = (
        stats.shapiro(
            test_values
        )
    )

    return {
        "test":
            "Shapiro-Wilk Normality Test",

        "sample_size":
            len(x),

        "tested_sample_size":
            len(test_values),

        "w_statistic":
            clean_number(
                statistic
            ),

        "p_value":
            clean_number(
                p_value
            ),

        "normally_distributed_0_05":
            bool(
                p_value > 0.05
            ),

        "warning":
            warning,
    }


# ============================================================
# MANN-WHITNEY U TEST
# ============================================================

def mann_whitney_test(
    df,
    column,
    group_column,
    group1,
    group2,
):
    """
    Mann-Whitney U test for two
    independent groups.
    """

    x = pd.to_numeric(
        df.loc[
            df[group_column]
            == group1,
            column,
        ],
        errors="coerce",
    ).dropna()

    y = pd.to_numeric(
        df.loc[
            df[group_column]
            == group2,
            column,
        ],
        errors="coerce",
    ).dropna()

    if (
        len(x) == 0
        or len(y) == 0
    ):
        raise ValueError(
            "Both groups require observations."
        )

    statistic, p_value = (
        stats.mannwhitneyu(
            x,
            y,
            alternative="two-sided",
        )
    )

    return {
        "test":
            "Mann-Whitney U Test",

        "group1":
            str(group1),

        "group2":
            str(group2),

        "group1_n":
            len(x),

        "group2_n":
            len(y),

        "group1_median":
            clean_number(
                x.median()
            ),

        "group2_median":
            clean_number(
                y.median()
            ),

        "u_statistic":
            clean_number(
                statistic
            ),

        "p_value":
            clean_number(
                p_value
            ),

        "significant_0_05":
            bool(
                p_value < 0.05
            ),
    }


# ============================================================
# WILCOXON SIGNED-RANK TEST
# ============================================================

def wilcoxon_test(
    df,
    column1,
    column2,
):
    """
    Wilcoxon signed-rank test for paired samples.
    """

    paired = (
        df[
            [
                column1,
                column2,
            ]
        ]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .dropna()
    )

    if len(paired) < 1:
        raise ValueError(
            "Paired observations are required."
        )

    statistic, p_value = (
        stats.wilcoxon(
            paired[column1],
            paired[column2],
        )
    )

    return {
        "test":
            "Wilcoxon Signed-Rank Test",

        "sample_size":
            len(paired),

        "statistic":
            clean_number(
                statistic
            ),

        "p_value":
            clean_number(
                p_value
            ),

        "significant_0_05":
            bool(
                p_value < 0.05
            ),
    }


# ============================================================
# KRUSKAL-WALLIS H TEST
# ============================================================

def kruskal_wallis_test(
    df,
    value_column,
    group_column,
):
    """
    Kruskal-Wallis test for more than
    two independent groups.
    """

    groups = []

    group_names = []

    group_information = {}

    for (
        group_name,
        group_df,
    ) in df.groupby(
        group_column
    ):

        values = pd.to_numeric(
            group_df[
                value_column
            ],
            errors="coerce",
        ).dropna()

        if len(values):

            groups.append(
                values
            )

            group_names.append(
                str(group_name)
            )

            group_information[
                str(group_name)
            ] = {
                "n":
                    len(values),

                "median":
                    clean_number(
                        values.median()
                    ),
            }

    if len(groups) < 2:
        raise ValueError(
            "At least two groups are required."
        )

    statistic, p_value = (
        stats.kruskal(
            *groups
        )
    )

    return {
        "test":
            "Kruskal-Wallis H Test",

        "groups":
            group_names,

        "group_statistics":
            group_information,

        "h_statistic":
            clean_number(
                statistic
            ),

        "p_value":
            clean_number(
                p_value
            ),

        "significant_0_05":
            bool(
                p_value < 0.05
            ),
    }


# ============================================================
# ONE-WAY ANOVA
# ============================================================

def one_way_anova(
    df,
    value_column,
    group_column,
):
    """
    One-way Analysis of Variance.
    """

    groups = []

    group_information = {}

    for (
        group_name,
        group_df,
    ) in df.groupby(
        group_column
    ):

        values = pd.to_numeric(
            group_df[
                value_column
            ],
            errors="coerce",
        ).dropna()

        if len(values):

            groups.append(
                values
            )

            group_information[
                str(group_name)
            ] = {
                "n":
                    len(values),

                "mean":
                    clean_number(
                        values.mean()
                    ),

                "std":
                    (
                        clean_number(
                            values.std(
                                ddof=1
                            )
                        )
                        if len(values) > 1
                        else None
                    ),
            }

    if len(groups) < 2:
        raise ValueError(
            "ANOVA requires at least two groups."
        )

    statistic, p_value = (
        stats.f_oneway(
            *groups
        )
    )

    # --------------------------------------------------------
    # Eta squared effect size
    # --------------------------------------------------------

    working = (
        df[
            [
                value_column,
                group_column,
            ]
        ]
        .copy()
    )

    working[
        value_column
    ] = pd.to_numeric(
        working[
            value_column
        ],
        errors="coerce",
    )

    working = (
        working.dropna()
    )

    grand_mean = (
        working[
            value_column
        ]
        .mean()
    )

    ss_between = 0.0
    ss_total = 0.0

    for (
        _,
        group_df,
    ) in working.groupby(
        group_column
    ):

        values = group_df[
            value_column
        ]

        ss_between += (
            len(values)
            * (
                values.mean()
                - grand_mean
            ) ** 2
        )

    ss_total = (
        (
            working[
                value_column
            ]
            - grand_mean
        ) ** 2
    ).sum()

    eta_squared = (
        ss_between
        / ss_total
        if ss_total > 0
        else None
    )

    return {
        "test":
            "One-Way ANOVA",

        "groups":
            group_information,

        "f_statistic":
            clean_number(
                statistic
            ),

        "p_value":
            clean_number(
                p_value
            ),

        "eta_squared":
            (
                clean_number(
                    eta_squared
                )
                if eta_squared
                is not None
                else None
            ),

        "significant_0_05":
            bool(
                p_value < 0.05
            ),
    }


# ============================================================
# CONFIDENCE INTERVAL
# ============================================================

def confidence_interval(
    series,
    confidence=0.95,
):
    """
    Student-t confidence interval for a mean.
    """

    x = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    n = len(x)

    if n < 2:
        raise ValueError(
            "At least two observations are required."
        )

    mean = x.mean()

    standard_deviation = (
        x.std(
            ddof=1
        )
    )

    sem = (
        standard_deviation
        / math.sqrt(n)
    )

    interval = (
        stats.t.interval(
            confidence=confidence,
            df=n - 1,
            loc=mean,
            scale=sem,
        )
    )

    return {
        "sample_size":
            n,

        "confidence_level":
            confidence,

        "mean":
            clean_number(
                mean
            ),

        "standard_deviation":
            clean_number(
                standard_deviation
            ),

        "standard_error":
            clean_number(
                sem
            ),

        "lower_bound":
            clean_number(
                interval[0]
            ),

        "upper_bound":
            clean_number(
                interval[1]
            ),
    }
