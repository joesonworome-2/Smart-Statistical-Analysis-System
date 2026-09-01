import math

import numpy as np
import pandas as pd
from scipy import stats


# ============================================================
# Utility functions
# ============================================================

def clean_number(value):
    if value is None:
        return None

    if isinstance(
        value,
        (np.integer,),
    ):
        return int(value)

    if isinstance(
        value,
        (np.floating, float),
    ):
        value = float(value)

        if (
            math.isnan(value)
            or math.isinf(value)
        ):
            return None

        return value

    return value


def require_columns(
    df: pd.DataFrame,
    columns: list[str],
):
    missing = [
        column
        for column in columns
        if (
            column
            and column not in df.columns
        )
    ]

    if missing:
        raise ValueError(
            "Unknown columns: "
            + ", ".join(missing)
        )


def numeric_series(
    df: pd.DataFrame,
    column: str,
):
    if column not in df.columns:
        raise ValueError(
            f"Unknown column: {column}"
        )

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        raise ValueError(
            f"{column} contains no usable "
            "numeric observations."
        )

    return values


# ============================================================
# VARIABLE PROFILING
# ============================================================

def infer_variable(
    series: pd.Series,
):
    total = len(series)

    non_missing = series.dropna()

    missing = int(
        series.isna().sum()
    )

    unique = int(
        non_missing.nunique()
    )

    missing_percent = (
        missing / total * 100
        if total
        else 0
    )

    # --------------------------------------------------------
    # Boolean
    # --------------------------------------------------------

    if pd.api.types.is_bool_dtype(
        series
    ):
        return {
            "data_type": "boolean",
            "measurement_level":
                "nominal",
            "confidence":
                "high",
            "reason":
                "Boolean variables represent "
                "categories.",
            "missing_count":
                missing,
            "missing_percent":
                round(
                    missing_percent,
                    2,
                ),
            "unique_count":
                unique,
        }

    # --------------------------------------------------------
    # Date / time
    # --------------------------------------------------------

    if pd.api.types.is_datetime64_any_dtype(
        series
    ):
        return {
            "data_type":
                "datetime",
            "measurement_level":
                "metric",
            "confidence":
                "high",
            "reason":
                "Date/time values are ordered "
                "and measurable.",
            "missing_count":
                missing,
            "missing_percent":
                round(
                    missing_percent,
                    2,
                ),
            "unique_count":
                unique,
        }

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    if pd.api.types.is_numeric_dtype(
        series
    ):
        # Numeric binary variables
        if unique <= 2:
            level = "nominal"

            reason = (
                "Numeric variable has only "
                "two unique values."
            )

            confidence = "medium"

        else:
            level = "metric"

            reason = (
                "Numeric variable with "
                "multiple values."
            )

            confidence = "high"

        profile = {
            "data_type":
                "numeric",
            "measurement_level":
                level,
            "confidence":
                confidence,
            "reason":
                reason,
            "missing_count":
                missing,
            "missing_percent":
                round(
                    missing_percent,
                    2,
                ),
            "unique_count":
                unique,
        }

        if (
            unique >= 3
            and unique <= 10
        ):
            profile[
                "possible_alternative"
            ] = "ordinal"

            profile[
                "note"
            ] = (
                "This numeric variable has "
                "relatively few unique "
                "values. Check whether it "
                "represents an ordered scale."
            )

        return profile

    # --------------------------------------------------------
    # Text / categorical
    # --------------------------------------------------------

    unique_ratio = (
        unique / len(non_missing)
        if len(non_missing)
        else 0
    )

    if (
        unique <= 20
        or unique_ratio <= 0.20
    ):
        return {
            "data_type":
                "categorical",
            "measurement_level":
                "nominal",
            "confidence":
                "medium",
            "reason":
                "Text variable has a "
                "limited set of repeated "
                "categories.",
            "missing_count":
                missing,
            "missing_percent":
                round(
                    missing_percent,
                    2,
                ),
            "unique_count":
                unique,
        }

    return {
        "data_type":
            "text",
        "measurement_level":
            "nominal",
        "confidence":
            "low",
        "reason":
            "High-cardinality text variable. "
            "Review manually before using it "
            "in statistical analysis.",
        "missing_count":
            missing,
        "missing_percent":
            round(
                missing_percent,
                2,
            ),
        "unique_count":
            unique,
    }


def variable_profiles(
    df: pd.DataFrame,
):
    profiles = []

    for column in df.columns:
        information = infer_variable(
            df[column]
        )

        profiles.append(
            {
                "name":
                    column,
                "pandas_dtype":
                    str(
                        df[column].dtype
                    ),
                **information,
            }
        )

    return profiles


# ============================================================
# FREQUENCY TABLES
# ============================================================

def frequency_table(
    df: pd.DataFrame,
    column: str,
):
    require_columns(
        df,
        [column],
    )

    series = df[column]

    total_count = len(series)

    missing_count = int(
        series.isna().sum()
    )

    valid = series.dropna()

    valid_count = len(valid)

    counts = (
        valid
        .value_counts(
            dropna=False
        )
    )

    rows = []

    cumulative = 0.0

    for value, count in counts.items():
        count = int(count)

        percent = (
            count
            / total_count
            * 100
            if total_count
            else 0
        )

        valid_percent = (
            count
            / valid_count
            * 100
            if valid_count
            else 0
        )

        cumulative += (
            valid_percent
        )

        rows.append(
            {
                "value":
                    (
                        value.item()
                        if isinstance(
                            value,
                            np.generic,
                        )
                        else value
                    ),
                "count":
                    count,
                "percent":
                    round(
                        percent,
                        2,
                    ),
                "valid_percent":
                    round(
                        valid_percent,
                        2,
                    ),
                "cumulative_percent":
                    round(
                        cumulative,
                        2,
                    ),
            }
        )

    return {
        "column":
            column,
        "total_count":
            total_count,
        "valid_count":
            valid_count,
        "missing_count":
            missing_count,
        "frequencies":
            rows,
    }


# ============================================================
# NORMALITY TESTING
# ============================================================

def normality_tests(
    series,
    methods=None,
    alpha=0.05,
):
    x = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if len(x) < 3:
        raise ValueError(
            "At least three numeric "
            "observations are required."
        )

    if methods is None:
        methods = [
            "shapiro",
            "anderson",
            "ks",
        ]

    result = {
        "sample_size":
            len(x),
        "alpha":
            alpha,
        "tests":
            {},
        "warnings":
            [],
    }

    # --------------------------------------------------------
    # Shapiro-Wilk
    # --------------------------------------------------------

    if "shapiro" in methods:
        shapiro_values = x

        if len(x) > 5000:
            shapiro_values = x.sample(
                n=5000,
                random_state=42,
            )

            result[
                "warnings"
            ].append(
                "Shapiro-Wilk used a "
                "reproducible sample of "
                "5,000 observations because "
                "very large samples can make "
                "its p-value unreliable."
            )

        statistic, p_value = (
            stats.shapiro(
                shapiro_values
            )
        )

        result["tests"][
            "shapiro_wilk"
        ] = {
            "statistic":
                clean_number(
                    statistic
                ),
            "p_value":
                clean_number(
                    p_value
                ),
            "normal":
                bool(
                    p_value > alpha
                ),
        }

    # --------------------------------------------------------
    # Anderson-Darling
    # --------------------------------------------------------

    if "anderson" in methods:
        anderson = stats.anderson(
            x,
            dist="norm",
        )

        critical_values = {
            str(level):
                clean_number(
                    value
                )
            for level, value
            in zip(
                anderson
                .significance_level,
                anderson
                .critical_values,
            )
        }

        normal_at_5 = None

        index_5 = np.argmin(
            np.abs(
                anderson
                .significance_level
                - 5
            )
        )

        normal_at_5 = bool(
            anderson.statistic
            <
            anderson
            .critical_values[
                index_5
            ]
        )

        result["tests"][
            "anderson_darling"
        ] = {
            "statistic":
                clean_number(
                    anderson
                    .statistic
                ),
            "critical_values":
                critical_values,
            "normal_at_5_percent":
                normal_at_5,
        }

    # --------------------------------------------------------
    # Kolmogorov-Smirnov
    # --------------------------------------------------------

    if "ks" in methods:
        standard_deviation = (
            x.std(
                ddof=1
            )
        )

        if (
            standard_deviation
            == 0
            or np.isnan(
                standard_deviation
            )
        ):
            result[
                "tests"
            ][
                "kolmogorov_smirnov"
            ] = {
                "available":
                    False,
                "reason":
                    (
                        "The variable has "
                        "zero variance."
                    ),
            }

        else:
            standardized = (
                x - x.mean()
            ) / standard_deviation

            statistic, p_value = (
                stats.kstest(
                    standardized,
                    "norm",
                )
            )

            result[
                "tests"
            ][
                "kolmogorov_smirnov"
            ] = {
                "statistic":
                    clean_number(
                        statistic
                    ),
                "p_value":
                    clean_number(
                        p_value
                    ),
                "normal":
                    bool(
                        p_value
                        > alpha
                    ),
                "note":
                    (
                        "Normal parameters "
                        "were estimated from "
                        "the sample; interpret "
                        "this KS result as an "
                        "approximate diagnostic."
                    ),
            }

    return result


# ============================================================
# EFFECT SIZE
# ============================================================

def magnitude_from_d(
    value,
):
    absolute = abs(value)

    if absolute < 0.2:
        return "negligible"

    if absolute < 0.5:
        return "small"

    if absolute < 0.8:
        return "medium"

    return "large"


def correlation_magnitude(
    value,
):
    absolute = abs(value)

    if absolute < 0.1:
        return "negligible"

    if absolute < 0.3:
        return "small"

    if absolute < 0.5:
        return "moderate"

    return "large"


def independent_effect_size(
    df,
    column,
    group_column,
    group1,
    group2,
):
    require_columns(
        df,
        [
            column,
            group_column,
        ],
    )

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
            "Both groups require at "
            "least two observations."
        )

    pooled_variance = (
        (
            (len(x) - 1)
            * x.var(ddof=1)
        )
        +
        (
            (len(y) - 1)
            * y.var(ddof=1)
        )
    ) / (
        len(x)
        + len(y)
        - 2
    )

    pooled_sd = math.sqrt(
        pooled_variance
    )

    if pooled_sd == 0:
        raise ValueError(
            "Effect size cannot be "
            "calculated because pooled "
            "standard deviation is zero."
        )

    cohen_d = (
        x.mean()
        - y.mean()
    ) / pooled_sd

    degrees_freedom = (
        len(x)
        + len(y)
        - 2
    )

    correction = (
        1
        -
        (
            3
            /
            (
                4
                * degrees_freedom
                - 1
            )
        )
        if degrees_freedom > 1
        else 1
    )

    hedges_g = (
        cohen_d
        * correction
    )

    return {
        "test":
            "Independent Samples",
        "group1":
            str(group1),
        "group2":
            str(group2),
        "group1_n":
            len(x),
        "group2_n":
            len(y),
        "cohen_d":
            clean_number(
                cohen_d
            ),
        "hedges_g":
            clean_number(
                hedges_g
            ),
        "magnitude":
            magnitude_from_d(
                cohen_d
            ),
    }


def paired_effect_size(
    df,
    column1,
    column2,
):
    require_columns(
        df,
        [
            column1,
            column2,
        ],
    )

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
            "At least two paired "
            "observations are required."
        )

    differences = (
        paired[column1]
        - paired[column2]
    )

    standard_deviation = (
        differences.std(
            ddof=1
        )
    )

    if standard_deviation == 0:
        raise ValueError(
            "Difference scores have "
            "zero variance."
        )

    cohen_dz = (
        differences.mean()
        /
        standard_deviation
    )

    return {
        "test":
            "Paired Samples",
        "sample_size":
            len(paired),
        "cohen_dz":
            clean_number(
                cohen_dz
            ),
        "magnitude":
            magnitude_from_d(
                cohen_dz
            ),
    }


def anova_effect_size(
    df,
    value_column,
    group_column,
):
    require_columns(
        df,
        [
            value_column,
            group_column,
        ],
    )

    working = df[
        [
            value_column,
            group_column,
        ]
    ].copy()

    working[
        value_column
    ] = pd.to_numeric(
        working[
            value_column
        ],
        errors="coerce",
    )

    working = working.dropna()

    if working.empty:
        raise ValueError(
            "No usable observations."
        )

    groups = [
        group[
            value_column
        ].values
        for _, group
        in working.groupby(
            group_column
        )
        if len(group)
    ]

    if len(groups) < 2:
        raise ValueError(
            "At least two groups "
            "are required."
        )

    grand_mean = working[
        value_column
    ].mean()

    ss_between = sum(
        len(group)
        * (
            np.mean(group)
            - grand_mean
        ) ** 2
        for group in groups
    )

    ss_within = sum(
        np.sum(
            (
                group
                - np.mean(group)
            ) ** 2
        )
        for group in groups
    )

    ss_total = (
        ss_between
        + ss_within
    )

    eta_squared = (
        ss_between
        / ss_total
        if ss_total
        else 0
    )

    df_between = (
        len(groups)
        - 1
    )

    df_within = (
        len(working)
        - len(groups)
    )

    ms_within = (
        ss_within
        / df_within
        if df_within > 0
        else 0
    )

    omega_squared = (
        (
            ss_between
            -
            df_between
            * ms_within
        )
        /
        (
            ss_total
            + ms_within
        )
        if (
            ss_total
            + ms_within
        )
        else 0
    )

    omega_squared = max(
        0,
        omega_squared,
    )

    return {
        "test":
            "One-Way ANOVA",
        "eta_squared":
            clean_number(
                eta_squared
            ),
        "omega_squared":
            clean_number(
                omega_squared
            ),
    }


def chi_square_effect_size(
    df,
    column1,
    column2,
):
    require_columns(
        df,
        [
            column1,
            column2,
        ],
    )

    table = pd.crosstab(
        df[column1],
        df[column2],
    )

    if table.empty:
        raise ValueError(
            "Contingency table is empty."
        )

    statistic, _, _, _ = (
        stats.chi2_contingency(
            table
        )
    )

    n = table.values.sum()

    dimensions = min(
        table.shape[0] - 1,
        table.shape[1] - 1,
    )

    if (
        n == 0
        or dimensions <= 0
    ):
        raise ValueError(
            "Cramer's V cannot be "
            "calculated for this table."
        )

    cramers_v = math.sqrt(
        statistic
        /
        (
            n
            * dimensions
        )
    )

    return {
        "test":
            "Chi-Square",
        "cramers_v":
            clean_number(
                cramers_v
            ),
    }


def correlation_effect_size(
    df,
    column1,
    column2,
    method="pearson",
):
    require_columns(
        df,
        [
            column1,
            column2,
        ],
    )

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

    if len(paired) < 3:
        raise ValueError(
            "At least three paired "
            "numeric observations "
            "are required."
        )

    if method == "pearson":
        coefficient, p_value = (
            stats.pearsonr(
                paired[column1],
                paired[column2],
            )
        )

    elif method == "spearman":
        coefficient, p_value = (
            stats.spearmanr(
                paired[column1],
                paired[column2],
            )
        )

    elif method == "kendall":
        coefficient, p_value = (
            stats.kendalltau(
                paired[column1],
                paired[column2],
            )
        )

    else:
        raise ValueError(
            "Unsupported correlation method."
        )

    return {
        "test":
            f"{method.title()} correlation",
        "coefficient":
            clean_number(
                coefficient
            ),
        "p_value":
            clean_number(
                p_value
            ),
        "magnitude":
            correlation_magnitude(
                coefficient
            ),
    }


def calculate_effect_size(
    df,
    request,
):
    if request.test == "independent_t":
        if (
            request.column is None
            or request.group_column is None
            or request.group1 is None
            or request.group2 is None
        ):
            raise ValueError(
                "Independent t effect size "
                "requires column, group_column, "
                "group1 and group2."
            )

        return independent_effect_size(
            df,
            request.column,
            request.group_column,
            request.group1,
            request.group2,
        )

    if request.test == "paired_t":
        if (
            request.column1 is None
            or request.column2 is None
        ):
            raise ValueError(
                "Paired effect size requires "
                "column1 and column2."
            )

        return paired_effect_size(
            df,
            request.column1,
            request.column2,
        )

    if request.test == "anova":
        if (
            request.column is None
            or request.group_column is None
        ):
            raise ValueError(
                "ANOVA effect size requires "
                "column and group_column."
            )

        return anova_effect_size(
            df,
            request.column,
            request.group_column,
        )

    if request.test == "chi_square":
        if (
            request.column1 is None
            or request.column2 is None
        ):
            raise ValueError(
                "Chi-square effect size "
                "requires column1 and column2."
            )

        return chi_square_effect_size(
            df,
            request.column1,
            request.column2,
        )

    if request.test == "correlation":
        if (
            request.column1 is None
            or request.column2 is None
        ):
            raise ValueError(
                "Correlation effect size "
                "requires column1 and column2."
            )

        return correlation_effect_size(
            df,
            request.column1,
            request.column2,
            request.method,
        )

    raise ValueError(
        "Unsupported effect size test."
    )


# ============================================================
# SMART METHOD RECOMMENDER
# ============================================================

def effective_level(
    df,
    column,
    overrides=None,
):
    if (
        overrides
        and column in overrides
    ):
        return overrides[column]

    return infer_variable(
        df[column]
    )[
        "measurement_level"
    ]


def recommend_analysis(
    df,
    request,
):
    alpha = request.alpha

    overrides = (
        request.measurement_levels
        or {}
    )

    response = {
        "goal":
            request.goal,
        "recommended_method":
            None,
        "method_code":
            None,
        "implementation_status":
            "available",
        "reasoning":
            [],
        "assumptions":
            [],
        "alternatives":
            [],
        "variables":
            {},
    }

    # ========================================================
    # DISTRIBUTION / NORMALITY
    # ========================================================

    if request.goal == "distribution":
        if not request.outcome:
            raise ValueError(
                "Distribution analysis "
                "requires outcome."
            )

        require_columns(
            df,
            [request.outcome],
        )

        outcome_level = (
            effective_level(
                df,
                request.outcome,
                overrides,
            )
        )

        response[
            "variables"
        ][
            request.outcome
        ] = outcome_level

        if outcome_level != "metric":
            raise ValueError(
                "Normality assessment "
                "requires a metric "
                "numeric variable."
            )

        normality = normality_tests(
            df[request.outcome],
            alpha=alpha,
        )

        response.update(
            {
                "recommended_method":
                    (
                        "Normality "
                        "Assessment"
                    ),
                "method_code":
                    "normality",
                "reasoning": [
                    (
                        "A distribution/"
                        "normality goal was "
                        "selected."
                    ),
                    (
                        f"{request.outcome} "
                        "is treated as metric."
                    ),
                ],
                "assumptions":
                    normality,
            }
        )

        return response

    # ========================================================
    # COMPARE GROUPS
    # ========================================================

    if request.goal == "compare_groups":
        if not request.outcome:
            raise ValueError(
                "Group comparison "
                "requires outcome."
            )

        # ----------------------------------------------------
        # Paired comparison
        # ----------------------------------------------------

        if request.paired_column:
            require_columns(
                df,
                [
                    request.outcome,
                    request.paired_column,
                ],
            )

            paired = (
                df[
                    [
                        request.outcome,
                        request.paired_column,
                    ]
                ]
                .apply(
                    pd.to_numeric,
                    errors="coerce",
                )
                .dropna()
            )

            if len(paired) < 3:
                raise ValueError(
                    "At least three paired "
                    "observations are required."
                )

            differences = (
                paired[
                    request.outcome
                ]
                -
                paired[
                    request.paired_column
                ]
            )

            normality = (
                normality_tests(
                    differences,
                    methods=[
                        "shapiro"
                    ],
                    alpha=alpha,
                )
            )

            is_normal = (
                normality[
                    "tests"
                ][
                    "shapiro_wilk"
                ][
                    "normal"
                ]
            )

            response[
                "variables"
            ] = {
                request.outcome:
                    "metric",
                request.paired_column:
                    "metric",
            }

            if is_normal:
                response[
                    "recommended_method"
                ] = (
                    "Paired Samples "
                    "t-Test"
                )

                response[
                    "method_code"
                ] = "paired_t"

                response[
                    "alternatives"
                ] = [
                    "Wilcoxon Signed-Rank Test"
                ]

            else:
                response[
                    "recommended_method"
                ] = (
                    "Wilcoxon "
                    "Signed-Rank Test"
                )

                response[
                    "method_code"
                ] = "wilcoxon"

                response[
                    "alternatives"
                ] = [
                    "Paired Samples t-Test"
                ]

            response[
                "reasoning"
            ] = [
                (
                    "Two measurements are "
                    "paired for the same "
                    "observations."
                ),
                (
                    "Normality of the "
                    "difference scores was "
                    "checked."
                ),
            ]

            response[
                "assumptions"
            ] = normality

            return response

        # ----------------------------------------------------
        # Independent groups
        # ----------------------------------------------------

        if not request.group:
            raise ValueError(
                "Independent group "
                "comparison requires group."
            )

        require_columns(
            df,
            [
                request.outcome,
                request.group,
            ],
        )

        outcome_level = (
            effective_level(
                df,
                request.outcome,
                overrides,
            )
        )

        group_level = (
            effective_level(
                df,
                request.group,
                overrides,
            )
        )

        response[
            "variables"
        ] = {
            request.outcome:
                outcome_level,
            request.group:
                group_level,
        }

        if outcome_level != "metric":
            raise ValueError(
                "Current group comparison "
                "recommendations require "
                "a metric outcome."
            )

        working = df[
            [
                request.outcome,
                request.group,
            ]
        ].copy()

        working[
            request.outcome
        ] = pd.to_numeric(
            working[
                request.outcome
            ],
            errors="coerce",
        )

        working = (
            working.dropna()
        )

        groups = []

        group_names = []

        normality_results = {}

        for (
            name,
            group_df,
        ) in working.groupby(
            request.group
        ):
            values = group_df[
                request.outcome
            ].dropna()

            if len(values):
                groups.append(
                    values
                )

                group_names.append(
                    str(name)
                )

                if len(values) >= 3:
                    normal = (
                        normality_tests(
                            values,
                            methods=[
                                "shapiro"
                            ],
                            alpha=alpha,
                        )
                    )

                    normality_results[
                        str(name)
                    ] = normal

        if len(groups) < 2:
            raise ValueError(
                "At least two groups "
                "are required."
            )

        all_normal = True

        for result in (
            normality_results
            .values()
        ):
            if not result[
                "tests"
            ][
                "shapiro_wilk"
            ][
                "normal"
            ]:
                all_normal = False

        levene_stat = None
        levene_p = None
        equal_variances = None

        if (
            len(groups) >= 2
            and all(
                len(group) >= 2
                for group in groups
            )
        ):
            (
                levene_stat,
                levene_p,
            ) = stats.levene(
                *groups,
                center="median",
            )

            equal_variances = bool(
                levene_p > alpha
            )

        response[
            "assumptions"
        ] = {
            "normality_by_group":
                normality_results,
            "levene": {
                "statistic":
                    clean_number(
                        levene_stat
                    ),
                "p_value":
                    clean_number(
                        levene_p
                    ),
                "equal_variances":
                    equal_variances,
            },
        }

        # Two independent groups
        if len(groups) == 2:
            if all_normal:
                response[
                    "recommended_method"
                ] = (
                    "Independent Samples "
                    "t-Test (Welch)"
                )

                response[
                    "method_code"
                ] = "independent_t"

                response[
                    "alternatives"
                ] = [
                    "Mann-Whitney U Test"
                ]

                response[
                    "reasoning"
                ] = [
                    (
                        "The outcome is metric."
                    ),
                    (
                        "There are two "
                        "independent groups."
                    ),
                    (
                        "Group distributions "
                        "passed the normality "
                        "diagnostic."
                    ),
                    (
                        "Welch's form of the "
                        "t-test is robust to "
                        "unequal variances."
                    ),
                ]

            else:
                response[
                    "recommended_method"
                ] = (
                    "Mann-Whitney U Test"
                )

                response[
                    "method_code"
                ] = "mann_whitney"

                response[
                    "alternatives"
                ] = [
                    (
                        "Independent Samples "
                        "t-Test"
                    )
                ]

                response[
                    "reasoning"
                ] = [
                    (
                        "The outcome is metric."
                    ),
                    (
                        "There are two "
                        "independent groups."
                    ),
                    (
                        "Normality was not "
                        "supported for all "
                        "groups."
                    ),
                ]

            response[
                "group_names"
            ] = group_names

            return response

        # More than two independent groups
        if all_normal and (
            equal_variances
            is not False
        ):
            response[
                "recommended_method"
            ] = "One-Way ANOVA"

            response[
                "method_code"
            ] = "one_way_anova"

            response[
                "alternatives"
            ] = [
                "Kruskal-Wallis H Test"
            ]

            response[
                "reasoning"
            ] = [
                (
                    "The outcome is metric."
                ),
                (
                    "There are more than "
                    "two independent groups."
                ),
                (
                    "Normality and variance "
                    "diagnostics support "
                    "parametric ANOVA."
                ),
            ]

        else:
            response[
                "recommended_method"
            ] = (
                "Kruskal-Wallis H Test"
            )

            response[
                "method_code"
            ] = "kruskal_wallis"

            response[
                "alternatives"
            ] = [
                "One-Way ANOVA"
            ]

            response[
                "reasoning"
            ] = [
                (
                    "There are more than "
                    "two independent groups."
                ),
                (
                    "Parametric assumptions "
                    "were not fully supported."
                ),
            ]

        response[
            "group_names"
        ] = group_names

        return response

    # ========================================================
    # RELATIONSHIP
    # ========================================================

    if request.goal == "relationship":
        if (
            not request.variables
            or len(
                request.variables
            ) != 2
        ):
            raise ValueError(
                "Relationship analysis "
                "requires exactly two "
                "variables."
            )

        column1 = (
            request.variables[0]
        )

        column2 = (
            request.variables[1]
        )

        require_columns(
            df,
            [
                column1,
                column2,
            ],
        )

        level1 = effective_level(
            df,
            column1,
            overrides,
        )

        level2 = effective_level(
            df,
            column2,
            overrides,
        )

        response[
            "variables"
        ] = {
            column1:
                level1,
            column2:
                level2,
        }

        # Both metric
        if (
            level1 == "metric"
            and level2 == "metric"
        ):
            normal1 = (
                normality_tests(
                    df[column1],
                    methods=[
                        "shapiro"
                    ],
                    alpha=alpha,
                )
            )

            normal2 = (
                normality_tests(
                    df[column2],
                    methods=[
                        "shapiro"
                    ],
                    alpha=alpha,
                )
            )

            both_normal = (
                normal1[
                    "tests"
                ][
                    "shapiro_wilk"
                ][
                    "normal"
                ]
                and
                normal2[
                    "tests"
                ][
                    "shapiro_wilk"
                ][
                    "normal"
                ]
            )

            if both_normal:
                response[
                    "recommended_method"
                ] = (
                    "Pearson Correlation"
                )

                response[
                    "method_code"
                ] = "pearson"

                response[
                    "alternatives"
                ] = [
                    "Spearman Correlation",
                    "Kendall Correlation",
                ]

            else:
                response[
                    "recommended_method"
                ] = (
                    "Spearman Correlation"
                )

                response[
                    "method_code"
                ] = "spearman"

                response[
                    "alternatives"
                ] = [
                    "Kendall Correlation",
                    "Pearson Correlation",
                ]

            response[
                "reasoning"
            ] = [
                (
                    "Both variables are "
                    "metric."
                ),
                (
                    "Normality was evaluated "
                    "to distinguish Pearson "
                    "from rank correlation."
                ),
            ]

            response[
                "assumptions"
            ] = {
                column1:
                    normal1,
                column2:
                    normal2,
            }

            return response

        # Both categorical
        if (
            level1
            in {
                "nominal",
                "ordinal",
            }
            and level2
            in {
                "nominal",
                "ordinal",
            }
        ):
            response[
                "recommended_method"
            ] = (
                "Chi-Square Test "
                "of Independence"
            )

            response[
                "method_code"
            ] = "chi_square"

            response[
                "reasoning"
            ] = [
                (
                    "Both variables are "
                    "categorical."
                ),
                (
                    "Chi-square evaluates "
                    "association between "
                    "categorical variables."
                ),
            ]

            return response

        response[
            "recommended_method"
        ] = (
            "Group comparison / "
            "point-biserial analysis"
        )

        response[
            "method_code"
        ] = "mixed_relationship"

        response[
            "implementation_status"
        ] = "partially_available"

        response[
            "reasoning"
        ] = [
            (
                "One variable is metric "
                "and the other categorical."
            ),
            (
                "For a binary categorical "
                "variable, an independent "
                "t-test or point-biserial "
                "correlation can be used."
            ),
        ]

        return response

    # ========================================================
    # PREDICTION
    # ========================================================

    if request.goal == "prediction":
        if not request.outcome:
            raise ValueError(
                "Prediction requires "
                "an outcome variable."
            )

        require_columns(
            df,
            [request.outcome],
        )

        predictors = (
            request.predictors
            or []
        )

        require_columns(
            df,
            predictors,
        )

        outcome_level = (
            effective_level(
                df,
                request.outcome,
                overrides,
            )
        )

        response[
            "variables"
        ][
            request.outcome
        ] = outcome_level

        if outcome_level == "metric":
            response[
                "recommended_method"
            ] = (
                "Linear Regression / "
                "Random Forest Regression"
            )

            response[
                "method_code"
            ] = "regression"

            response[
                "reasoning"
            ] = [
                (
                    "The outcome variable "
                    "is metric."
                ),
                (
                    "Regression methods "
                    "predict continuous "
                    "outcomes."
                ),
            ]

            response[
                "alternatives"
            ] = [
                "Linear Regression",
                (
                    "Random Forest "
                    "Regression"
                ),
            ]

            return response

        unique_outcomes = (
            df[
                request.outcome
            ]
            .dropna()
            .nunique()
        )

        if unique_outcomes == 2:
            response[
                "recommended_method"
            ] = (
                "Logistic Regression / "
                "Random Forest "
                "Classification"
            )

            response[
                "method_code"
            ] = (
                "binary_classification"
            )

            response[
                "reasoning"
            ] = [
                (
                    "The outcome has two "
                    "categories."
                ),
                (
                    "Binary classification "
                    "is appropriate."
                ),
            ]

            return response

        response[
            "recommended_method"
        ] = (
            "Multiclass Classification"
        )

        response[
            "method_code"
        ] = (
            "multiclass_classification"
        )

        response[
            "implementation_status"
        ] = "planned_extension"

        response[
            "reasoning"
        ] = [
            (
                "The outcome has more than "
                "two categories."
            ),
            (
                "A multiclass classifier "
                "or multinomial logistic "
                "model is appropriate."
            ),
        ]

        return response

    raise ValueError(
        "Unsupported research goal."
    )
