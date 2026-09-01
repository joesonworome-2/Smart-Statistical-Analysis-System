import math

import numpy as np
import pandas as pd

from scipy import stats


# ==========================================================
# GENERAL HELPERS
# ==========================================================


# ==========================================================
# JSON-SAFE CONVERSION
# ==========================================================

def json_safe(value):
    """
    Recursively convert NumPy values into normal
    Python values that FastAPI can serialize to JSON.
    """

    if value is None:
        return None

    # Boolean
    if isinstance(
        value,
        (
            np.bool_,
            bool,
        ),
    ):
        return bool(value)

    # Integer
    if isinstance(
        value,
        np.integer,
    ):
        return int(value)

    # Floating point
    if isinstance(
        value,
        np.floating,
    ):
        number = float(value)

        if (
            math.isnan(number)
            or
            math.isinf(number)
        ):
            return None

        return number

    # NumPy array
    if isinstance(
        value,
        np.ndarray,
    ):
        return [
            json_safe(item)
            for item in value.tolist()
        ]

    # Dictionary
    if isinstance(
        value,
        dict,
    ):
        return {
            str(key):
                json_safe(item)
            for key, item
            in value.items()
        }

    # Collections
    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            json_safe(item)
            for item in value
        ]

    return value


def clean_number(value):
    if value is None:
        return None

    if isinstance(value, np.integer):
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


def numeric_series(series: pd.Series):
    """
    Convert a variable into numeric values.

    Numeric values are used directly.

    Date values are converted to elapsed-day values.

    Text categories are NOT automatically encoded because
    category ordering must not be invented for correlation.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    valid_numeric = int(
        numeric.notna().sum()
    )

    original_valid = int(
        series.notna().sum()
    )

    if (
        original_valid > 0
        and
        valid_numeric
        / original_valid
        >= 0.75
    ):
        return numeric.astype(
            float
        )

    dates = pd.to_datetime(
        series,
        errors="coerce",
    )

    valid_dates = int(
        dates.notna().sum()
    )

    if (
        original_valid > 0
        and
        valid_dates
        / original_valid
        >= 0.75
    ):
        result = pd.Series(
            np.nan,
            index=series.index,
            dtype=float,
        )

        valid_mask = (
            dates.notna()
        )

        result.loc[
            valid_mask
        ] = (
            dates.loc[
                valid_mask
            ].astype("int64")
            / 86_400_000_000_000
        )

        return result

    return pd.Series(
        np.nan,
        index=series.index,
        dtype=float,
    )


# ==========================================================
# NORMALITY DIAGNOSTIC
# ==========================================================

def normality_test(
    values,
    alpha=0.05,
):
    series = pd.Series(
        values
    ).dropna()

    if len(series) < 3:
        return {
            "statistic": None,
            "p_value": None,
            "normal": None,
            "status": (
                "Insufficient observations"
            ),
        }

    sample = series

    if len(sample) > 5000:
        sample = sample.sample(
            n=5000,
            random_state=42,
        )

    statistic, p_value = (
        stats.shapiro(
            sample
        )
    )

    return {
        "statistic": clean_number(
            statistic
        ),
        "p_value": clean_number(
            p_value
        ),
        "normal": bool(
            p_value >= alpha
        ),
        "status": (
            "Approximately normal"
            if p_value >= alpha
            else "Normality rejected"
        ),
    }


# ==========================================================
# OUTLIERS
# ==========================================================

def outlier_summary(values):
    series = pd.Series(
        values
    ).dropna()

    if len(series) < 4:
        return {
            "count": 0,
            "percent": 0.0,
            "warning": False,
        }

    q1 = series.quantile(
        0.25
    )

    q3 = series.quantile(
        0.75
    )

    iqr = q3 - q1

    if iqr == 0:
        return {
            "count": 0,
            "percent": 0.0,
            "warning": False,
        }

    lower = (
        q1
        - 1.5
        * iqr
    )

    upper = (
        q3
        + 1.5
        * iqr
    )

    mask = (
        (series < lower)
        |
        (series > upper)
    )

    count = int(
        mask.sum()
    )

    percent = (
        count
        / len(series)
        * 100
    )

    return {
        "count": count,
        "percent": clean_number(
            percent
        ),
        "warning": bool(
            percent >= 5
        ),
    }


# ==========================================================
# TIES
# ==========================================================

def tie_ratio(values):
    series = pd.Series(
        values
    ).dropna()

    if len(series) == 0:
        return 0.0

    unique_count = int(
        series.nunique()
    )

    return clean_number(
        1
        -
        unique_count
        / len(series)
    )


# ==========================================================
# CORRELATION STRENGTH
# ==========================================================

def correlation_strength(
    coefficient,
):
    if coefficient is None:
        return None

    absolute = abs(
        coefficient
    )

    if absolute < 0.10:
        return "Negligible"

    if absolute < 0.30:
        return "Weak"

    if absolute < 0.50:
        return "Moderate"

    if absolute < 0.70:
        return "Strong"

    return "Very strong"


def correlation_direction(
    coefficient,
):
    if coefficient is None:
        return None

    if coefficient > 0:
        return "Positive"

    if coefficient < 0:
        return "Negative"

    return "None"


# ==========================================================
# AUTOMATIC METHOD RECOMMENDATION
# ==========================================================

def recommend_method(
    dataframe,
    variables,
):
    """
    Smart recommendation.

    Pearson:
        suitable when there are no strong skew/outlier
        warnings and variables behave as continuous data.

    Spearman:
        preferred when there is substantial skewness
        or outlier influence.

    Kendall:
        useful for smaller samples or many tied ranks.

    We deliberately do not select a method solely from
    Shapiro-Wilk normality results.
    """

    numeric_data = {}

    substantial_outliers = False
    substantial_skew = False
    many_ties = False

    diagnostics = []

    for variable in variables:
        converted = numeric_series(
            dataframe[
                variable
            ]
        )

        clean = converted.dropna()

        if len(clean) < 3:
            raise ValueError(
                (
                    f"{variable} does not contain "
                    f"enough numeric or date values "
                    f"for correlation analysis."
                )
            )

        numeric_data[
            variable
        ] = converted

        skewness = None

        if len(clean) > 2:
            skewness = clean_number(
                stats.skew(
                    clean,
                    bias=False,
                )
            )

        outliers = (
            outlier_summary(
                clean
            )
        )

        ties = tie_ratio(
            clean
        )

        if (
            skewness is not None
            and
            abs(skewness) >= 1.0
        ):
            substantial_skew = True

        if outliers[
            "warning"
        ]:
            substantial_outliers = True

        if ties >= 0.20:
            many_ties = True

        diagnostics.append({
            "Variable": variable,
            "Valid n": int(
                len(clean)
            ),
            "Skewness": skewness,
            "Outliers": (
                outliers[
                    "count"
                ]
            ),
            "Outlier %": (
                outliers[
                    "percent"
                ]
            ),
            "Tie Ratio": ties,
        })

    complete = pd.DataFrame(
        numeric_data
    ).dropna()

    complete_n = len(
        complete
    )

    if (
        complete_n < 30
        or many_ties
    ):
        method = "kendall"

        reason = (
            "Kendall correlation was recommended because "
            "the complete sample is small or the selected "
            "variables contain substantial tied ranks."
        )

    elif (
        substantial_skew
        or substantial_outliers
    ):
        method = "spearman"

        reason = (
            "Spearman correlation was recommended because "
            "one or more variables contain substantial "
            "skewness or outlier influence."
        )

    else:
        method = "pearson"

        reason = (
            "Pearson correlation was recommended because "
            "the selected variables do not show major "
            "skewness or outlier warnings."
        )

    return {
        "method": method,
        "reason": reason,
        "complete_n": int(
            complete_n
        ),
        "diagnostics": diagnostics,
    }


# ==========================================================
# PEARSON CONFIDENCE INTERVAL
# ==========================================================

def pearson_confidence_interval(
    coefficient,
    sample_size,
    confidence_level,
):
    if (
        coefficient is None
        or sample_size <= 3
        or abs(coefficient) >= 1
    ):
        return (
            None,
            None,
        )

    fisher_z = np.arctanh(
        coefficient
    )

    standard_error = (
        1
        / math.sqrt(
            sample_size - 3
        )
    )

    alpha = (
        1
        - confidence_level
    )

    critical = (
        stats.norm.ppf(
            1
            - alpha
            / 2
        )
    )

    lower_z = (
        fisher_z
        -
        critical
        * standard_error
    )

    upper_z = (
        fisher_z
        +
        critical
        * standard_error
    )

    return (
        clean_number(
            np.tanh(
                lower_z
            )
        ),
        clean_number(
            np.tanh(
                upper_z
            )
        ),
    )


# ==========================================================
# CALCULATE PAIR
# ==========================================================

def calculate_pair(
    dataframe,
    variable1,
    variable2,
    method,
    alpha,
    confidence_level,
):
    x = numeric_series(
        dataframe[
            variable1
        ]
    )

    y = numeric_series(
        dataframe[
            variable2
        ]
    )

    paired = pd.DataFrame({
        variable1: x,
        variable2: y,
    }).dropna()

    if len(paired) < 3:
        raise ValueError(
            (
                f"{variable1} and {variable2} "
                f"do not have enough complete "
                f"paired observations."
            )
        )

    x_values = paired[
        variable1
    ]

    y_values = paired[
        variable2
    ]

    if (
        x_values.nunique() < 2
        or
        y_values.nunique() < 2
    ):
        raise ValueError(
            (
                f"Correlation cannot be calculated "
                f"between {variable1} and {variable2} "
                f"because one variable is constant."
            )
        )

    ci_lower = None
    ci_upper = None

    if method == "pearson":
        coefficient, p_value = (
            stats.pearsonr(
                x_values,
                y_values,
            )
        )

        (
            ci_lower,
            ci_upper,
        ) = (
            pearson_confidence_interval(
                coefficient,
                len(paired),
                confidence_level,
            )
        )

    elif method == "spearman":
        coefficient, p_value = (
            stats.spearmanr(
                x_values,
                y_values,
            )
        )

    elif method == "kendall":
        coefficient, p_value = (
            stats.kendalltau(
                x_values,
                y_values,
            )
        )

    else:
        raise ValueError(
            (
                "Correlation method must be "
                "pearson, spearman or kendall."
            )
        )

    coefficient = clean_number(
        coefficient
    )

    p_value = clean_number(
        p_value
    )

    significant = bool(
        p_value < alpha
    )

    return {
        "Variable 1": variable1,
        "Variable 2": variable2,
        "Method": (
            method.capitalize()
        ),
        "Coefficient": coefficient,
        "p-value": p_value,
        "n": int(
            len(paired)
        ),
        "CI Lower": ci_lower,
        "CI Upper": ci_upper,
        "Strength": (
            correlation_strength(
                coefficient
            )
        ),
        "Direction": (
            correlation_direction(
                coefficient
            )
        ),
        "Significant": (
            "Yes"
            if significant
            else "No"
        ),
    }


# ==========================================================
# CORRELATION MATRIX
# ==========================================================

def build_matrix(
    variables,
    pair_results,
):
    lookup = {}

    for row in pair_results:
        first = row[
            "Variable 1"
        ]

        second = row[
            "Variable 2"
        ]

        coefficient = row[
            "Coefficient"
        ]

        lookup[
            (
                first,
                second,
            )
        ] = coefficient

        lookup[
            (
                second,
                first,
            )
        ] = coefficient

    matrix_rows = []

    for row_variable in variables:
        row = {
            "Variable":
                row_variable
        }

        for column_variable in variables:
            if (
                row_variable
                ==
                column_variable
            ):
                row[
                    column_variable
                ] = 1.0

            else:
                row[
                    column_variable
                ] = lookup.get(
                    (
                        row_variable,
                        column_variable,
                    )
                )

        matrix_rows.append(
            row
        )

    return matrix_rows


# ==========================================================
# DIAGNOSTICS
# ==========================================================

def build_diagnostics(
    dataframe,
    variables,
    selected_method,
    alpha,
):
    rows = []

    for variable in variables:
        converted = numeric_series(
            dataframe[
                variable
            ]
        )

        clean = converted.dropna()

        normality = (
            normality_test(
                clean,
                alpha,
            )
        )

        outliers = (
            outlier_summary(
                clean
            )
        )

        skewness = None

        if len(clean) > 2:
            skewness = clean_number(
                stats.skew(
                    clean,
                    bias=False,
                )
            )

        if (
            selected_method
            ==
            "pearson"
        ):
            if (
                outliers[
                    "warning"
                ]
                or
                (
                    skewness
                    is not None
                    and
                    abs(
                        skewness
                    )
                    >= 1
                )
            ):
                status = (
                    "Review potential "
                    "outlier/skew influence"
                )

            else:
                status = (
                    "No major warning"
                )

        else:
            status = (
                "Rank-based correlation selected"
            )

        rows.append({
            "Variable": variable,
            "Valid n": int(
                len(clean)
            ),
            "Shapiro-Wilk": (
                normality[
                    "statistic"
                ]
            ),
            "Normality p": (
                normality[
                    "p_value"
                ]
            ),
            "Skewness": skewness,
            "Outliers": (
                outliers[
                    "count"
                ]
            ),
            "Outlier %": (
                outliers[
                    "percent"
                ]
            ),
            "Status": status,
        })

    return rows


# ==========================================================
# INTERPRETATION
# ==========================================================

def build_interpretation(
    pair_results,
    selected_method,
    alpha,
):
    if not pair_results:
        return (
            "No valid pairwise correlations "
            "were calculated."
        )

    strongest = max(
        pair_results,
        key=lambda row:
            abs(
                row[
                    "Coefficient"
                ]
            ),
    )

    significant_rows = [
        row
        for row
        in pair_results
        if row[
            "Significant"
        ] == "Yes"
    ]

    coefficient = (
        strongest[
            "Coefficient"
        ]
    )

    text = (
        f"{selected_method.capitalize()} correlation "
        f"was used. The strongest relationship was "
        f"between {strongest['Variable 1']} and "
        f"{strongest['Variable 2']} "
        f"(coefficient = {coefficient:.4f}). "
        f"This represents a "
        f"{strongest['Strength'].lower()} "
        f"{strongest['Direction'].lower()} relationship. "
    )

    if significant_rows:
        text += (
            f"{len(significant_rows)} of "
            f"{len(pair_results)} pairwise relationships "
            f"were statistically significant at "
            f"α = {alpha}. "
        )

    else:
        text += (
            f"No pairwise relationships were "
            f"statistically significant at "
            f"α = {alpha}. "
        )

    text += (
        "Correlation measures association and does "
        "not by itself establish causation."
    )

    return text


# ==========================================================
# APA STYLE
# ==========================================================

def build_apa(
    pair_results,
    selected_method,
):
    if not pair_results:
        return None

    strongest = max(
        pair_results,
        key=lambda row:
            abs(
                row[
                    "Coefficient"
                ]
            ),
    )

    symbols = {
        "pearson": "r",
        "spearman": "ρ",
        "kendall": "τ",
    }

    symbol = symbols.get(
        selected_method,
        "r",
    )

    p_value = strongest[
        "p-value"
    ]

    if p_value < 0.001:
        p_text = "p < .001"
    else:
        p_text = (
            f"p = {p_value:.3f}"
        )

    return (
        f"A {selected_method.capitalize()} correlation "
        f"showed a "
        f"{strongest['Strength'].lower()} "
        f"{strongest['Direction'].lower()} association "
        f"between {strongest['Variable 1']} and "
        f"{strongest['Variable 2']}, "
        f"{symbol} = "
        f"{strongest['Coefficient']:.3f}, "
        f"{p_text}, "
        f"n = {strongest['n']}."
    )


# ==========================================================
# MAIN ANALYSIS
# ==========================================================

def run_correlation_analysis(
    dataframe,
    variables,
    requested_method="auto",
    alpha=0.05,
    confidence_level=0.95,
):
    if not variables:
        raise ValueError(
            "Select at least two variables."
        )

    if len(variables) < 2:
        raise ValueError(
            "At least two variables are required."
        )

    if len(set(variables)) != len(
        variables
    ):
        raise ValueError(
            "Each variable may only be selected once."
        )

    missing = [
        variable
        for variable
        in variables
        if variable
        not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            (
                "Unknown variables: "
                +
                ", ".join(
                    missing
                )
            )
        )

    if requested_method not in {
        "auto",
        "pearson",
        "spearman",
        "kendall",
    }:
        raise ValueError(
            "Invalid correlation method."
        )

    recommendation = (
        recommend_method(
            dataframe,
            variables,
        )
    )

    if (
        requested_method
        ==
        "auto"
    ):
        selected_method = (
            recommendation[
                "method"
            ]
        )

    else:
        selected_method = (
            requested_method
        )

    pair_results = []

    for first_index in range(
        len(variables)
    ):
        for second_index in range(
            first_index + 1,
            len(variables),
        ):
            variable1 = (
                variables[
                    first_index
                ]
            )

            variable2 = (
                variables[
                    second_index
                ]
            )

            result = calculate_pair(
                dataframe=dataframe,
                variable1=variable1,
                variable2=variable2,
                method=selected_method,
                alpha=alpha,
                confidence_level=(
                    confidence_level
                ),
            )

            pair_results.append(
                result
            )

    matrix_rows = build_matrix(
        variables,
        pair_results,
    )

    diagnostic_rows = (
        build_diagnostics(
            dataframe,
            variables,
            selected_method,
            alpha,
        )
    )

    return {
        "test_name":
            "Correlation Analysis",

        "requested_method":
            requested_method,

        "selected_method":
            selected_method,

        "recommendation": {
            "method":
                recommendation[
                    "method"
                ],

            "reason":
                recommendation[
                    "reason"
                ],
        },

        "configuration": {
            "variables":
                variables,

            "method":
                selected_method,

            "alpha":
                alpha,

            "confidence_level":
                confidence_level,
        },

        "tables": [
            {
                "title":
                    "Correlation Matrix",

                "columns": [
                    "Variable",
                    *variables,
                ],

                "rows":
                    matrix_rows,
            },

            {
                "title":
                    "Correlation Significance",

                "columns": [
                    "Variable 1",
                    "Variable 2",
                    "Method",
                    "Coefficient",
                    "p-value",
                    "n",
                    "CI Lower",
                    "CI Upper",
                    "Strength",
                    "Direction",
                    "Significant",
                ],

                "rows":
                    pair_results,
            },
        ],

        "assumptions": {
            "title":
                "Correlation Diagnostics",

            "columns": [
                "Variable",
                "Valid n",
                "Shapiro-Wilk",
                "Normality p",
                "Skewness",
                "Outliers",
                "Outlier %",
                "Status",
            ],

            "rows":
                diagnostic_rows,
        },

        "interpretation":
            build_interpretation(
                pair_results,
                selected_method,
                alpha,
            ),

        "apa":
            build_apa(
                pair_results,
                selected_method,
            ),
    }
