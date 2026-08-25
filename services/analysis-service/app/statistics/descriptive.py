import math
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def safe_float(value):
    """
    Convert NumPy/scipy values into JSON-compatible floats.
    """
    if value is None:
        return None

    try:
        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def calculate_mode(series: pd.Series):
    modes = series.mode()

    if modes.empty:
        return None

    return [
        value.item() if hasattr(value, "item") else value
        for value in modes.tolist()
    ]


def calculate_weighted_mean(series: pd.Series):
    """
    Currently uses equal weights.

    A future version can accept a separate weight column.
    """
    return safe_float(series.mean())


def calculate_geometric_mean(series: pd.Series):
    values = series.dropna().astype(float)

    if len(values) == 0:
        return None

    if (values <= 0).any():
        return None

    return safe_float(stats.gmean(values))


def calculate_harmonic_mean(series: pd.Series):
    values = series.dropna().astype(float)

    if len(values) == 0:
        return None

    if (values <= 0).any():
        return None

    return safe_float(stats.hmean(values))


def calculate_confidence_interval(
    series: pd.Series,
    confidence_level: float,
):
    values = series.dropna().astype(float)

    n = len(values)

    if n < 2:
        return {
            "lower": None,
            "upper": None,
            "confidence_level": confidence_level,
        }

    mean = values.mean()

    standard_error = stats.sem(values)

    alpha = 1 - confidence_level

    interval = stats.t.interval(
        confidence_level,
        df=n - 1,
        loc=mean,
        scale=standard_error,
    )

    return {
        "lower": safe_float(interval[0]),
        "upper": safe_float(interval[1]),
        "confidence_level": confidence_level,
    }


def calculate_outliers(series: pd.Series):
    values = series.dropna().astype(float)

    if values.empty:
        return {
            "lower_bound": None,
            "upper_bound": None,
            "lower_outliers": 0,
            "upper_outliers": 0,
            "total_outliers": 0,
            "outlier_percentage": 0,
        }

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)

    iqr = q3 - q1

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    lower = values[values < lower_bound]
    upper = values[values > upper_bound]

    total = len(lower) + len(upper)

    return {
        "lower_bound": safe_float(lower_bound),
        "upper_bound": safe_float(upper_bound),
        "lower_outliers": int(len(lower)),
        "upper_outliers": int(len(upper)),
        "total_outliers": int(total),
        "outlier_percentage": safe_float(
            (total / len(values)) * 100
        ),
    }


def numeric_statistics(
    series: pd.Series,
    confidence_level: float = 0.95,
):
    values = series.dropna().astype(float)

    n = len(values)

    if n == 0:
        return {
            "data_type": "numeric",
            "count": 0,
        }

    mean = values.mean()

    median = values.median()

    variance = values.var(ddof=1) if n > 1 else 0

    standard_deviation = (
        values.std(ddof=1)
        if n > 1
        else 0
    )

    standard_error = (
        standard_deviation / math.sqrt(n)
        if n > 0
        else None
    )

    minimum = values.min()
    maximum = values.max()

    data_range = maximum - minimum

    mad = np.mean(
        np.abs(values - mean)
    )

    q1 = values.quantile(0.25)
    q2 = values.quantile(0.50)
    q3 = values.quantile(0.75)

    iqr = q3 - q1

    quartile_deviation = iqr / 2

    coefficient_variation = (
        (standard_deviation / mean) * 100
        if mean != 0
        else None
    )

    skewness = (
        values.skew()
        if n >= 3
        else None
    )

    kurtosis = (
        values.kurt()
        if n >= 4
        else None
    )

    percentile_values = {
        "p1": values.quantile(0.01),
        "p5": values.quantile(0.05),
        "p10": values.quantile(0.10),
        "p20": values.quantile(0.20),
        "p25": values.quantile(0.25),
        "p50": values.quantile(0.50),
        "p75": values.quantile(0.75),
        "p80": values.quantile(0.80),
        "p90": values.quantile(0.90),
        "p95": values.quantile(0.95),
        "p99": values.quantile(0.99),
    }

    deciles = {
        f"d{i}": values.quantile(i / 10)
        for i in range(1, 10)
    }

    return {
        "data_type": "numeric",

        "count": int(n),

        "missing": int(series.isna().sum()),

        "missing_percentage": safe_float(
            series.isna().mean() * 100
        ),

        "unique_values": int(
            series.nunique(dropna=True)
        ),

        "central_tendency": {
            "mean": safe_float(mean),
            "median": safe_float(median),
            "mode": calculate_mode(series),
            "weighted_mean": calculate_weighted_mean(values),
            "geometric_mean": calculate_geometric_mean(values),
            "harmonic_mean": calculate_harmonic_mean(values),
        },

        "dispersion": {
            "minimum": safe_float(minimum),
            "maximum": safe_float(maximum),
            "range": safe_float(data_range),
            "variance": safe_float(variance),
            "standard_deviation": safe_float(
                standard_deviation
            ),
            "mean_absolute_deviation": safe_float(mad),
            "interquartile_range": safe_float(iqr),
            "quartile_deviation": safe_float(
                quartile_deviation
            ),
            "coefficient_of_variation": safe_float(
                coefficient_variation
            ),
        },

        "quartiles": {
            "q1": safe_float(q1),
            "q2": safe_float(q2),
            "q3": safe_float(q3),
        },

        "percentiles": {
            key: safe_float(value)
            for key, value in percentile_values.items()
        },

        "deciles": {
            key: safe_float(value)
            for key, value in deciles.items()
        },

        "distribution": {
            "skewness": safe_float(skewness),
            "kurtosis": safe_float(kurtosis),
            "excess_kurtosis": safe_float(kurtosis),
        },

        "five_number_summary": {
            "minimum": safe_float(minimum),
            "q1": safe_float(q1),
            "median": safe_float(median),
            "q3": safe_float(q3),
            "maximum": safe_float(maximum),
        },

        "standardization": {
            "standard_error": safe_float(
                standard_error
            ),
            "confidence_interval": calculate_confidence_interval(
                values,
                confidence_level,
            ),
        },

        "outliers": calculate_outliers(values),
    }


def categorical_statistics(series: pd.Series):
    values = series.dropna()

    count = len(values)

    frequencies = (
        values.value_counts(dropna=False)
    )

    percentages = (
        values.value_counts(
            normalize=True,
            dropna=False,
        ) * 100
    )

    frequency_table = []

    cumulative = 0

    for category, frequency in frequencies.items():

        percentage = percentages[category]

        cumulative += percentage

        frequency_table.append(
            {
                "value": str(category),
                "frequency": int(frequency),
                "percentage": safe_float(
                    percentage
                ),
                "cumulative_percentage": safe_float(
                    cumulative
                ),
            }
        )

    modes = values.mode()

    mode_values = [
        str(value)
        for value in modes.tolist()
    ]

    return {
        "data_type": "categorical",

        "count": int(count),

        "missing": int(series.isna().sum()),

        "missing_percentage": safe_float(
            series.isna().mean() * 100
        ),

        "unique_values": int(
            series.nunique(dropna=True)
        ),

        "mode": mode_values,

        "frequency_table": frequency_table,
    }


def calculate_descriptive_statistics(
    dataframe: pd.DataFrame,
    columns: list[str] | None = None,
    confidence_level: float = 0.95,
):
    if not 0 < confidence_level < 1:
        raise ValueError(
            "Confidence level must be between 0 and 1."
        )

    if columns is None:
        columns = dataframe.columns.tolist()

    missing_columns = [
        column
        for column in columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Columns not found: {missing_columns}"
        )

    results = {}

    for column in columns:

        series = dataframe[column]

        if pd.api.types.is_numeric_dtype(series):
            results[column] = numeric_statistics(
                series,
                confidence_level,
            )

        else:
            results[column] = categorical_statistics(
                series
            )

    return results
