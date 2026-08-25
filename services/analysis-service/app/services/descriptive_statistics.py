import math

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew


def clean_value(value):
    """
    Convert NumPy/Pandas values into JSON-compatible values.
    """

    if pd.isna(value):
        return None

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        if not np.isfinite(value):
            return None
        return float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, np.ndarray):
        return value.tolist()

    return value


def calculate_mode(series: pd.Series):
    mode_values = series.dropna().mode()

    if mode_values.empty:
        return None

    return [clean_value(value) for value in mode_values.tolist()]


def calculate_numeric_statistics(series: pd.Series):
    numeric = pd.to_numeric(series, errors="coerce")

    total_count = len(numeric)
    missing_count = int(numeric.isna().sum())

    valid = numeric.dropna()

    if valid.empty:
        return {
            "data_type": "numeric",
            "count": total_count,
            "valid_count": 0,
            "missing_count": missing_count,
            "missing_percentage": (
                round((missing_count / total_count) * 100, 4)
                if total_count
                else 0
            ),
        }

    mean_value = valid.mean()
    median_value = valid.median()

    variance_value = (
        valid.var(ddof=1)
        if len(valid) > 1
        else 0
    )

    std_value = (
        valid.std(ddof=1)
        if len(valid) > 1
        else 0
    )

    minimum = valid.min()
    maximum = valid.max()

    range_value = maximum - minimum

    q1 = valid.quantile(0.25)
    q2 = valid.quantile(0.50)
    q3 = valid.quantile(0.75)

    iqr = q3 - q1

    sum_value = valid.sum()

    skewness_value = (
        skew(valid, bias=False)
        if len(valid) > 2
        else 0
    )

    kurtosis_value = (
        kurtosis(
            valid,
            fisher=True,
            bias=False,
        )
        if len(valid) > 3
        else 0
    )

    coefficient_variation = (
        (std_value / abs(mean_value)) * 100
        if mean_value != 0
        else None
    )

    percentiles = {
        "1%": clean_value(valid.quantile(0.01)),
        "5%": clean_value(valid.quantile(0.05)),
        "10%": clean_value(valid.quantile(0.10)),
        "25%": clean_value(valid.quantile(0.25)),
        "50%": clean_value(valid.quantile(0.50)),
        "75%": clean_value(valid.quantile(0.75)),
        "90%": clean_value(valid.quantile(0.90)),
        "95%": clean_value(valid.quantile(0.95)),
        "99%": clean_value(valid.quantile(0.99)),
    }

    return {
        "data_type": "numeric",

        "count": total_count,
        "valid_count": len(valid),

        "missing_count": missing_count,
        "missing_percentage": round(
            (missing_count / total_count) * 100,
            4,
        ) if total_count else 0,

        "unique_count": int(valid.nunique()),

        "mean": clean_value(mean_value),
        "median": clean_value(median_value),
        "mode": calculate_mode(valid),

        "sum": clean_value(sum_value),

        "minimum": clean_value(minimum),
        "maximum": clean_value(maximum),
        "range": clean_value(range_value),

        "variance": clean_value(variance_value),
        "standard_deviation": clean_value(std_value),

        "q1": clean_value(q1),
        "q2": clean_value(q2),
        "q3": clean_value(q3),

        "iqr": clean_value(iqr),

        "skewness": clean_value(skewness_value),
        "kurtosis": clean_value(kurtosis_value),

        "coefficient_of_variation": clean_value(
            coefficient_variation
        ),

        "percentiles": percentiles,
    }


def calculate_categorical_statistics(series: pd.Series):
    total_count = len(series)

    missing_count = int(series.isna().sum())

    valid = series.dropna()

    unique_count = int(valid.nunique())

    mode_values = calculate_mode(valid)

    frequencies = valid.value_counts(dropna=False)

    frequency_distribution = []

    for value, count in frequencies.items():
        percentage = (
            (count / len(valid)) * 100
            if len(valid)
            else 0
        )

        frequency_distribution.append(
            {
                "value": clean_value(value),
                "frequency": int(count),
                "percentage": round(
                    percentage,
                    4,
                ),
            }
        )

    return {
        "data_type": "categorical",

        "count": total_count,
        "valid_count": len(valid),

        "missing_count": missing_count,
        "missing_percentage": round(
            (missing_count / total_count) * 100,
            4,
        ) if total_count else 0,

        "unique_count": unique_count,

        "mode": mode_values,

        "frequency_distribution": frequency_distribution,
    }


def analyze_dataframe(df: pd.DataFrame):
    """
    Perform complete descriptive analysis
    on a Pandas DataFrame.
    """

    numeric_columns = []
    categorical_columns = []

    column_statistics = {}

    for column in df.columns:

        series = df[column]

        if pd.api.types.is_numeric_dtype(series):
            numeric_columns.append(column)

            column_statistics[column] = (
                calculate_numeric_statistics(series)
            )

        else:
            categorical_columns.append(column)

            column_statistics[column] = (
                calculate_categorical_statistics(series)
            )

    duplicate_rows = int(df.duplicated().sum())

    total_cells = int(df.shape[0] * df.shape[1])

    missing_cells = int(df.isna().sum().sum())

    return {
        "dataset_summary": {
            "row_count": int(df.shape[0]),
            "column_count": int(df.shape[1]),

            "numeric_column_count": len(
                numeric_columns
            ),

            "categorical_column_count": len(
                categorical_columns
            ),

            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,

            "total_cells": total_cells,
            "missing_cells": missing_cells,

            "missing_percentage": round(
                (missing_cells / total_cells) * 100,
                4,
            ) if total_cells else 0,

            "duplicate_rows": duplicate_rows,

            "duplicate_percentage": round(
                (duplicate_rows / len(df)) * 100,
                4,
            ) if len(df) else 0,
        },

        "columns": column_statistics,
    }
