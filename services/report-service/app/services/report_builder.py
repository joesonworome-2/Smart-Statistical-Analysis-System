from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
from typing import Any

import json
import httpx
import pandas as pd
from bson import ObjectId

from app.config import settings
from app.database import (
    analyses_collection,
    statistical_results_collection,
    visualizations_collection,
)


# ============================================================
# JSON safety
# ============================================================

def make_json_safe(
    value: Any,
) -> Any:
    if isinstance(
        value,
        ObjectId,
    ):
        return str(value)

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            make_json_safe(item)
            for item in value
        ]

    return value


# ============================================================
# Query helpers
# ============================================================

def _possible_id_values(
    value: str,
) -> list[Any]:
    values: list[Any] = [value]

    if ObjectId.is_valid(value):
        values.append(
            ObjectId(value)
        )

    return values


def _owned_dataset_query(
    dataset_id: str,
    user_id: str,
) -> dict[str, Any]:
    return {
        "dataset_id": {
            "$in": _possible_id_values(
                dataset_id
            )
        },
        "user_id": {
            "$in": _possible_id_values(
                user_id
            )
        },
    }



# ============================================================
# Remove duplicate saved analyses
# ============================================================

_VOLATILE_ANALYSIS_KEYS = {
    "_id",
    "id",
    "user_id",
    "dataset_id",
    "created_at",
    "updated_at",
    "saved_at",
}


def _stable_analysis_value(
    value: Any,
) -> Any:
    """
    Return a stable JSON-compatible value for building a
    duplicate-analysis signature.

    Volatile database/timestamp fields are excluded so repeated
    saves of the same analysis configuration compare as equal.
    """
    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _stable_analysis_value(
                item
            )
            for key, item
            in sorted(
                value.items(),
                key=lambda pair: str(
                    pair[0]
                ),
            )
            if str(key)
            not in _VOLATILE_ANALYSIS_KEYS
        }

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            _stable_analysis_value(
                item
            )
            for item in value
        ]

    return make_json_safe(
        value
    )


def _analysis_signature(
    analysis: dict[str, Any],
) -> str:
    """
    Identify one logical analysis.

    The signature intentionally focuses on the analysis method,
    title and user-selected configuration. Therefore, if the
    same analysis is saved multiple times for the same dataset,
    only the newest saved copy is used in the final report.

    Different methods or different variable/configuration
    choices remain separate analyses.
    """
    method = str(
        analysis.get(
            "method"
        )
        or analysis.get(
            "analysis_type"
        )
        or analysis.get(
            "type"
        )
        or analysis.get(
            "test_type"
        )
        or ""
    ).strip().lower()

    title = str(
        analysis.get(
            "title"
        )
        or analysis.get(
            "test_name"
        )
        or ""
    ).strip().lower()

    configuration = (
        analysis.get(
            "configuration"
        )
        or {}
    )

    metadata = (
        analysis.get(
            "metadata"
        )
        or {}
    )

    if isinstance(
        metadata,
        dict,
    ):
        metadata = {
            key: value
            for key, value
            in metadata.items()
            if key not in {
                "raw_result",
                "source",
                "endpoint",
                "query",
            }
        }

    payload = {
        "method": method,
        "title": title,
        "configuration": (
            _stable_analysis_value(
                configuration
            )
        ),
        "metadata": (
            _stable_analysis_value(
                metadata
            )
        ),
    }

    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
        separators=(
            ",",
            ":",
        ),
    )


def deduplicate_analysis_results(
    analyses: list[
        dict[str, Any]
    ],
) -> list[
    dict[str, Any]
]:
    """
    Keep only the newest copy of each logical analysis.

    This affects report generation only. It does not delete old
    analysis history from MongoDB.
    """
    if not analyses:
        return []

    def sort_key(
        item: dict[str, Any],
    ) -> str:
        return str(
            item.get(
                "created_at",
                "",
            )
            or item.get(
                "updated_at",
                "",
            )
            or ""
        )

    newest_first = sorted(
        analyses,
        key=sort_key,
        reverse=True,
    )

    kept = []
    seen = set()

    for analysis in newest_first:
        signature = (
            _analysis_signature(
                analysis
            )
        )

        if signature in seen:
            continue

        seen.add(
            signature
        )

        kept.append(
            analysis
        )

    kept.sort(
        key=sort_key
    )

    return kept


# ============================================================
# Load statistical results
# ============================================================

def get_saved_statistical_results(
    dataset_id: str,
    user_id: str,
) -> list[dict[str, Any]]:
    documents = list(
        statistical_results_collection.find(
            _owned_dataset_query(
                dataset_id,
                user_id,
            )
        ).sort(
            "created_at",
            1,
        )
    )

    return make_json_safe(
        documents
    )


def get_legacy_analysis_results(
    dataset_id: str,
    user_id: str,
) -> list[dict[str, Any]]:
    documents = list(
        analyses_collection.find(
            _owned_dataset_query(
                dataset_id,
                user_id,
            )
        ).sort(
            "created_at",
            1,
        )
    )

    normalized = []

    for document in documents:
        analysis_type = (
            document.get(
                "analysis_type"
            )
            or document.get("type")
            or document.get("test_type")
            or "statistical_analysis"
        )

        normalized.append(
            {
                "id": str(
                    document.get(
                        "_id",
                        "",
                    )
                ),
                "dataset_id": dataset_id,
                "user_id": user_id,
                "method": analysis_type,
                "title": _humanize(
                    analysis_type
                ),
                "configuration": make_json_safe(
                    document.get(
                        "configuration",
                        {},
                    )
                ),
                "tables": make_json_safe(
                    document.get(
                        "tables",
                        [],
                    )
                ),
                "assumptions": make_json_safe(
                    document.get(
                        "assumptions"
                    )
                ),
                "interpretation": document.get(
                    "interpretation"
                ),
                "apa": document.get("apa"),
                "metadata": {
                    "raw_result": make_json_safe(
                        document.get(
                            "results",
                            document,
                        )
                    ),
                    "source": "analysis_service",
                },
                "created_at": make_json_safe(
                    document.get(
                        "created_at"
                    )
                ),
            }
        )

    return normalized


def get_all_analysis_results(
    dataset_id: str,
    user_id: str,
) -> list[dict[str, Any]]:
    saved = get_saved_statistical_results(
        dataset_id,
        user_id,
    )

    legacy = get_legacy_analysis_results(
        dataset_id,
        user_id,
    )

    combined = [
        *saved,
        *legacy,
    ]

    def sort_key(item):
        return str(
            item.get(
                "created_at",
                "",
            )
        )

    combined.sort(
        key=sort_key
    )

    return (
        deduplicate_analysis_results(
            combined
        )
    )


# ============================================================
# Load saved visualizations
# ============================================================

def get_visualization_results(
    dataset_id: str,
    user_id: str,
) -> list[dict[str, Any]]:
    documents = list(
        visualizations_collection.find(
            _owned_dataset_query(
                dataset_id,
                user_id,
            )
        ).sort(
            "created_at",
            1,
        )
    )

    return make_json_safe(
        documents
    )


# ============================================================
# Load the actual dataset used by the user
# ============================================================

def get_dataset_data(
    dataset_id: str,
    authorization: str | None,
) -> dict[str, Any]:
    if not authorization:
        return {
            "columns": [],
            "rows": [],
        }

    all_rows: list[dict[str, Any]] = []
    columns: list[str] = []
    offset = 0
    limit = 5000
    has_more = True

    try:
        with httpx.Client(
            timeout=60.0
        ) as client:
            while has_more:
                response = client.get(
                    (
                        f"{settings.dataset_service_url}"
                        f"/datasets/{dataset_id}/data"
                    ),
                    params={
                        "offset": offset,
                        "limit": limit,
                    },
                    headers={
                        "Authorization": authorization
                    },
                )

                if response.status_code != 200:
                    break

                payload = response.json()

                if not columns:
                    columns = payload.get(
                        "columns",
                        [],
                    )

                rows = payload.get(
                    "rows",
                    [],
                )

                all_rows.extend(rows)

                returned = payload.get(
                    "returned_rows",
                    len(rows),
                )

                has_more = bool(
                    payload.get(
                        "has_more",
                        False,
                    )
                )

                if not returned:
                    break

                offset += int(returned)

    except Exception:
        # A report can still be generated without chart
        # reconstruction if the dataset service is temporarily
        # unavailable.
        return {
            "columns": columns,
            "rows": all_rows,
        }

    return {
        "columns": columns,
        "rows": make_json_safe(
            all_rows
        ),
    }


# ============================================================
# Formatting / interpretation helpers
# ============================================================

def _humanize(
    value: Any,
) -> str:
    return (
        str(value or "")
        .replace("_", " ")
        .replace("-", " ")
        .strip()
        .title()
    )


def _first_value(
    source: Any,
    keys: tuple[str, ...],
) -> Any:
    if isinstance(source, dict):
        for key in keys:
            if key in source:
                return source[key]

        for value in source.values():
            found = _first_value(
                value,
                keys,
            )
            if found is not None:
                return found

    elif isinstance(source, list):
        for value in source:
            found = _first_value(
                value,
                keys,
            )
            if found is not None:
                return found

    return None


def _safe_number(
    value: Any,
) -> float | None:
    try:
        number = float(value)
        if pd.notna(number):
            return number
    except (TypeError, ValueError):
        pass

    return None


def _format_number(
    value: Any,
) -> str:
    number = _safe_number(value)

    if number is None:
        return str(value)

    if float(number).is_integer():
        return f"{int(number):,}"

    return (
        f"{number:,.3f}"
        .rstrip("0")
        .rstrip(".")
    )


def _analysis_raw_result(
    analysis: dict[str, Any],
) -> Any:
    metadata = analysis.get(
        "metadata",
        {},
    )

    if isinstance(metadata, dict):
        raw = metadata.get(
            "raw_result"
        )
        if raw is not None:
            return raw

    return analysis.get(
        "results",
        analysis,
    )


def _descriptive_table_summary(
    analysis: dict[str, Any],
) -> str | None:
    tables = analysis.get(
        "tables",
        [],
    )

    for table in tables:
        if not isinstance(table, dict):
            continue

        columns = table.get(
            "columns",
            [],
        )
        rows = table.get(
            "rows",
            [],
        )

        if (
            not columns
            or not rows
            or str(columns[0]).lower()
            != "statistic"
        ):
            continue

        mean_row = next(
            (
                row
                for row in rows
                if str(
                    row.get(
                        columns[0],
                        "",
                    )
                ).lower()
                == "mean"
            ),
            None,
        )

        median_row = next(
            (
                row
                for row in rows
                if str(
                    row.get(
                        columns[0],
                        "",
                    )
                ).lower()
                == "median"
            ),
            None,
        )

        if not mean_row:
            return None

        summaries = []

        for variable in columns[1:4]:
            mean_value = mean_row.get(
                variable
            )

            if mean_value is None:
                continue

            text = (
                f"{variable} had a mean of "
                f"{_format_number(mean_value)}"
            )

            if median_row:
                median_value = median_row.get(
                    variable
                )
                if median_value is not None:
                    text += (
                        " and a median of "
                        f"{_format_number(median_value)}"
                    )

            summaries.append(text)

        if summaries:
            return (
                "; ".join(summaries)
                + "."
            )

    return None


def build_analysis_interpretation(
    analysis: dict[str, Any],
) -> str:
    existing = analysis.get(
        "interpretation"
    )

    if isinstance(existing, str) and existing.strip():
        return existing.strip()

    descriptive = _descriptive_table_summary(
        analysis
    )

    if descriptive:
        return descriptive

    raw = _analysis_raw_result(
        analysis
    )

    test_name = (
        _first_value(
            raw,
            (
                "test",
                "test_name",
                "analysis_type",
            ),
        )
        or analysis.get("title")
        or _humanize(
            analysis.get("method")
        )
    )

    p_value = _safe_number(
        _first_value(
            raw,
            (
                "p_value",
                "p-value",
                "pvalue",
            ),
        )
    )

    alpha = _safe_number(
        _first_value(
            raw,
            (
                "alpha",
                "significance_level",
            ),
        )
    )

    if alpha is None:
        alpha = 0.05

    if p_value is not None:
        significance = (
            "statistically significant"
            if p_value < alpha
            else "not statistically significant"
        )

        return (
            f"{test_name} produced a p-value of "
            f"{_format_number(p_value)}. At an alpha level "
            f"of {_format_number(alpha)}, the result is "
            f"{significance}."
        )

    correlation = _safe_number(
        _first_value(
            raw,
            (
                "correlation",
                "pearson_r",
                "r",
            ),
        )
    )

    if correlation is not None:
        absolute = abs(correlation)

        if absolute >= 0.7:
            strength = "strong"
        elif absolute >= 0.4:
            strength = "moderate"
        else:
            strength = "weak"

        direction = (
            "positive"
            if correlation > 0
            else "negative"
            if correlation < 0
            else "neutral"
        )

        return (
            f"The analysis produced a {strength} {direction} "
            f"relationship (r = {_format_number(correlation)})."
        )

    return (
        f"{test_name} was performed on the selected dataset. "
        "The complete numerical output is shown in the result "
        "table above."
    )


# ============================================================
# Visualization interpretation
# ============================================================

def _visualization_config(
    visualization: dict[str, Any],
) -> dict[str, Any]:
    request = visualization.get(
        "request",
        {},
    )

    if isinstance(request, dict) and request:
        return request

    recommendation = visualization.get(
        "recommendation",
        {},
    )

    if isinstance(recommendation, dict):
        config = recommendation.get(
            "suggested_config",
            {},
        )
        if isinstance(config, dict):
            return config

    return {}


def build_visualization_interpretation(
    visualization: dict[str, Any],
    dataset_data: dict[str, Any],
) -> dict[str, Any]:
    chart_type = (
        visualization.get(
            "visualization_type"
        )
        or visualization.get(
            "chart_type"
        )
        or "visualization"
    )

    title = _humanize(
        chart_type
    )

    config = _visualization_config(
        visualization
    )

    rows = dataset_data.get(
        "rows",
        [],
    )

    columns = dataset_data.get(
        "columns",
        [],
    )

    if not rows:
        return {
            "title": title,
            "summary": (
                f"The {title.lower()} was generated by SSAS "
                "for this dataset. The chart configuration is "
                "included in the report, but the dataset could "
                "not be reloaded for numerical interpretation."
            ),
            "key_findings": [],
        }

    dataframe = pd.DataFrame(
        rows,
        columns=(
            columns or None
        ),
    )

    x = config.get("x")
    y = config.get("y")
    category = (
        config.get("category")
        or config.get("group_by")
        or x
    )

    findings: list[str] = []
    summary = (
        f"The {title.lower()} summarizes the selected "
        "variables in the dataset."
    )

    distribution_types = {
        "histogram",
        "density",
        "ecdf",
        "frequency_polygon",
        "box",
        "violin",
    }

    relationship_types = {
        "scatter",
        "bubble",
        "regression_line",
        "actual_vs_predicted",
        "residual_vs_fitted",
    }

    time_types = {
        "line",
        "area",
        "moving_average",
        "step",
        "stacked_area",
    }

    categorical_types = {
        "bar",
        "horizontal_bar",
        "pie",
        "donut",
        "treemap",
        "sunburst",
    }

    if chart_type in distribution_types:
        variable = y or x

        if variable in dataframe.columns:
            values = pd.to_numeric(
                dataframe[variable],
                errors="coerce",
            ).dropna()

            if not values.empty:
                mean = values.mean()
                median = values.median()
                minimum = values.min()
                maximum = values.max()

                summary = (
                    f"The {title.lower()} shows the distribution "
                    f"of {variable}. The mean is "
                    f"{_format_number(mean)}, the median is "
                    f"{_format_number(median)}, and observed "
                    f"values range from {_format_number(minimum)} "
                    f"to {_format_number(maximum)}."
                )

                findings.extend(
                    [
                        f"Usable observations: {len(values):,}.",
                        (
                            f"Observed range: {_format_number(minimum)} "
                            f"to {_format_number(maximum)}."
                        ),
                    ]
                )

    elif chart_type in relationship_types:
        if (
            x in dataframe.columns
            and y in dataframe.columns
        ):
            working = dataframe[
                [x, y]
            ].apply(
                pd.to_numeric,
                errors="coerce",
            ).dropna()

            if len(working) >= 2:
                correlation = working[x].corr(
                    working[y]
                )

                if pd.notna(correlation):
                    absolute = abs(correlation)
                    if absolute >= 0.7:
                        strength = "strong"
                    elif absolute >= 0.4:
                        strength = "moderate"
                    else:
                        strength = "weak"

                    direction = (
                        "positive"
                        if correlation > 0
                        else "negative"
                        if correlation < 0
                        else "neutral"
                    )

                    summary = (
                        f"The {title.lower()} examines the "
                        f"relationship between {x} and {y}. "
                        f"The observed linear association is "
                        f"{strength} and {direction} "
                        f"(r = {_format_number(correlation)})."
                    )

                    findings.append(
                        (
                            f"Pearson correlation: "
                            f"{_format_number(correlation)}."
                        )
                    )

    elif chart_type == "correlation_heatmap":
        numeric = dataframe.select_dtypes(
            include="number"
        )

        if numeric.shape[1] >= 2:
            matrix = numeric.corr()
            best_pair = None
            best_value = None

            for index, column_a in enumerate(
                matrix.columns
            ):
                for column_b in matrix.columns[
                    index + 1:
                ]:
                    value = matrix.loc[
                        column_a,
                        column_b,
                    ]

                    if pd.isna(value):
                        continue

                    if (
                        best_value is None
                        or abs(value) > abs(best_value)
                    ):
                        best_value = float(value)
                        best_pair = (
                            column_a,
                            column_b,
                        )

            if best_pair:
                summary = (
                    "The correlation heatmap compares linear "
                    "relationships among numeric variables. "
                    f"The strongest observed pair is "
                    f"{best_pair[0]} and {best_pair[1]} "
                    f"(r = {_format_number(best_value)})."
                )

                findings.append(
                    summary
                )

    elif chart_type in time_types:
        if y in dataframe.columns:
            values = pd.to_numeric(
                dataframe[y],
                errors="coerce",
            ).dropna()

            if len(values) >= 2:
                first = values.iloc[0]
                last = values.iloc[-1]
                change = last - first
                direction = (
                    "increased"
                    if change > 0
                    else "decreased"
                    if change < 0
                    else "remained unchanged"
                )

                summary = (
                    f"The {title.lower()} shows how {y} changes "
                    f"across the plotted sequence. The value "
                    f"{direction} from {_format_number(first)} "
                    f"to {_format_number(last)}."
                )

                findings.append(
                    (
                        f"Overall change: "
                        f"{_format_number(change)}."
                    )
                )

    elif chart_type in categorical_types:
        if category in dataframe.columns:
            counts = dataframe[
                category
            ].dropna().astype(str).value_counts()

            if not counts.empty:
                top_category = counts.index[0]
                top_count = int(counts.iloc[0])
                total = int(counts.sum())
                percentage = (
                    top_count / total * 100
                    if total
                    else 0
                )

                summary = (
                    f"The {title.lower()} compares categories of "
                    f"{category}. The most frequent category is "
                    f"'{top_category}' with {top_count:,} "
                    f"observations ({percentage:.1f}%)."
                )

                findings.append(
                    (
                        f"Most frequent category: {top_category} "
                        f"({top_count:,} observations)."
                    )
                )

    elif chart_type in {
        "missing_values_bar",
        "missing_values_heatmap",
    }:
        missing = dataframe.isna().sum()
        affected = missing[
            missing > 0
        ]
        total_missing = int(
            missing.sum()
        )

        summary = (
            f"The visualization shows missing-data patterns. "
            f"There are {total_missing:,} missing values across "
            f"{len(affected):,} affected columns."
        )

        findings.append(
            summary
        )

    reason = None
    recommendation = visualization.get(
        "recommendation",
        {},
    )

    if isinstance(recommendation, dict):
        reason = recommendation.get(
            "reason"
        )

    if reason:
        findings.append(
            str(reason)
        )

    return {
        "title": title,
        "summary": summary,
        "key_findings": findings,
    }


# ============================================================
# Conclusion
# ============================================================

def build_conclusion(
    dataset_summary: dict[str, Any],
    analyses: list[dict[str, Any]],
    visualizations: list[dict[str, Any]],
) -> str:
    file_name = dataset_summary.get(
        "file_name",
        "the dataset",
    )

    row_count = dataset_summary.get(
        "row_count",
        0,
    )

    column_count = dataset_summary.get(
        "column_count",
        0,
    )

    sentences = [
        (
            f"This report summarizes the complete SSAS workflow "
            f"performed on {file_name}, containing {row_count:,} "
            f"rows and {column_count:,} columns."
        )
    ]

    if analyses:
        titles = []
        for analysis in analyses:
            title = (
                analysis.get("title")
                or _humanize(
                    analysis.get("method")
                )
            )
            if title and title not in titles:
                titles.append(title)

        if titles:
            sentences.append(
                (
                    "The statistical procedures carried out were: "
                    + ", ".join(titles)
                    + "."
                )
            )

        interpretation_sentences = []

        for analysis in analyses[:5]:
            text = build_analysis_interpretation(
                analysis
            )
            if text:
                interpretation_sentences.append(
                    text
                )

        if interpretation_sentences:
            sentences.append(
                " ".join(
                    interpretation_sentences
                )
            )
    else:
        sentences.append(
            "No stored statistical test results were available "
            "for inclusion in this report."
        )

    if visualizations:
        chart_names = []

        for visualization in visualizations:
            name = _humanize(
                visualization.get(
                    "visualization_type",
                    visualization.get(
                        "chart_type",
                        "visualization",
                    ),
                )
            )
            if name not in chart_names:
                chart_names.append(name)

        sentences.append(
            (
                f"SSAS generated {len(visualizations)} "
                f"visualization(s), including "
                + ", ".join(chart_names)
                + ". These visualizations provide graphical "
                "support for the statistical findings described "
                "in the preceding sections."
            )
        )

        interpretation_summaries = []

        for visualization in visualizations[:4]:
            interpretation = visualization.get(
                "report_interpretation",
                {},
            )
            summary = interpretation.get(
                "summary"
            ) if isinstance(
                interpretation,
                dict,
            ) else None

            if summary:
                interpretation_summaries.append(
                    summary
                )

        if interpretation_summaries:
            sentences.append(
                " ".join(
                    interpretation_summaries
                )
            )

    sentences.append(
        (
            "Overall, the conclusions above should be interpreted "
            "together with the reported sample size, assumptions, "
            "p-values, effect estimates, descriptive measures, and "
            "visual evidence. The report reflects the analyses and "
            "visualizations stored by SSAS for this dataset at the "
            "time the report was generated."
        )
    )

    return " ".join(
        sentences
    )


# ============================================================
# Build complete report data
# ============================================================

def build_report_data(
    dataset: dict[str, Any],
    dataset_id: str,
    user_id: str,
    authorization: str | None,
) -> dict[str, Any]:
    generated_at = datetime.now(
        timezone.utc
    )

    dataset_data = get_dataset_data(
        dataset_id,
        authorization,
    )

    analyses = get_all_analysis_results(
        dataset_id,
        user_id,
    )

    visualizations = get_visualization_results(
        dataset_id,
        user_id,
    )

    # Add an interpretation specifically for every saved
    # visualization instead of only interpreting a generic
    # recommended chart.
    enriched_visualizations = []

    for visualization in visualizations:
        item = dict(visualization)
        item[
            "report_interpretation"
        ] = build_visualization_interpretation(
            visualization,
            dataset_data,
        )
        enriched_visualizations.append(
            item
        )

    file_name = (
        dataset.get(
            "original_filename"
        )
        or dataset.get("file_name")
        or dataset.get("filename")
        or "Dataset"
    )

    row_count = dataset.get(
        "row_count"
    )

    column_count = dataset.get(
        "column_count"
    )

    if row_count is None:
        row_count = len(
            dataset_data.get(
                "rows",
                [],
            )
        )

    if column_count is None:
        column_count = len(
            dataset_data.get(
                "columns",
                [],
            )
        )

    dataset_summary = {
        "file_name": file_name,
        "row_count": int(
            row_count or 0
        ),
        "column_count": int(
            column_count or 0
        ),
        "date_generated": generated_at.isoformat(),
    }

    conclusion = build_conclusion(
        dataset_summary,
        analyses,
        enriched_visualizations,
    )

    return {
        "title": (
            "SSAS Statistical Analysis Report"
        ),
        "generated_at": generated_at.isoformat(),
        "dataset_id": dataset_id,
        "user_id": user_id,
        "dataset": make_json_safe(
            dataset
        ),
        "dataset_summary": dataset_summary,
        "dataset_data": dataset_data,
        "summary": {
            "analysis_count": len(
                analyses
            ),
            "visualization_count": len(
                enriched_visualizations
            ),
            "smart_interpretation_available": bool(
                enriched_visualizations
            ),
        },
        "analyses": analyses,
        "visualizations": enriched_visualizations,
        # Kept for compatibility with the existing report route
        # and Excel generator.
        "smart_interpretation": {
            "available": bool(
                enriched_visualizations
            ),
            "interpretations": [
                item.get(
                    "report_interpretation"
                )
                for item in enriched_visualizations
            ],
        },
        "conclusion": conclusion,
    }
