from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# Helpers
# ============================================================


def _safe_float(
    value: Any,
) -> float | None:

    try:
        number = float(value)

        if math.isfinite(number):
            return number

    except (
        TypeError,
        ValueError,
    ):
        pass

    return None


def _round_value(
    value: Any,
    digits: int = 3,
) -> float | None:

    number = _safe_float(
        value
    )

    if number is None:
        return None

    return round(
        number,
        digits,
    )


def _human_chart_name(
    chart_type: str,
) -> str:

    return (
        chart_type
        .replace("_", " ")
        .title()
    )


def _profile_cautions(
    profile: dict[str, Any],
) -> list[str]:

    cautions: list[str] = []

    for warning in profile.get(
        "warnings",
        [],
    ):
        message = warning.get(
            "message"
        )

        if message:
            cautions.append(
                message
            )

    return cautions


def _numeric_series(
    dataframe: pd.DataFrame,
    column: str,
) -> pd.Series:

    if column not in dataframe.columns:
        raise ValueError(
            f"Column '{column}' "
            "does not exist."
        )

    return pd.to_numeric(
        dataframe[column],
        errors="coerce",
    ).dropna()


# ============================================================
# Distribution interpretation
# ============================================================


def _interpret_distribution(
    dataframe: pd.DataFrame,
    chart_type: str,
    config: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:

    column = (
        config.get("x")
        or config.get("y")
    )

    if not column:
        raise ValueError(
            "A numeric column is required "
            "for distribution interpretation."
        )

    values = _numeric_series(
        dataframe,
        column,
    )

    if values.empty:
        raise ValueError(
            f"Column '{column}' does not "
            "contain usable numeric values."
        )

    count = int(
        values.count()
    )

    minimum = _round_value(
        values.min()
    )

    maximum = _round_value(
        values.max()
    )

    mean = _round_value(
        values.mean()
    )

    median = _round_value(
        values.median()
    )

    std = (
        _round_value(
            values.std(
                ddof=1
            )
        )
        if count > 1
        else None
    )

    q1 = _round_value(
        values.quantile(
            0.25
        )
    )

    q3 = _round_value(
        values.quantile(
            0.75
        )
    )

    findings = [
        (
            f"{column} contains "
            f"{count} usable observations."
        ),
        (
            f"Observed values range from "
            f"{minimum} to {maximum}."
        ),
        (
            f"The mean is {mean} and "
            f"the median is {median}."
        ),
    ]

    if (
        mean is not None
        and median is not None
    ):

        difference = abs(
            mean - median
        )

        spread = (
            abs(
                maximum - minimum
            )
            if (
                maximum is not None
                and minimum is not None
            )
            else 0
        )

        if (
            spread > 0
            and difference
            <= spread * 0.10
        ):
            findings.append(
                "The mean and median are "
                "relatively close, suggesting "
                "no large difference between "
                "these two measures of center."
            )

        elif mean > median:
            findings.append(
                "The mean is greater than the "
                "median, which may indicate "
                "some influence from larger "
                "observations."
            )

        elif mean < median:
            findings.append(
                "The mean is lower than the "
                "median, which may indicate "
                "some influence from smaller "
                "observations."
            )

    cautions = _profile_cautions(
        profile
    )

    return {
        "chart_type": chart_type,
        "title": (
            f"{_human_chart_name(chart_type)} "
            f"of {column}"
        ),
        "summary": (
            f"The {_human_chart_name(chart_type).lower()} "
            f"describes the distribution of "
            f"{column}. The observed values "
            f"range from {minimum} to {maximum}, "
            f"with a mean of {mean} and a "
            f"median of {median}."
        ),
        "key_findings": findings,
        "metrics": {
            "variable": column,
            "count": count,
            "minimum": minimum,
            "maximum": maximum,
            "mean": mean,
            "median": median,
            "standard_deviation": std,
            "q1": q1,
            "q3": q3,
        },
        "cautions": cautions,
    }


# ============================================================
# Categorical interpretation
# ============================================================


def _interpret_categorical(
    dataframe: pd.DataFrame,
    chart_type: str,
    config: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:

    column = (
        config.get("x")
        or config.get("category")
    )

    if not column:
        raise ValueError(
            "A categorical column is required."
        )

    if column not in dataframe.columns:
        raise ValueError(
            f"Column '{column}' "
            "does not exist."
        )

    series = dataframe[
        column
    ].dropna()

    counts = series.value_counts()

    if counts.empty:
        raise ValueError(
            f"Column '{column}' does not "
            "contain usable values."
        )

    total = int(
        counts.sum()
    )

    top_category = str(
        counts.index[0]
    )

    top_count = int(
        counts.iloc[0]
    )

    top_percentage = round(
        (
            top_count
            / total
            * 100
        ),
        2,
    )

    category_count = int(
        counts.size
    )

    findings = [
        (
            f"{column} contains "
            f"{category_count} distinct "
            "observed categories."
        ),
        (
            f"The most frequent category is "
            f"'{top_category}' with "
            f"{top_count} observations "
            f"({top_percentage}%)."
        ),
    ]

    breakdown = {
        str(category): int(count)
        for category, count
        in counts.items()
    }

    return {
        "chart_type": chart_type,
        "title": (
            f"{_human_chart_name(chart_type)} "
            f"of {column}"
        ),
        "summary": (
            f"The chart compares the observed "
            f"categories of {column}. "
            f"'{top_category}' is the most "
            f"frequent category, representing "
            f"{top_percentage}% of the "
            "non-missing observations."
        ),
        "key_findings": findings,
        "metrics": {
            "variable": column,
            "total_observations": total,
            "category_count": category_count,
            "most_frequent_category": (
                top_category
            ),
            "most_frequent_count": (
                top_count
            ),
            "most_frequent_percentage": (
                top_percentage
            ),
            "category_counts": (
                breakdown
            ),
        },
        "cautions": _profile_cautions(
            profile
        ),
    }


# ============================================================
# Grouped distribution interpretation
# ============================================================


def _interpret_grouped_distribution(
    dataframe: pd.DataFrame,
    chart_type: str,
    config: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:

    category = config.get(
        "x"
    )

    numeric = config.get(
        "y"
    )

    if (
        not category
        or not numeric
    ):
        return _interpret_distribution(
            dataframe,
            chart_type,
            config,
            profile,
        )

    if (
        category
        not in dataframe.columns
        or numeric
        not in dataframe.columns
    ):
        raise ValueError(
            "Required grouping columns "
            "do not exist."
        )

    working = dataframe[
        [
            category,
            numeric,
        ]
    ].copy()

    working[numeric] = (
        pd.to_numeric(
            working[numeric],
            errors="coerce",
        )
    )

    working = working.dropna()

    if working.empty:
        raise ValueError(
            "No usable grouped numeric "
            "observations were found."
        )

    grouped = (
        working.groupby(
            category
        )[numeric]
        .agg(
            [
                "count",
                "mean",
                "median",
                "min",
                "max",
            ]
        )
    )

    group_metrics = {}

    for group_name, row in (
        grouped.iterrows()
    ):
        group_metrics[
            str(group_name)
        ] = {
            "count": int(
                row["count"]
            ),
            "mean": _round_value(
                row["mean"]
            ),
            "median": _round_value(
                row["median"]
            ),
            "minimum": _round_value(
                row["min"]
            ),
            "maximum": _round_value(
                row["max"]
            ),
        }

    highest_group = (
        grouped["mean"]
        .idxmax()
    )

    lowest_group = (
        grouped["mean"]
        .idxmin()
    )

    highest_mean = _round_value(
        grouped.loc[
            highest_group,
            "mean",
        ]
    )

    lowest_mean = _round_value(
        grouped.loc[
            lowest_group,
            "mean",
        ]
    )

    findings = [
        (
            f"The chart compares {numeric} "
            f"across {len(grouped)} "
            f"categories of {category}."
        ),
        (
            f"'{highest_group}' has the "
            f"highest observed mean "
            f"{numeric} ({highest_mean})."
        ),
        (
            f"'{lowest_group}' has the "
            f"lowest observed mean "
            f"{numeric} ({lowest_mean})."
        ),
    ]

    return {
        "chart_type": chart_type,
        "title": (
            f"{_human_chart_name(chart_type)} "
            f"of {numeric} by {category}"
        ),
        "summary": (
            f"The chart compares the "
            f"distribution of {numeric} "
            f"between categories of "
            f"{category}. The highest "
            f"observed group mean is "
            f"{highest_mean} for "
            f"'{highest_group}'."
        ),
        "key_findings": findings,
        "metrics": {
            "numeric_variable": (
                numeric
            ),
            "group_variable": (
                category
            ),
            "groups": (
                group_metrics
            ),
        },
        "cautions": _profile_cautions(
            profile
        ),
    }


# ============================================================
# Relationship / regression interpretation
# ============================================================


def _interpret_relationship(
    dataframe: pd.DataFrame,
    chart_type: str,
    config: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:

    x = config.get(
        "x"
    )

    y = config.get(
        "y"
    )

    if not x or not y:
        raise ValueError(
            "Both x and y variables "
            "are required."
        )

    if (
        x not in dataframe.columns
        or y not in dataframe.columns
    ):
        raise ValueError(
            "Relationship variables "
            "do not exist."
        )

    working = dataframe[
        [
            x,
            y,
        ]
    ].copy()

    working[x] = pd.to_numeric(
        working[x],
        errors="coerce",
    )

    working[y] = pd.to_numeric(
        working[y],
        errors="coerce",
    )

    working = working.dropna()

    n = int(
        len(
            working
        )
    )

    if n < 2:
        raise ValueError(
            "At least two valid observations "
            "are required."
        )

    correlation = _safe_float(
        working[x].corr(
            working[y]
        )
    )

    slope = None
    intercept = None

    if (
        working[x].nunique()
        > 1
    ):
        coefficients = np.polyfit(
            working[x],
            working[y],
            1,
        )

        slope = _round_value(
            coefficients[0]
        )

        intercept = _round_value(
            coefficients[1]
        )

    rounded_corr = _round_value(
        correlation
    )

    if correlation is None:
        strength = "undetermined"
        direction = "undetermined"

    else:
        absolute = abs(
            correlation
        )

        if absolute >= 0.90:
            strength = "very strong"

        elif absolute >= 0.70:
            strength = "strong"

        elif absolute >= 0.50:
            strength = "moderate"

        elif absolute >= 0.30:
            strength = "weak"

        else:
            strength = "very weak"

        if correlation > 0:
            direction = "positive"

        elif correlation < 0:
            direction = "negative"

        else:
            direction = "no linear"

    findings = [
        (
            f"The observed linear association "
            f"between {x} and {y} is "
            f"{strength} and {direction}."
        ),
    ]

    if rounded_corr is not None:
        findings.append(
            f"The Pearson correlation "
            f"coefficient is {rounded_corr}."
        )

    if slope is not None:
        findings.append(
            f"The fitted linear slope is "
            f"{slope}, meaning the fitted "
            f"value of {y} changes by about "
            f"{slope} units for each one-unit "
            f"increase in {x}."
        )

    cautions = _profile_cautions(
        profile
    )

    causation_warning = (
        "Association or correlation does "
        "not by itself establish a causal "
        "relationship."
    )

    if causation_warning not in cautions:
        cautions.append(
            causation_warning
        )

    return {
        "chart_type": chart_type,
        "title": (
            f"{_human_chart_name(chart_type)}: "
            f"{y} vs {x}"
        ),
        "summary": (
            f"The chart examines the "
            f"relationship between {x} and "
            f"{y}. The observed linear "
            f"association is {strength} and "
            f"{direction}"
            + (
                f" (r = {rounded_corr})."
                if rounded_corr is not None
                else "."
            )
        ),
        "key_findings": findings,
        "metrics": {
            "x_variable": x,
            "y_variable": y,
            "observations": n,
            "correlation": (
                rounded_corr
            ),
            "relationship_strength": (
                strength
            ),
            "direction": (
                direction
            ),
            "slope": slope,
            "intercept": intercept,
        },
        "cautions": cautions,
    }


# ============================================================
# Correlation heatmap interpretation
# ============================================================


def _interpret_correlation_heatmap(
    dataframe: pd.DataFrame,
    chart_type: str,
    config: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:

    columns = config.get(
        "columns"
    )

    if not columns:
        columns = profile.get(
            "numeric_columns",
            [],
        )

    columns = [
        column
        for column in columns
        if column in dataframe.columns
    ]

    if len(columns) < 2:
        raise ValueError(
            "At least two numeric variables "
            "are required."
        )

    numeric_data = dataframe[
        columns
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    correlation_matrix = (
        numeric_data.corr()
    )

    strongest_pair = None
    strongest_value = None

    for index, column_a in enumerate(
        columns
    ):
        for column_b in columns[
            index + 1:
        ]:

            value = correlation_matrix.loc[
                column_a,
                column_b,
            ]

            if pd.isna(
                value
            ):
                continue

            if (
                strongest_value is None
                or abs(value)
                > abs(strongest_value)
            ):
                strongest_value = float(
                    value
                )

                strongest_pair = (
                    column_a,
                    column_b,
                )

    findings = [
        (
            f"The heatmap compares linear "
            f"relationships among "
            f"{len(columns)} numeric variables."
        )
    ]

    if (
        strongest_pair
        and strongest_value is not None
    ):

        column_a, column_b = (
            strongest_pair
        )

        rounded = _round_value(
            strongest_value
        )

        direction = (
            "positive"
            if strongest_value > 0
            else "negative"
            if strongest_value < 0
            else "no linear"
        )

        findings.append(
            f"The strongest observed pair is "
            f"{column_a} and {column_b}, with "
            f"a {direction} correlation of "
            f"{rounded}."
        )

        summary = (
            f"The correlation heatmap summarizes "
            f"linear relationships among "
            f"{', '.join(columns)}. "
            f"The strongest observed relationship "
            f"is between {column_a} and "
            f"{column_b} (r = {rounded})."
        )

    else:
        summary = (
            "The correlation heatmap compares "
            "the numeric variables, but no "
            "usable pairwise correlation could "
            "be determined."
        )

    cautions = _profile_cautions(
        profile
    )

    cautions.append(
        "Correlation measures linear "
        "association and does not establish "
        "causation."
    )

    matrix = {}

    for column in columns:
        matrix[column] = {
            other: _round_value(
                correlation_matrix.loc[
                    column,
                    other,
                ]
            )
            for other in columns
        }

    return {
        "chart_type": chart_type,
        "title": (
            "Correlation Heatmap Interpretation"
        ),
        "summary": summary,
        "key_findings": findings,
        "metrics": {
            "variables": columns,
            "strongest_pair": (
                list(
                    strongest_pair
                )
                if strongest_pair
                else None
            ),
            "strongest_correlation": (
                _round_value(
                    strongest_value
                )
                if strongest_value
                is not None
                else None
            ),
            "correlation_matrix": (
                matrix
            ),
        },
        "cautions": cautions,
    }


# ============================================================
# Time-series interpretation
# ============================================================


def _interpret_time_series(
    dataframe: pd.DataFrame,
    chart_type: str,
    config: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:

    x = config.get(
        "x"
    )

    y = config.get(
        "y"
    )

    if not x or not y:
        raise ValueError(
            "Time-series interpretation "
            "requires x and y."
        )

    working = dataframe[
        [
            x,
            y,
        ]
    ].copy()

    working[x] = pd.to_datetime(
        working[x],
        errors="coerce",
    )

    working[y] = pd.to_numeric(
        working[y],
        errors="coerce",
    )

    working = (
        working
        .dropna()
        .sort_values(
            x
        )
    )

    if working.empty:
        raise ValueError(
            "No usable time-series "
            "observations were found."
        )

    first_value = _safe_float(
        working[y].iloc[0]
    )

    last_value = _safe_float(
        working[y].iloc[-1]
    )

    change = None
    percentage_change = None

    if (
        first_value is not None
        and last_value is not None
    ):

        change = (
            last_value
            - first_value
        )

        if first_value != 0:
            percentage_change = (
                change
                / abs(first_value)
                * 100
            )

    if change is None:
        direction = "undetermined"

    elif change > 0:
        direction = "increased"

    elif change < 0:
        direction = "decreased"

    else:
        direction = "remained unchanged"

    first_date = (
        working[x]
        .iloc[0]
        .isoformat()
    )

    last_date = (
        working[x]
        .iloc[-1]
        .isoformat()
    )

    findings = [
        (
            f"{y} {direction} between "
            f"the first and last observed "
            "time points."
        ),
        (
            f"The first observed value is "
            f"{_round_value(first_value)} and "
            f"the last observed value is "
            f"{_round_value(last_value)}."
        ),
    ]

    if percentage_change is not None:
        findings.append(
            f"The overall observed percentage "
            f"change is approximately "
            f"{round(percentage_change, 2)}%."
        )

    return {
        "chart_type": chart_type,
        "title": (
            f"{_human_chart_name(chart_type)} "
            f"of {y} over {x}"
        ),
        "summary": (
            f"The chart shows how {y} changes "
            f"over {x}. Across the observed "
            f"period, the measure {direction} "
            f"from {_round_value(first_value)} "
            f"to {_round_value(last_value)}."
        ),
        "key_findings": findings,
        "metrics": {
            "time_variable": x,
            "value_variable": y,
            "observations": int(
                len(
                    working
                )
            ),
            "first_date": first_date,
            "last_date": last_date,
            "first_value": (
                _round_value(
                    first_value
                )
            ),
            "last_value": (
                _round_value(
                    last_value
                )
            ),
            "absolute_change": (
                _round_value(
                    change
                )
                if change is not None
                else None
            ),
            "percentage_change": (
                round(
                    percentage_change,
                    2,
                )
                if percentage_change
                is not None
                else None
            ),
        },
        "cautions": _profile_cautions(
            profile
        ),
    }


# ============================================================
# Missing-value interpretation
# ============================================================


def _interpret_missing_values(
    dataframe: pd.DataFrame,
    chart_type: str,
    profile: dict[str, Any],
) -> dict[str, Any]:

    missing_counts = (
        dataframe
        .isna()
        .sum()
    )

    total_missing = int(
        missing_counts.sum()
    )

    affected = (
        missing_counts[
            missing_counts > 0
        ]
    )

    findings: list[str] = []

    if affected.empty:

        findings.append(
            "No missing values were detected "
            "in the dataset."
        )

        summary = (
            "The dataset does not contain "
            "missing values."
        )

    else:

        most_affected = (
            affected.idxmax()
        )

        most_count = int(
            affected.max()
        )

        findings.append(
            f"{len(affected)} columns contain "
            "at least one missing value."
        )

        findings.append(
            f"{most_affected} contains the "
            f"largest number of missing "
            f"values ({most_count})."
        )

        summary = (
            f"The dataset contains "
            f"{total_missing} missing values "
            f"across {len(affected)} columns."
        )

    percentages = {}

    row_count = len(
        dataframe
    )

    for column, count in (
        affected.items()
    ):

        percentages[
            str(column)
        ] = round(
            (
                int(count)
                / row_count
                * 100
            )
            if row_count
            else 0,
            2,
        )

    return {
        "chart_type": chart_type,
        "title": (
            "Missing Values Interpretation"
        ),
        "summary": summary,
        "key_findings": findings,
        "metrics": {
            "total_missing_values": (
                total_missing
            ),
            "affected_columns": (
                int(
                    len(
                        affected
                    )
                )
            ),
            "missing_counts": {
                str(column): int(count)
                for column, count
                in affected.items()
            },
            "missing_percentages": (
                percentages
            ),
        },
        "cautions": [],
    }


# ============================================================
# Generic interpretation
# ============================================================


def _interpret_generic(
    dataframe: pd.DataFrame,
    chart_type: str,
    config: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:

    selected_columns = []

    for key in (
        "x",
        "y",
        "category",
        "group_by",
    ):
        value = config.get(
            key
        )

        if isinstance(
            value,
            str,
        ):
            selected_columns.append(
                value
            )

    columns_value = config.get(
        "columns"
    )

    if isinstance(
        columns_value,
        list,
    ):
        selected_columns.extend(
            columns_value
        )

    selected_columns = list(
        dict.fromkeys(
            selected_columns
        )
    )

    return {
        "chart_type": chart_type,
        "title": (
            f"{_human_chart_name(chart_type)} "
            "Interpretation"
        ),
        "summary": (
            f"The {_human_chart_name(chart_type).lower()} "
            f"visualizes selected information "
            f"from a dataset containing "
            f"{len(dataframe)} rows and "
            f"{len(dataframe.columns)} columns."
        ),
        "key_findings": [
            (
                "Variables used in the "
                f"visualization: "
                f"{', '.join(selected_columns)}."
                if selected_columns
                else (
                    "The visualization summarizes "
                    "the supplied dataset."
                )
            )
        ],
        "metrics": {
            "row_count": int(
                len(
                    dataframe
                )
            ),
            "column_count": int(
                len(
                    dataframe.columns
                )
            ),
            "variables": (
                selected_columns
            ),
        },
        "cautions": _profile_cautions(
            profile
        ),
    }


# ============================================================
# Public interpretation function
# ============================================================


def interpret_visualization(
    dataframe: pd.DataFrame,
    recommendation: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:

    chart_type = recommendation.get(
        "chart_type",
        "",
    )

    config = recommendation.get(
        "suggested_config",
        {},
    )

    if not chart_type:
        raise ValueError(
            "Visualization type is missing."
        )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    if chart_type in {
        "missing_values_bar",
        "missing_values_heatmap",
    }:
        return _interpret_missing_values(
            dataframe,
            chart_type,
            profile,
        )

    # --------------------------------------------------------
    # Correlation
    # --------------------------------------------------------

    if chart_type == (
        "correlation_heatmap"
    ):
        return (
            _interpret_correlation_heatmap(
                dataframe,
                chart_type,
                config,
                profile,
            )
        )

    # --------------------------------------------------------
    # Relationship / regression
    # --------------------------------------------------------

    if chart_type in {
        "scatter",
        "bubble",
        "regression_line",
        "actual_vs_predicted",
        "residual_vs_fitted",
    }:
        return _interpret_relationship(
            dataframe,
            chart_type,
            config,
            profile,
        )

    # --------------------------------------------------------
    # Time series
    # --------------------------------------------------------

    if chart_type in {
        "line",
        "area",
        "moving_average",
        "step",
        "stacked_area",
    }:
        return _interpret_time_series(
            dataframe,
            chart_type,
            config,
            profile,
        )

    # --------------------------------------------------------
    # Grouped distribution
    # --------------------------------------------------------

    if chart_type in {
        "box",
        "violin",
    }:

        if (
            config.get("x")
            and config.get("y")
        ):
            return (
                _interpret_grouped_distribution(
                    dataframe,
                    chart_type,
                    config,
                    profile,
                )
            )

        return _interpret_distribution(
            dataframe,
            chart_type,
            config,
            profile,
        )

    # --------------------------------------------------------
    # Numeric distribution
    # --------------------------------------------------------

    if chart_type in {
        "histogram",
        "density",
        "ecdf",
        "frequency_polygon",
    }:
        return _interpret_distribution(
            dataframe,
            chart_type,
            config,
            profile,
        )

    # --------------------------------------------------------
    # Categorical
    # --------------------------------------------------------

    if chart_type in {
        "bar",
        "horizontal_bar",
        "pie",
        "donut",
    }:
        return _interpret_categorical(
            dataframe,
            chart_type,
            config,
            profile,
        )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return _interpret_generic(
        dataframe,
        chart_type,
        config,
        profile,
    )
