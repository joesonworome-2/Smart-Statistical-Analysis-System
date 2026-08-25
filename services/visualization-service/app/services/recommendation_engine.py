from __future__ import annotations

from typing import Any

import pandas as pd


# ============================================================
# Column detection keywords
# ============================================================

DATE_KEYWORDS = (
    "date",
    "time",
    "year",
    "month",
    "day",
    "timestamp",
)

IDENTIFIER_KEYWORDS = (
    "id",
    "uuid",
    "code",
    "identifier",
)

IDENTIFIER_EXACT_NAMES = {
    "name",
    "full_name",
    "first_name",
    "last_name",
    "student_name",
    "employee_name",
    "customer_name",
    "client_name",
    "patient_name",
    "username",
    "user_name",
    "email",
    "email_address",
    "phone",
    "phone_number",
}


# ============================================================
# Detect datetime columns
# ============================================================

def _looks_like_datetime(
    series: pd.Series,
    column_name: str,
) -> bool:

    name = (
        column_name
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

    if pd.api.types.is_datetime64_any_dtype(
        series
    ):
        return True

    if any(
        keyword in name
        for keyword in DATE_KEYWORDS
    ):
        try:
            parsed = pd.to_datetime(
                series,
                errors="coerce",
            )

            return (
                parsed.notna().mean()
                >= 0.60
            )

        except Exception:
            return False

    if series.dtype == "object":
        try:
            parsed = pd.to_datetime(
                series,
                errors="coerce",
            )

            return (
                parsed.notna().mean()
                >= 0.85
            )

        except Exception:
            return False

    return False


# ============================================================
# Detect identifier / label columns
# ============================================================

def _looks_like_identifier(
    series: pd.Series,
    column_name: str,
) -> bool:

    name = (
        column_name
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

    # --------------------------------------------------------
    # Common human-readable identifier / label fields
    # --------------------------------------------------------

    if name in IDENTIFIER_EXACT_NAMES:
        return True

    # --------------------------------------------------------
    # Explicit ID-style fields
    # --------------------------------------------------------

    if (
        name == "id"
        or name.endswith("_id")
        or name.startswith("id_")
        or name.endswith("_uuid")
        or name.endswith("_code")
        or name.endswith("_identifier")
    ):
        return True

    if name in IDENTIFIER_KEYWORDS:
        return True

    non_null = series.dropna()

    if len(non_null) == 0:
        return False

    uniqueness = (
        non_null.nunique()
        / len(non_null)
    )

    # --------------------------------------------------------
    # High-cardinality text is often an identifier
    #
    # Example:
    # registration numbers, emails, names, codes, etc.
    # --------------------------------------------------------

    if (
        series.dtype == "object"
        and uniqueness >= 0.98
        and len(non_null) >= 20
    ):
        return True

    return False


# ============================================================
# Dataset profiling
# ============================================================

def profile_dataset(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:

    numeric_columns: list[str] = []
    categorical_columns: list[str] = []
    datetime_columns: list[str] = []
    boolean_columns: list[str] = []
    identifier_columns: list[str] = []

    # --------------------------------------------------------
    # Detect column types
    # --------------------------------------------------------

    for column in dataframe.columns:

        series = dataframe[column]

        if _looks_like_identifier(
            series,
            column,
        ):
            identifier_columns.append(
                column
            )
            continue

        if _looks_like_datetime(
            series,
            column,
        ):
            datetime_columns.append(
                column
            )
            continue

        if pd.api.types.is_bool_dtype(
            series
        ):
            boolean_columns.append(
                column
            )

            categorical_columns.append(
                column
            )

            continue

        if pd.api.types.is_numeric_dtype(
            series
        ):
            numeric_columns.append(
                column
            )
            continue

        categorical_columns.append(
            column
        )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    missing_values = {
        column: int(
            dataframe[column]
            .isna()
            .sum()
        )
        for column in dataframe.columns
        if (
            dataframe[column]
            .isna()
            .sum()
            > 0
        )
    }

    # --------------------------------------------------------
    # High-cardinality categorical variables
    # --------------------------------------------------------

    high_cardinality_columns = []

    for column in categorical_columns:

        unique_count = dataframe[
            column
        ].nunique(
            dropna=True
        )

        if unique_count > 20:
            high_cardinality_columns.append(
                column
            )

    # --------------------------------------------------------
    # Detect strong numeric correlations
    # --------------------------------------------------------

    strong_correlations = []

    if len(numeric_columns) >= 2:

        correlation_matrix = (
            dataframe[
                numeric_columns
            ]
            .corr(
                numeric_only=True
            )
        )

        for i, column_a in enumerate(
            numeric_columns
        ):

            for column_b in (
                numeric_columns[
                    i + 1:
                ]
            ):

                correlation_value = (
                    correlation_matrix.loc[
                        column_a,
                        column_b,
                    ]
                )

                if (
                    pd.notna(
                        correlation_value
                    )
                    and abs(
                        correlation_value
                    ) >= 0.70
                ):
                    strong_correlations.append(
                        {
                            "column_1": (
                                column_a
                            ),
                            "column_2": (
                                column_b
                            ),
                            "correlation": float(
                                correlation_value
                            ),
                        }
                    )

    # --------------------------------------------------------
    # Statistical warnings
    # --------------------------------------------------------

    warnings: list[
        dict[str, Any]
    ] = []

    row_count = len(
        dataframe
    )

    if row_count < 10:

        warnings.append(
            {
                "type": (
                    "very_small_sample"
                ),
                "severity": "high",
                "message": (
                    "Very small sample size "
                    "detected. Correlation, "
                    "regression and other "
                    "inferential results should "
                    "be interpreted with caution."
                ),
                "row_count": int(
                    row_count
                ),
            }
        )

    elif row_count < 30:

        warnings.append(
            {
                "type": (
                    "small_sample"
                ),
                "severity": "medium",
                "message": (
                    "Small sample size detected. "
                    "Statistical relationships "
                    "may be unstable and should "
                    "be interpreted cautiously."
                ),
                "row_count": int(
                    row_count
                ),
            }
        )

    # --------------------------------------------------------
    # Return dataset profile
    # --------------------------------------------------------

    return {
        "row_count": int(
            row_count
        ),
        "column_count": int(
            len(
                dataframe.columns
            )
        ),
        "numeric_columns": (
            numeric_columns
        ),
        "categorical_columns": (
            categorical_columns
        ),
        "datetime_columns": (
            datetime_columns
        ),
        "boolean_columns": (
            boolean_columns
        ),
        "identifier_columns": (
            identifier_columns
        ),
        "high_cardinality_columns": (
            high_cardinality_columns
        ),
        "missing_values": (
            missing_values
        ),
        "strong_correlations": (
            strong_correlations
        ),
        "warnings": warnings,
    }


# ============================================================
# Recommendation helper
# ============================================================

def _recommendation(
    chart_type: str,
    score: float,
    reason: str,
    config: dict[str, Any],
    category: str,
) -> dict[str, Any]:

    normalized_score = min(
        max(
            score,
            0.0,
        ),
        1.0,
    )

    return {
        "chart_type": chart_type,
        "score": round(
            normalized_score,
            2,
        ),
        "confidence_percent": int(
            round(
                normalized_score
                * 100
            )
        ),
        "category": category,
        "reason": reason,
        "suggested_config": config,
    }


# ============================================================
# Smart visualization recommendation engine
# ============================================================

def recommend_visualizations(
    dataframe: pd.DataFrame,
    goal: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:

    # --------------------------------------------------------
    # Profile dataset
    # --------------------------------------------------------

    profile = profile_dataset(
        dataframe
    )

    numeric = profile[
        "numeric_columns"
    ]

    categorical = profile[
        "categorical_columns"
    ]

    dates = profile[
        "datetime_columns"
    ]

    missing = profile[
        "missing_values"
    ]

    strong_correlations = profile[
        "strong_correlations"
    ]

    sample_size = profile[
        "row_count"
    ]

    # --------------------------------------------------------
    # Sample-size penalty
    #
    # Relationship / correlation visualizations are still
    # available, but their recommendation confidence is
    # reduced when the dataset is very small.
    # --------------------------------------------------------

    if sample_size < 10:

        relationship_penalty = (
            0.15
        )

    elif sample_size < 30:

        relationship_penalty = (
            0.08
        )

    else:

        relationship_penalty = (
            0.0
        )

    recommendations: list[
        dict[str, Any]
    ] = []

    # --------------------------------------------------------
    # Normalize goal
    # --------------------------------------------------------

    goal = (
        goal.lower().strip()
        if goal
        else "automatic"
    )

    # ========================================================
    # DATA QUALITY
    # ========================================================

    if missing:

        recommendations.append(
            _recommendation(
                "missing_values_bar",
                0.99,
                (
                    "The dataset contains "
                    "missing values. A missing-"
                    "values bar chart clearly "
                    "shows which variables are "
                    "affected."
                ),
                {},
                "data_quality",
            )
        )

        recommendations.append(
            _recommendation(
                "missing_values_heatmap",
                0.96,
                (
                    "A missing-values heatmap "
                    "can reveal patterns of "
                    "missingness across rows "
                    "and variables."
                ),
                {},
                "data_quality",
            )
        )

    # ========================================================
    # SINGLE NUMERIC VARIABLE
    # ========================================================

    if numeric:

        column = numeric[0]

        recommendations.extend(
            [
                _recommendation(
                    "histogram",
                    0.92,
                    (
                        f"{column} is numeric. "
                        "A histogram is suitable "
                        "for examining its "
                        "distribution."
                    ),
                    {
                        "x": column,
                        "bins": 20,
                    },
                    "distribution",
                ),
                _recommendation(
                    "box",
                    0.87,
                    (
                        f"A box plot of {column} "
                        "helps identify spread, "
                        "median and potential "
                        "outliers."
                    ),
                    {
                        "y": column,
                    },
                    "distribution",
                ),
                _recommendation(
                    "density",
                    0.82,
                    (
                        f"A density view provides "
                        f"a smooth representation "
                        f"of the distribution of "
                        f"{column}."
                    ),
                    {
                        "x": column,
                    },
                    "distribution",
                ),
                _recommendation(
                    "ecdf",
                    0.78,
                    (
                        f"An ECDF shows the "
                        f"cumulative distribution "
                        f"of {column} without "
                        f"requiring bins."
                    ),
                    {
                        "x": column,
                    },
                    "distribution",
                ),
            ]
        )

    # ========================================================
    # SINGLE CATEGORICAL VARIABLE
    # ========================================================

    if categorical:

        column = categorical[0]

        unique_count = dataframe[
            column
        ].nunique(
            dropna=True
        )

        recommendations.append(
            _recommendation(
                "bar",
                0.91,
                (
                    f"{column} is categorical. "
                    "A bar chart is appropriate "
                    "for comparing category "
                    "frequencies."
                ),
                {
                    "x": column,
                },
                "comparison",
            )
        )

        if unique_count <= 10:

            recommendations.extend(
                [
                    _recommendation(
                        "pie",
                        0.75,
                        (
                            f"{column} has "
                            f"{unique_count} "
                            "categories, making "
                            "a pie chart suitable "
                            "for showing category "
                            "composition."
                        ),
                        {
                            "category": (
                                column
                            ),
                        },
                        "composition",
                    ),
                    _recommendation(
                        "donut",
                        0.73,
                        (
                            "A donut chart provides "
                            "an alternative view "
                            "of category "
                            "proportions."
                        ),
                        {
                            "category": (
                                column
                            ),
                        },
                        "composition",
                    ),
                ]
            )

    # ========================================================
    # TWO OR MORE NUMERIC VARIABLES
    # ========================================================

    if len(numeric) >= 2:

        x = numeric[0]
        y = numeric[1]

        recommendations.extend(
            [
                _recommendation(
                    "scatter",
                    (
                        0.93
                        - relationship_penalty
                    ),
                    (
                        f"{x} and {y} are numeric. "
                        "A scatter plot is suitable "
                        "for examining their "
                        "relationship."
                    ),
                    {
                        "x": x,
                        "y": y,
                    },
                    "relationship",
                ),
                _recommendation(
                    "regression_line",
                    (
                        0.89
                        - relationship_penalty
                    ),
                    (
                        f"A regression plot can "
                        f"show the linear "
                        f"relationship between "
                        f"{x} and {y}. "
                        f"Recommendation confidence "
                        f"takes sample size into "
                        f"account."
                    ),
                    {
                        "x": x,
                        "y": y,
                    },
                    "relationship",
                ),
            ]
        )

    # ========================================================
    # MULTIPLE NUMERIC VARIABLES
    # ========================================================

    if len(numeric) >= 3:

        recommendations.extend(
            [
                _recommendation(
                    "correlation_heatmap",
                    (
                        0.97
                        - relationship_penalty
                    ),
                    (
                        "The dataset contains "
                        "multiple numeric variables. "
                        "A correlation heatmap is "
                        "useful for identifying "
                        "relationships among them. "
                        "Confidence has been "
                        "adjusted for sample size."
                    ),
                    {
                        "columns": numeric,
                    },
                    "correlation",
                ),
                _recommendation(
                    "scatter_matrix",
                    (
                        0.91
                        - relationship_penalty
                    ),
                    (
                        "A scatter matrix enables "
                        "pairwise comparison of "
                        "multiple numeric variables."
                    ),
                    {
                        "columns": numeric,
                    },
                    "relationship",
                ),
                _recommendation(
                    "parallel_coordinates",
                    0.78,
                    (
                        "Parallel coordinates can "
                        "show multivariate patterns "
                        "across several numeric "
                        "variables."
                    ),
                    {
                        "columns": numeric,
                    },
                    "multivariate",
                ),
            ]
        )

    # ========================================================
    # NUMERIC + CATEGORICAL
    # ========================================================

    if (
        numeric
        and categorical
    ):

        numeric_column = (
            numeric[0]
        )

        category_column = (
            categorical[0]
        )

        recommendations.extend(
            [
                _recommendation(
                    "box",
                    0.90,
                    (
                        f"A grouped box plot can "
                        f"compare {numeric_column} "
                        f"across categories of "
                        f"{category_column}."
                    ),
                    {
                        "x": (
                            category_column
                        ),
                        "y": (
                            numeric_column
                        ),
                    },
                    "comparison",
                ),
                _recommendation(
                    "violin",
                    0.84,
                    (
                        f"A violin plot can compare "
                        f"the distribution of "
                        f"{numeric_column} across "
                        f"{category_column}."
                    ),
                    {
                        "x": (
                            category_column
                        ),
                        "y": (
                            numeric_column
                        ),
                    },
                    "distribution",
                ),
            ]
        )

    # ========================================================
    # DATE / TIME DATA
    # ========================================================

    if (
        dates
        and numeric
    ):

        date_column = dates[0]
        value_column = numeric[0]

        recommendations.extend(
            [
                _recommendation(
                    "line",
                    0.98,
                    (
                        f"{date_column} appears "
                        f"to be temporal and "
                        f"{value_column} is numeric. "
                        "A line chart is suitable "
                        "for showing change over "
                        "time."
                    ),
                    {
                        "x": date_column,
                        "y": value_column,
                    },
                    "time_series",
                ),
                _recommendation(
                    "moving_average",
                    0.91,
                    (
                        "A moving-average chart "
                        "can smooth short-term "
                        "variation and highlight "
                        "longer-term trends."
                    ),
                    {
                        "x": date_column,
                        "y": value_column,
                        "options": {
                            "window": 3,
                        },
                    },
                    "time_series",
                ),
                _recommendation(
                    "area",
                    0.81,
                    (
                        "An area chart provides "
                        "another view of numeric "
                        "change across time."
                    ),
                    {
                        "x": date_column,
                        "y": value_column,
                    },
                    "time_series",
                ),
            ]
        )

        if categorical:

            recommendations.append(
                _recommendation(
                    "stacked_area",
                    0.88,
                    (
                        "The dataset contains a "
                        "date variable, numeric "
                        "measure and categorical "
                        "group, making a stacked "
                        "area chart suitable."
                    ),
                    {
                        "x": date_column,
                        "y": value_column,
                        "group_by": (
                            categorical[0]
                        ),
                    },
                    "time_series",
                )
            )

    # ========================================================
    # STRONG CORRELATIONS
    # ========================================================

    for relationship in (
        strong_correlations[:3]
    ):

        column_1 = relationship[
            "column_1"
        ]

        column_2 = relationship[
            "column_2"
        ]

        correlation_value = (
            relationship[
                "correlation"
            ]
        )

        recommendations.append(
            _recommendation(
                "regression_line",
                (
                    0.96
                    - relationship_penalty
                ),
                (
                    f"{column_1} and "
                    f"{column_2} have a "
                    f"strong correlation "
                    f"({correlation_value:.2f}). "
                    "A regression plot is "
                    "recommended, but confidence "
                    "has been adjusted for the "
                    "available sample size."
                ),
                {
                    "x": column_1,
                    "y": column_2,
                },
                "relationship",
            )
        )

    # =====================================================
    # GOAL-SPECIFIC BOOSTING
    # =====================================================

    goal_categories = {
        "distribution": {
            "distribution",
        },
        "comparison": {
            "comparison",
        },
        "relationship": {
            "relationship",
            "correlation",
        },
        "correlation": {
            "correlation",
            "relationship",
        },
        "trend": {
            "time_series",
        },
        "time_series": {
            "time_series",
        },
        "composition": {
            "composition",
        },
        "quality": {
            "data_quality",
        },
    }

    if goal in goal_categories:

        preferred_categories = (
            goal_categories[
                goal
            ]
        )

        for recommendation in (
            recommendations
        ):

            if (
                recommendation[
                    "category"
                ]
                in preferred_categories
            ):

                recommendation[
                    "score"
                ] = min(
                    recommendation[
                        "score"
                    ] + 0.08,
                    1.0,
                )

                recommendation[
                    "score"
                ] = round(
                    recommendation[
                        "score"
                    ],
                    2,
                )

                recommendation[
                    "confidence_percent"
                ] = int(
                    round(
                        recommendation[
                            "score"
                        ]
                        * 100
                    )
                )

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    unique_recommendations: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    for item in recommendations:

        key = (
            item[
                "chart_type"
            ],
            str(
                item[
                    "suggested_config"
                ]
            ),
        )

        existing = (
            unique_recommendations.get(
                key
            )
        )

        if (
            existing is None
            or item["score"]
            > existing["score"]
        ):
            unique_recommendations[
                key
            ] = item

    # =====================================================
    # GOAL-AWARE RANKING
    # =====================================================

    all_unique = list(
        unique_recommendations.values()
    )

    if (
        goal != "automatic"
        and goal in goal_categories
    ):

        preferred_categories = (
            goal_categories[
                goal
            ]
        )

        # -------------------------------------------------
        # Explicit user goal:
        # matching chart categories are ranked first.
        # Score determines ordering within each group.
        # -------------------------------------------------

        ranked = sorted(
            all_unique,
            key=lambda item: (
                (
                    1
                    if item[
                        "category"
                    ]
                    in preferred_categories
                    else 0
                ),
                item[
                    "score"
                ],
            ),
            reverse=True,
        )

    else:

        # -------------------------------------------------
        # Automatic mode:
        # use overall recommendation score.
        # -------------------------------------------------

        ranked = sorted(
            all_unique,
            key=lambda item: (
                item[
                    "score"
                ]
            ),
            reverse=True,
        )

    # =====================================================
    # SAFE RESULT LIMIT
    # =====================================================

    safe_limit = min(
        max(
            int(limit),
            1,
        ),
        25,
    )

    # =====================================================
    # RETURN RESULT
    # =====================================================

    return {
        "goal": goal,
        "dataset_profile": profile,
        "recommendation_count": min(
            len(ranked),
            safe_limit,
        ),
        "recommendations": (
            ranked[
                :safe_limit
            ]
        ),
    }
