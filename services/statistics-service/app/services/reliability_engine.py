import math

import numpy as np
import pandas as pd

from scipy import stats


# ==========================================================
# JSON SAFE
# ==========================================================

def json_safe(
    value,
):
    if value is None:
        return None


    if isinstance(
        value,
        (
            bool,
            np.bool_,
        ),
    ):
        return bool(
            value
        )


    if isinstance(
        value,
        np.integer,
    ):
        return int(
            value
        )


    if isinstance(
        value,
        np.floating,
    ):
        number = float(
            value
        )

        if (
            math.isnan(
                number
            )
            or
            math.isinf(
                number
            )
        ):
            return None

        return number


    if isinstance(
        value,
        np.ndarray,
    ):
        return [
            json_safe(
                item
            )
            for item
            in value.tolist()
        ]


    if isinstance(
        value,
        dict,
    ):
        return {
            str(
                key
            ):
                json_safe(
                    item
                )
            for key, item
            in value.items()
        }


    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            json_safe(
                item
            )
            for item
            in value
        ]


    return value


# ==========================================================
# PREPARE DATA
# ==========================================================

def prepare_reliability_data(
    dataframe,
    variables,
):
    missing_columns = [
        variable
        for variable
        in variables
        if variable
        not in dataframe.columns
    ]


    if missing_columns:
        raise ValueError(
            (
                "Dataset does not contain: "
                +
                ", ".join(
                    missing_columns
                )
            )
        )


    working = (
        dataframe[
            variables
        ]
        .copy()
    )


    original_rows = int(
        len(
            working
        )
    )


    for variable in variables:

        original_non_missing = int(
            working[
                variable
            ]
            .notna()
            .sum()
        )


        converted = pd.to_numeric(
            working[
                variable
            ],
            errors="coerce",
        )


        converted_non_missing = int(
            converted
            .notna()
            .sum()
        )


        if original_non_missing > 0:

            conversion_ratio = (
                converted_non_missing
                /
                original_non_missing
            )

        else:

            conversion_ratio = 0.0


        if conversion_ratio < 0.80:

            raise ValueError(
                (
                    f"Item '{variable}' is not "
                    f"sufficiently numeric for "
                    f"reliability analysis."
                )
            )


        working[
            variable
        ] = converted


    working = (
        working
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .dropna()
    )


    complete_rows = int(
        len(
            working
        )
    )


    if complete_rows < 10:

        raise ValueError(
            (
                "Reliability analysis requires "
                "at least 10 complete observations. "
                f"Only {complete_rows} complete "
                f"observations remained."
            )
        )


    for variable in variables:

        unique_count = int(
            working[
                variable
            ]
            .nunique()
        )


        if unique_count < 2:

            raise ValueError(
                (
                    f"Item '{variable}' is constant "
                    f"and cannot be included in "
                    f"reliability analysis."
                )
            )


    return {
        "data":
            working,

        "original_rows":
            original_rows,

        "complete_rows":
            complete_rows,

        "excluded_rows":
            (
                original_rows
                -
                complete_rows
            ),
    }


# ==========================================================
# CRONBACH ALPHA
# ==========================================================

def cronbach_alpha(
    dataframe,
):
    values = (
        dataframe
        .to_numpy(
            dtype=float
        )
    )


    number_items = (
        values.shape[
            1
        ]
    )


    if number_items < 2:
        return None


    item_variances = np.var(
        values,
        axis=0,
        ddof=1,
    )


    total_score = np.sum(
        values,
        axis=1,
    )


    total_variance = float(
        np.var(
            total_score,
            ddof=1,
        )
    )


    if total_variance <= 0:
        return None


    alpha = (
        number_items
        /
        (
            number_items
            -
            1
        )
        *
        (
            1
            -
            (
                float(
                    np.sum(
                        item_variances
                    )
                )
                /
                total_variance
            )
        )
    )


    return float(
        alpha
    )


# ==========================================================
# STANDARDIZED CRONBACH ALPHA
# ==========================================================

def standardized_alpha(
    dataframe,
):
    correlation = (
        dataframe
        .corr()
        .to_numpy(
            dtype=float
        )
    )


    k = (
        correlation.shape[
            0
        ]
    )


    if k < 2:
        return None


    upper_triangle = (
        correlation[
            np.triu_indices(
                k,
                k=1,
            )
        ]
    )


    upper_triangle = (
        upper_triangle[
            np.isfinite(
                upper_triangle
            )
        ]
    )


    if len(
        upper_triangle
    ) == 0:
        return None


    average_correlation = float(
        np.mean(
            upper_triangle
        )
    )


    denominator = (
        1
        +
        (
            k
            -
            1
        )
        *
        average_correlation
    )


    if abs(
        denominator
    ) < 1e-12:
        return None


    alpha = (
        k
        *
        average_correlation
        /
        denominator
    )


    return {
        "alpha":
            float(
                alpha
            ),

        "average_inter_item_correlation":
            average_correlation,
    }


# ==========================================================
# ALPHA ASSESSMENT
# ==========================================================

def reliability_label(
    value,
):
    if value is None:
        return "Unavailable"


    value = float(
        value
    )


    if value >= 0.90:
        return "Excellent"


    if value >= 0.80:
        return "Good"


    if value >= 0.70:
        return "Acceptable"


    if value >= 0.60:
        return "Questionable"


    if value >= 0.50:
        return "Poor"


    return "Unacceptable"


# ==========================================================
# ITEM DESCRIPTIVES
# ==========================================================

def item_descriptive_table(
    dataframe,
):
    rows = []


    for variable in dataframe.columns:

        series = (
            dataframe[
                variable
            ]
            .astype(
                float
            )
        )


        rows.append({
            "Item":
                variable,

            "N":
                int(
                    series.count()
                ),

            "Mean":
                float(
                    series.mean()
                ),

            "SD":
                float(
                    series.std(
                        ddof=1
                    )
                ),

            "Min":
                float(
                    series.min()
                ),

            "Max":
                float(
                    series.max()
                ),

            "Variance":
                float(
                    series.var(
                        ddof=1
                    )
                ),
        })


    return rows


# ==========================================================
# INTER-ITEM CORRELATION TABLE
# ==========================================================

def inter_item_correlation_table(
    dataframe,
):
    correlation = (
        dataframe
        .corr()
    )


    variables = (
        dataframe
        .columns
        .tolist()
    )


    columns = [
        "Item"
    ] + variables


    rows = []


    for row_variable in variables:

        row = {
            "Item":
                row_variable
        }


        for column_variable in variables:

            value = (
                correlation
                .loc[
                    row_variable,
                    column_variable
                ]
            )


            row[
                column_variable
            ] = (
                float(
                    value
                )
                if pd.notna(
                    value
                )
                else None
            )


        rows.append(
            row
        )


    return (
        columns,
        rows,
    )


# ==========================================================
# CORRECTED ITEM-TOTAL CORRELATION
# ==========================================================

def corrected_item_total(
    dataframe,
    variable,
):
    item = (
        dataframe[
            variable
        ]
        .to_numpy(
            dtype=float
        )
    )


    other_columns = [
        column
        for column
        in dataframe.columns
        if column
        !=
        variable
    ]


    if not other_columns:
        return None


    corrected_total = (
        dataframe[
            other_columns
        ]
        .sum(
            axis=1
        )
        .to_numpy(
            dtype=float
        )
    )


    if (
        np.std(
            item,
            ddof=1
        )
        <=
        0
        or
        np.std(
            corrected_total,
            ddof=1
        )
        <=
        0
    ):
        return None


    result = (
        stats.pearsonr(
            item,
            corrected_total,
        )
    )


    return float(
        result.statistic
    )


# ==========================================================
# ITEM DIAGNOSTICS
# ==========================================================

def item_diagnostics(
    dataframe,
    full_alpha,
    item_total_threshold,
):
    rows = []


    total_score = (
        dataframe
        .sum(
            axis=1
        )
    )


    full_total_mean = float(
        total_score.mean()
    )


    full_total_variance = float(
        total_score.var(
            ddof=1
        )
    )


    for variable in dataframe.columns:

        item_total = (
            corrected_item_total(
                dataframe,
                variable,
            )
        )


        reduced = (
            dataframe
            .drop(
                columns=[
                    variable
                ]
            )
        )


        if (
            reduced.shape[
                1
            ]
            >=
            2
        ):

            alpha_deleted = (
                cronbach_alpha(
                    reduced
                )
            )

        else:

            alpha_deleted = None


        if (
            item_total
            is None
        ):

            status = (
                "Unavailable"
            )


        elif (
            item_total
            <
            0
        ):

            status = (
                "Reverse / Review"
            )


        elif (
            item_total
            <
            item_total_threshold
        ):

            status = (
                "Review"
            )


        else:

            status = (
                "Good"
            )


        improves_alpha = (
            alpha_deleted
            is not None
            and
            full_alpha
            is not None
            and
            alpha_deleted
            >
            full_alpha
            +
            0.01
        )


        rows.append({
            "Item":
                variable,

            "Corrected Item-Total Correlation":
                item_total,

            "Alpha if Item Deleted":
                alpha_deleted,

            "Improves Alpha if Deleted":
                bool(
                    improves_alpha
                ),

            "Status":
                status,
        })


    return {
        "rows":
            rows,

        "scale_mean":
            full_total_mean,

        "scale_variance":
            full_total_variance,
    }


# ==========================================================
# INTER-ITEM SUMMARY
# ==========================================================

def inter_item_summary(
    dataframe,
):
    correlation = (
        dataframe
        .corr()
        .to_numpy(
            dtype=float
        )
    )


    k = (
        correlation.shape[
            0
        ]
    )


    values = (
        correlation[
            np.triu_indices(
                k,
                k=1,
            )
        ]
    )


    values = (
        values[
            np.isfinite(
                values
            )
        ]
    )


    if len(
        values
    ) == 0:

        return {
            "mean":
                None,

            "minimum":
                None,

            "maximum":
                None,

            "negative_count":
                0,
        }


    return {
        "mean":
            float(
                np.mean(
                    values
                )
            ),

        "minimum":
            float(
                np.min(
                    values
                )
            ),

        "maximum":
            float(
                np.max(
                    values
                )
            ),

        "negative_count":
            int(
                np.sum(
                    values
                    <
                    0
                )
            ),
    }


# ==========================================================
# SPLIT HALF RELIABILITY
# ==========================================================

def split_half_reliability(
    dataframe,
):
    variables = (
        dataframe
        .columns
        .tolist()
    )


    if len(
        variables
    ) < 4:

        return {
            "correlation":
                None,

            "spearman_brown":
                None,

            "first_half":
                [],

            "second_half":
                [],
        }


    first_half = (
        variables[
            ::2
        ]
    )


    second_half = (
        variables[
            1::2
        ]
    )


    score_one = (
        dataframe[
            first_half
        ]
        .sum(
            axis=1
        )
        .to_numpy(
            dtype=float
        )
    )


    score_two = (
        dataframe[
            second_half
        ]
        .sum(
            axis=1
        )
        .to_numpy(
            dtype=float
        )
    )


    if (
        np.std(
            score_one,
            ddof=1
        )
        <=
        0
        or
        np.std(
            score_two,
            ddof=1
        )
        <=
        0
    ):

        correlation = None
        spearman_brown = None

    else:

        correlation = float(
            stats.pearsonr(
                score_one,
                score_two,
            ).statistic
        )


        denominator = (
            1
            +
            correlation
        )


        if (
            abs(
                denominator
            )
            <
            1e-12
        ):

            spearman_brown = None

        else:

            spearman_brown = float(
                (
                    2
                    *
                    correlation
                )
                /
                denominator
            )


    return {
        "correlation":
            correlation,

        "spearman_brown":
            spearman_brown,

        "first_half":
            first_half,

        "second_half":
            second_half,
    }

# ==========================================================
# BUILD QUALITY CHECKS
# ==========================================================

def quality_checks(
    dataframe,
    full_alpha,
    item_rows,
    inter_item,
):
    rows = []


    # ------------------------------------------------------
    # NUMBER OF ITEMS
    # ------------------------------------------------------

    number_items = int(
        dataframe.shape[
            1
        ]
    )


    rows.append({
        "Check":
            "Number of scale items",

        "Status":
            (
                "Good"
                if number_items
                >=
                3
                else
                "Review"
            ),

        "Details":
            (
                f"{number_items} item(s) "
                f"were analysed."
            ),
    })


    # ------------------------------------------------------
    # INTERNAL CONSISTENCY
    # ------------------------------------------------------

    rows.append({
        "Check":
            "Cronbach's alpha",

        "Status":
            reliability_label(
                full_alpha
            ),

        "Details":
            (
                (
                    f"Overall alpha = "
                    f"{full_alpha:.3f}."
                )
                if full_alpha
                is not None
                else
                "Cronbach's alpha could not "
                "be estimated."
            ),
    })


    # ------------------------------------------------------
    # NEGATIVE INTER-ITEM CORRELATIONS
    # ------------------------------------------------------

    negative_count = (
        inter_item[
            "negative_count"
        ]
    )


    rows.append({
        "Check":
            "Negative inter-item correlations",

        "Status":
            (
                "Good"
                if negative_count
                ==
                0
                else
                "Review"
            ),

        "Details":
            (
                (
                    "No negative inter-item "
                    "correlations were detected."
                )
                if negative_count
                ==
                0
                else
                (
                    f"{negative_count} negative "
                    f"inter-item correlation(s) "
                    f"were detected. Check whether "
                    f"any items require reverse scoring."
                )
            ),
    })


    # ------------------------------------------------------
    # LOW ITEM-TOTAL
    # ------------------------------------------------------

    review_items = [
        row[
            "Item"
        ]
        for row
        in item_rows
        if row[
            "Status"
        ]
        in (
            "Review",
            "Reverse / Review",
        )
    ]


    rows.append({
        "Check":
            "Item-total relationships",

        "Status":
            (
                "Good"
                if not review_items
                else
                "Review"
            ),

        "Details":
            (
                "All items showed acceptable "
                "corrected item-total relationships."
                if not review_items
                else
                (
                    "Review item(s): "
                    +
                    ", ".join(
                        review_items
                    )
                )
            ),
    })


    # ------------------------------------------------------
    # SCALE CONSTRUCT
    # ------------------------------------------------------

    rows.append({
        "Check":
            "Unidimensionality",

        "Status":
            "User review",

        "Details":
            (
                "Cronbach's alpha does not prove "
                "that all items measure one construct. "
                "Use EFA/PCA and subject-matter theory "
                "to evaluate dimensionality."
            ),
    })


    return rows


# ==========================================================
# MAIN RELIABILITY ENGINE
# ==========================================================

def run_reliability_analysis(
    dataframe,
    variables,
    alpha=0.05,
    item_total_threshold=0.30,
):
    prepared = (
        prepare_reliability_data(
            dataframe=(
                dataframe
            ),

            variables=(
                variables
            ),
        )
    )


    working = (
        prepared[
            "data"
        ]
    )


    number_items = int(
        len(
            variables
        )
    )


    n = int(
        len(
            working
        )
    )


    # ======================================================
    # CRONBACH ALPHA
    # ======================================================

    full_alpha = (
        cronbach_alpha(
            working
        )
    )


    standardized = (
        standardized_alpha(
            working
        )
    )


    standardized_alpha_value = (
        standardized[
            "alpha"
        ]
        if standardized
        else None
    )


    average_inter_item = (
        standardized[
            "average_inter_item_correlation"
        ]
        if standardized
        else None
    )


    # ======================================================
    # ITEM TABLES
    # ======================================================

    descriptives = (
        item_descriptive_table(
            working
        )
    )


    diagnostics = (
        item_diagnostics(
            dataframe=(
                working
            ),

            full_alpha=(
                full_alpha
            ),

            item_total_threshold=(
                item_total_threshold
            ),
        )
    )


    (
        correlation_columns,
        correlation_rows,
    ) = (
        inter_item_correlation_table(
            working
        )
    )


    inter_item = (
        inter_item_summary(
            working
        )
    )


    split_half = (
        split_half_reliability(
            working
        )
    )


    checks = (
        quality_checks(
            dataframe=(
                working
            ),

            full_alpha=(
                full_alpha
            ),

            item_rows=(
                diagnostics[
                    "rows"
                ]
            ),

            inter_item=(
                inter_item
            ),
        )
    )


    # ======================================================
    # INTERPRETATION
    # ======================================================

    alpha_label = (
        reliability_label(
            full_alpha
        )
    )


    if full_alpha is None:

        alpha_text = (
            "Cronbach's alpha could "
            "not be estimated."
        )

    else:

        alpha_text = (
            f"Cronbach's alpha was "
            f"{full_alpha:.3f}, indicating "
            f"{alpha_label.lower()} internal "
            f"consistency under conventional "
            f"descriptive guidelines."
        )


    if (
        average_inter_item
        is not None
    ):

        inter_item_text = (
            f"The average inter-item correlation "
            f"was {average_inter_item:.3f}."
        )

    else:

        inter_item_text = (
            "The average inter-item correlation "
            "was unavailable."
        )


    low_items = [
        row[
            "Item"
        ]
        for row
        in diagnostics[
            "rows"
        ]
        if row[
            "Status"
        ]
        in (
            "Review",
            "Reverse / Review",
        )
    ]


    if low_items:

        item_text = (
            "The following item(s) should be "
            "reviewed because of weak or negative "
            "corrected item-total relationships: "
            +
            ", ".join(
                low_items
            )
            +
            "."
        )

    else:

        item_text = (
            "No selected item was flagged for "
            "a weak corrected item-total relationship."
        )


    interpretation = (
        f"Reliability analysis was performed on "
        f"{number_items} item(s) using {n} complete "
        f"observations. "
        f"{alpha_text} "
        f"{inter_item_text} "
        f"{item_text} "
        f"Cronbach's alpha should be interpreted "
        f"alongside item content and evidence that "
        f"the items measure a common construct."
    )


    # ======================================================
    # APA
    # ======================================================

    if full_alpha is not None:

        apa = (
            f"Internal consistency reliability was "
            f"evaluated for the {number_items}-item "
            f"scale using Cronbach's alpha. "
            f"The scale demonstrated "
            f"{alpha_label.lower()} internal consistency, "
            f"α = {full_alpha:.3f}, N = {n}."
        )

    else:

        apa = (
            f"Internal consistency reliability was "
            f"evaluated for the {number_items}-item "
            f"scale using {n} complete observations; "
            f"however, Cronbach's alpha could not "
            f"be estimated."
        )


    # ======================================================
    # TABLES
    # ======================================================

    tables = [
        {
            "title":
                "Reliability Statistics",

            "columns": [
                "N",
                "Items",
                "Cronbach's Alpha",
                "Standardized Alpha",
                "Average Inter-Item Correlation",
                "Assessment",
            ],

            "rows": [
                {
                    "N":
                        n,

                    "Items":
                        number_items,

                    "Cronbach's Alpha":
                        full_alpha,

                    "Standardized Alpha":
                        standardized_alpha_value,

                    "Average Inter-Item Correlation":
                        average_inter_item,

                    "Assessment":
                        alpha_label,
                }
            ],
        },

        {
            "title":
                "Scale Statistics",

            "columns": [
                "Scale Mean",
                "Scale Variance",
                "Complete Cases",
                "Excluded Cases",
            ],

            "rows": [
                {
                    "Scale Mean":
                        diagnostics[
                            "scale_mean"
                        ],

                    "Scale Variance":
                        diagnostics[
                            "scale_variance"
                        ],

                    "Complete Cases":
                        prepared[
                            "complete_rows"
                        ],

                    "Excluded Cases":
                        prepared[
                            "excluded_rows"
                        ],
                }
            ],
        },

        {
            "title":
                "Item Descriptive Statistics",

            "columns": [
                "Item",
                "N",
                "Mean",
                "SD",
                "Min",
                "Max",
                "Variance",
            ],

            "rows":
                descriptives,
        },

        {
            "title":
                "Item-Total Statistics",

            "columns": [
                "Item",
                "Corrected Item-Total Correlation",
                "Alpha if Item Deleted",
                "Improves Alpha if Deleted",
                "Status",
            ],

            "rows":
                diagnostics[
                    "rows"
                ],
        },

        {
            "title":
                "Inter-Item Correlation Matrix",

            "columns":
                correlation_columns,

            "rows":
                correlation_rows,
        },

        {
            "title":
                "Inter-Item Correlation Summary",

            "columns": [
                "Mean Correlation",
                "Minimum Correlation",
                "Maximum Correlation",
                "Negative Correlations",
            ],

            "rows": [
                {
                    "Mean Correlation":
                        inter_item[
                            "mean"
                        ],

                    "Minimum Correlation":
                        inter_item[
                            "minimum"
                        ],

                    "Maximum Correlation":
                        inter_item[
                            "maximum"
                        ],

                    "Negative Correlations":
                        inter_item[
                            "negative_count"
                        ],
                }
            ],
        },

        {
            "title":
                "Split-Half Reliability",

            "columns": [
                "First Half",
                "Second Half",
                "Half Correlation",
                "Spearman-Brown Coefficient",
            ],

            "rows": [
                {
                    "First Half":
                        ", ".join(
                            split_half[
                                "first_half"
                            ]
                        ),

                    "Second Half":
                        ", ".join(
                            split_half[
                                "second_half"
                            ]
                        ),

                    "Half Correlation":
                        split_half[
                            "correlation"
                        ],

                    "Spearman-Brown Coefficient":
                        split_half[
                            "spearman_brown"
                        ],
                }
            ],
        },

        {
            "title":
                "Reliability Checks",

            "columns": [
                "Check",
                "Status",
                "Details",
            ],

            "rows":
                checks,
        },
    ]


    return json_safe({
        "analysis_name":
            "Reliability Analysis",

        "title":
            "Internal Consistency Reliability",

        "configuration": {
            "variables":
                variables,

            "alpha":
                alpha,

            "item_total_threshold":
                item_total_threshold,

            "missing_data":
                "Complete-case analysis",
        },

        "summary": {
            "n":
                n,

            "items":
                number_items,

            "cronbach_alpha":
                full_alpha,

            "standardized_alpha":
                standardized_alpha_value,

            "assessment":
                alpha_label,

            "average_inter_item_correlation":
                average_inter_item,

            "excluded_cases":
                prepared[
                    "excluded_rows"
                ],
        },

        "tables":
            tables,

        "assumptions":
            checks,

        "interpretation":
            interpretation,

        "apa":
            apa,

        "metadata": {
            "complete_cases":
                n,

            "excluded_cases":
                prepared[
                    "excluded_rows"
                ],

            "items":
                variables,

            "method":
                "Cronbach's Alpha",

            "split_half_method":
                "Odd-even item split",
        },
    })
