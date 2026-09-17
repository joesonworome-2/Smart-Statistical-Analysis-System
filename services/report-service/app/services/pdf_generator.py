from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as ReportLabImage,
    KeepTogether,
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.chart_renderer import (
    render_visualization_png,
)


# ============================================================
# Formatting helpers
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


def _format_number(
    value: Any,
) -> str:
    if value is None:
        return "—"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        if value != value:
            return "—"

        if value != 0 and abs(value) < 0.001:
            return f"{value:.4e}"

        return (
            f"{value:,.3f}"
            .rstrip("0")
            .rstrip(".")
        )

    return str(value)


def _display_value(
    value: Any,
    limit: int = 600,
) -> str:
    if value is None:
        return "—"

    if isinstance(
        value,
        (int, float, bool),
    ):
        return _format_number(value)

    if isinstance(
        value,
        (dict, list, tuple),
    ):
        text = json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        )
    else:
        text = str(value)

    if len(text) > limit:
        return text[:limit] + "..."

    return text


def _paragraph(
    text: Any,
    style,
) -> Paragraph:
    return Paragraph(
        escape(
            _display_value(text)
        ).replace("\n", "<br/>") ,
        style,
    )


def _format_datetime(
    value: Any,
) -> str:
    text = str(value or "")

    if not text:
        return "—"

    try:
        from datetime import datetime

        parsed = datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        )

        return parsed.strftime(
            "%d %B %Y, %H:%M UTC"
        )
    except Exception:
        return text


def _flatten_result(
    value: Any,
    prefix: str = "",
    output: list[tuple[str, Any]] | None = None,
) -> list[tuple[str, Any]]:
    if output is None:
        output = []

    if isinstance(value, dict):
        for key, item in value.items():
            if key in {
                "dataset_id",
                "user_id",
                "_id",
                "id",
            }:
                continue

            label = (
                f"{prefix} · {_humanize(key)}"
                if prefix
                else _humanize(key)
            )

            if isinstance(
                item,
                (dict, list),
            ):
                _flatten_result(
                    item,
                    label,
                    output,
                )
            else:
                output.append(
                    (label, item)
                )

    elif isinstance(value, list):
        if (
            value
            and all(
                not isinstance(
                    item,
                    (dict, list),
                )
                for item in value
            )
        ):
            output.append(
                (
                    prefix or "Values",
                    ", ".join(
                        _display_value(item)
                        for item in value
                    ),
                )
            )
        else:
            for index, item in enumerate(value, 1):
                _flatten_result(
                    item,
                    (
                        f"{prefix} [{index}]"
                        if prefix
                        else f"Item {index}"
                    ),
                    output,
                )

    else:
        output.append(
            (
                prefix or "Result",
                value,
            )
        )

    return output


# ============================================================
# Common table style
# ============================================================

def _apply_table_style(
    table: Table,
    header_background=colors.HexColor(
        "#E6F4F3"
    ),
) -> None:
    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    header_background,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#083F43"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor(
                        "#AAB8BA"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )


# ============================================================
# Statistical-analysis table helpers
# ============================================================

def _normalized_key(
    value: Any,
) -> str:
    text = str(
        value or ""
    ).lower()

    text = (
        text
        .replace("²", "2")
        .replace("β", "beta")
        .replace("α", "alpha")
    )

    return "".join(
        character
        for character in text
        if character.isalnum()
    )


def _row_value(
    row: Any,
    column: Any,
    column_index: int,
) -> Any:
    if isinstance(row, dict):
        if column in row:
            return row.get(column)

        normalized = {
            _normalized_key(key): value
            for key, value in row.items()
        }

        wanted = _normalized_key(
            column
        )

        if wanted in normalized:
            return normalized[wanted]

        aliases = {
            "r2": [
                "rsquared",
                "r2",
            ],
            "adjustedr2": [
                "adjustedrsquared",
                "adjr2",
            ],
            "pvalue": [
                "p",
                "pvalue",
            ],
            "stderror": [
                "standarderror",
                "stderr",
                "stderror",
            ],
            "standardizedbeta": [
                "beta",
                "standardizedbeta",
            ],
            "cilower": [
                "lowerci",
                "cilower",
                "lower",
            ],
            "ciupper": [
                "upperci",
                "ciupper",
                "upper",
            ],
        }

        for candidate in aliases.get(
            wanted,
            [],
        ):
            if candidate in normalized:
                return normalized[candidate]

        return "—"

    if isinstance(
        row,
        (list, tuple),
    ):
        if column_index < len(row):
            return row[column_index]

    return "—"


def _analysis_column_widths(
    columns: list[Any],
    title: str = "",
) -> list[float]:
    available = 160 * mm
    count = len(columns)
    lowered = str(
        title or ""
    ).lower()

    if count <= 1:
        return [available]

    if count == 2:
        return [
            55 * mm,
            105 * mm,
        ]

    if (
        "regression coefficient" in lowered
        and count >= 8
    ):
        weights = [
            1.65,
            0.85,
            1.05,
            1.45,
            0.75,
            0.85,
            0.95,
            0.95,
            0.95,
        ]
        weights = weights[:count]
        if len(weights) < count:
            weights.extend(
                [1.0] * (
                    count - len(weights)
                )
            )

    elif "diagnostic" in lowered and count == 4:
        weights = [
            1.55,
            1.0,
            1.0,
            2.45,
        ]

    elif "anova" in lowered and count >= 5:
        weights = [
            1.5,
            1.25,
            0.7,
            1.1,
            0.85,
            0.9,
        ][:count]

    elif "multicollinearity" in lowered and count == 4:
        weights = [
            1.6,
            0.9,
            1.0,
            2.0,
        ]

    else:
        weights = []
        for index, column in enumerate(columns):
            header_length = max(
                6,
                min(
                    24,
                    len(str(column)),
                ),
            )

            weight = 1.0 + (
                header_length / 26.0
            )

            if index == 0:
                weight *= 1.25

            weights.append(weight)

    total = sum(weights) or 1.0

    return [
        available * (
            weight / total
        )
        for weight in weights
    ]


def _apply_analysis_table_style(
    table: Table,
) -> None:
    border = colors.HexColor(
        "#CDD5D7"
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#E7F3F3"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#073F43"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.45,
                    border,
                ),
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    border,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )


def _result_table_flowable(
    table_data: dict[str, Any],
    small_style,
) -> Table | None:
    rows = table_data.get(
        "rows",
        [],
    )

    columns = table_data.get(
        "columns",
        [],
    )

    if (
        not columns
        and rows
        and isinstance(
            rows[0],
            dict,
        )
    ):
        columns = list(
            rows[0].keys()
        )

    if not columns or not rows:
        return None

    title = str(
        table_data.get(
            "title",
            "",
        )
    )

    cell_style = small_style

    if len(columns) >= 8:
        cell_style = ParagraphStyle(
            "SSASAnalysisTiny",
            parent=small_style,
            fontSize=6.4,
            leading=7.7,
            spaceAfter=0,
        )

    elif len(columns) >= 6:
        cell_style = ParagraphStyle(
            "SSASAnalysisCompact",
            parent=small_style,
            fontSize=6.9,
            leading=8.2,
            spaceAfter=0,
        )

    rendered = [
        [
            _paragraph(
                column,
                cell_style,
            )
            for column in columns
        ]
    ]

    for row in rows:
        rendered.append(
            [
                _paragraph(
                    _row_value(
                        row,
                        column,
                        column_index,
                    ),
                    cell_style,
                )
                for column_index, column
                in enumerate(columns)
            ]
        )

    table = Table(
        rendered,
        colWidths=(
            _analysis_column_widths(
                list(columns),
                title,
            )
        ),
        repeatRows=1,
        hAlign="LEFT",
    )

    _apply_analysis_table_style(
        table
    )

    return table


def _raw_analysis_result(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    metadata = analysis.get(
        "metadata",
        {},
    )

    if isinstance(
        metadata,
        dict,
    ):
        raw = metadata.get(
            "raw_result"
        )

        if isinstance(
            raw,
            dict,
        ):
            return raw

    raw = analysis.get(
        "results"
    )

    if isinstance(
        raw,
        dict,
    ):
        return raw

    return {}


def _table_signature(
    table_data: dict[str, Any],
) -> str:
    try:
        return json.dumps(
            {
                "title": table_data.get(
                    "title"
                ),
                "columns": table_data.get(
                    "columns"
                ),
                "rows": table_data.get(
                    "rows"
                ),
            },
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
    except Exception:
        return str(
            id(table_data)
        )


def _collect_structured_tables(
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    collected: list[
        dict[str, Any]
    ] = []
    seen: set[str] = set()

    def add_table(
        item: Any,
        title_hint: str = "",
    ) -> bool:
        if not isinstance(
            item,
            dict,
        ):
            return False

        rows = item.get(
            "rows"
        )
        columns = item.get(
            "columns"
        )

        if not isinstance(
            rows,
            list,
        ):
            return False

        if not rows:
            return False

        if (
            not isinstance(
                columns,
                list,
            )
            or not columns
        ):
            if isinstance(
                rows[0],
                dict,
            ):
                columns = list(
                    rows[0].keys()
                )
            else:
                return False

        normalized = {
            **item,
            "title": (
                item.get("title")
                or _humanize(
                    title_hint
                )
                or "Results"
            ),
            "columns": columns,
            "rows": rows,
        }

        signature = _table_signature(
            normalized
        )

        if signature in seen:
            return True

        seen.add(signature)
        collected.append(
            normalized
        )
        return True

    top_tables = analysis.get(
        "tables",
        [],
    )

    if isinstance(
        top_tables,
        list,
    ):
        for item in top_tables:
            add_table(
                item,
                "Results",
            )

    raw = _raw_analysis_result(
        analysis
    )

    def walk(
        value: Any,
        path: str = "",
    ) -> None:
        if isinstance(
            value,
            dict,
        ):
            if add_table(
                value,
                path,
            ):
                return

            for key, item in value.items():
                if key in {
                    "dataset_data",
                    "raw_data",
                    "observations",
                }:
                    continue

                next_path = (
                    str(key)
                    if not path
                    else f"{path} {key}"
                )

                walk(
                    item,
                    next_path,
                )

        elif isinstance(
            value,
            list,
        ):
            for index, item in enumerate(
                value,
                1,
            ):
                walk(
                    item,
                    (
                        f"{path} {index}"
                        if path
                        else str(index)
                    ),
                )

    walk(raw)

    assumptions = analysis.get(
        "assumptions"
    )

    if isinstance(
        assumptions,
        dict,
    ):
        add_table(
            assumptions,
            "Assumptions / Checks",
        )

    return collected


def _configuration_rows(
    analysis: dict[str, Any],
) -> list[tuple[str, Any]]:
    raw = _raw_analysis_result(
        analysis
    )

    rows: list[
        tuple[str, Any]
    ] = []
    seen: set[str] = set()

    def append(
        label: str,
        value: Any,
    ) -> None:
        if value is None:
            return

        if isinstance(
            value,
            str,
        ) and not value.strip():
            return

        normalized = _normalized_key(
            label
        )

        if normalized in seen:
            return

        seen.add(normalized)
        rows.append(
            (label, value)
        )

    for key, label in (
        ("dataset_rows", "Dataset Rows"),
        ("row_count", "Dataset Rows"),
        ("dataset_columns", "Dataset Columns"),
        ("column_count", "Dataset Columns"),
        ("test_name", "Test Name"),
        ("test", "Test Name"),
        ("analysis_name", "Analysis"),
    ):
        if key in raw:
            append(
                label,
                raw.get(key),
            )

    raw_config = raw.get(
        "configuration",
        {},
    )

    if not isinstance(
        raw_config,
        dict,
    ):
        raw_config = {}

    saved_config = analysis.get(
        "configuration",
        {},
    )

    if not isinstance(
        saved_config,
        dict,
    ):
        saved_config = {}

    configuration = (
        raw_config
        if raw_config
        else saved_config
    )

    for key, value in configuration.items():
        if key in {
            "endpoint",
            "query",
            "http_method",
        }:
            continue

        append(
            _humanize(key),
            value,
        )

    if not rows:
        title = (
            analysis.get("title")
            or analysis.get("method")
        )

        if title:
            append(
                "Analysis",
                title,
            )

    return rows


def _key_value_table(
    rows: list[tuple[str, Any]],
    small_style,
    first_heading: str = "Setting / Statistic",
    second_heading: str = "Value",
) -> Table | None:
    if not rows:
        return None

    rendered = [
        [
            _paragraph(
                first_heading,
                small_style,
            ),
            _paragraph(
                second_heading,
                small_style,
            ),
        ]
    ]

    for label, value in rows:
        rendered.append(
            [
                _paragraph(
                    label,
                    small_style,
                ),
                _paragraph(
                    value,
                    small_style,
                ),
            ]
        )

    table = Table(
        rendered,
        colWidths=[
            58 * mm,
            102 * mm,
        ],
        repeatRows=1,
        hAlign="LEFT",
    )

    _apply_analysis_table_style(
        table
    )

    return table


def _additional_result_rows(
    analysis: dict[str, Any],
) -> list[tuple[str, Any]]:
    raw = _raw_analysis_result(
        analysis
    )

    skip = {
        "dataset_rows",
        "row_count",
        "dataset_columns",
        "column_count",
        "test_name",
        "test",
        "analysis_name",
        "configuration",
        "tables",
        "diagnostics",
        "assumptions",
        "interpretation",
        "summary",
        "apa",
        "explanation",
        "detailed_explanation",
        "explanation_sections",
        "dataset_id",
        "user_id",
        "id",
        "_id",
    }

    rows: list[
        tuple[str, Any]
    ] = []

    for key, value in raw.items():
        if key in skip:
            continue

        if isinstance(
            value,
            (str, int, float, bool),
        ) or value is None:
            rows.append(
                (
                    _humanize(key),
                    value,
                )
            )

        elif isinstance(
            value,
            list,
        ) and all(
            not isinstance(
                item,
                (dict, list),
            )
            for item in value
        ):
            rows.append(
                (
                    _humanize(key),
                    ", ".join(
                        _display_value(item)
                        for item in value
                    ),
                )
            )

    return rows[:40]


def _extract_explanation(
    analysis: dict[str, Any],
) -> Any:
    raw = _raw_analysis_result(
        analysis
    )

    for container in (
        analysis,
        raw,
    ):
        if not isinstance(
            container,
            dict,
        ):
            continue

        for key in (
            "detailed_explanation",
            "explanation",
            "explanation_sections",
        ):
            value = container.get(
                key
            )

            if value:
                return value

    return None


def _append_explanation(
    story: list,
    explanation: Any,
    body_style,
    note_style,
) -> None:
    """
    Render the saved SSAS detailed explanation in the same logical
    structure used by frontend/src/pages/analysis/components/
    DetailedExplanation.jsx.

    Important: when the analysis service has saved a
    ``detailed_explanation`` object, this function does not rewrite,
    summarize, reinterpret, or renumber it. The title, introduction,
    section titles, and section paragraphs are rendered from the saved
    object as-is.
    """
    if not explanation:
        return

    # --------------------------------------------------------
    # Simple text fallback
    # --------------------------------------------------------
    if isinstance(
        explanation,
        str,
    ):
        story.append(
            Paragraph(
                "<b>SSAS EXPLANATION</b>",
                body_style,
            )
        )
        story.append(
            Paragraph(
                escape(
                    explanation
                ).replace(
                    "\n",
                    "<br/>",
                ),
                note_style,
            )
        )
        return

    # --------------------------------------------------------
    # Frontend DetailedExplanation object
    # --------------------------------------------------------
    if isinstance(
        explanation,
        dict,
    ):
        sections = explanation.get(
            "sections"
        )

        if isinstance(
            sections,
            list,
        ):
            explanation_label_style = ParagraphStyle(
                "SSASExplanationLabel",
                parent=body_style,
                fontName="Helvetica",
                fontSize=8,
                leading=10,
                textColor=colors.HexColor(
                    "#087F82"
                ),
                spaceBefore=4,
                spaceAfter=2,
            )

            explanation_title_style = ParagraphStyle(
                "SSASExplanationTitle",
                parent=body_style,
                fontName="Helvetica-Bold",
                fontSize=11.5,
                leading=15,
                textColor=colors.HexColor(
                    "#111827"
                ),
                spaceAfter=7,
            )

            explanation_intro_style = ParagraphStyle(
                "SSASExplanationIntro",
                parent=body_style,
                fontName="Helvetica",
                fontSize=9,
                leading=13,
                textColor=colors.HexColor(
                    "#263235"
                ),
                spaceAfter=9,
            )

            explanation_section_style = ParagraphStyle(
                "SSASExplanationSection",
                parent=body_style,
                fontName="Helvetica-Bold",
                fontSize=8.5,
                leading=11,
                textColor=colors.HexColor(
                    "#111827"
                ),
                spaceBefore=5,
                spaceAfter=4,
            )

            explanation_paragraph_style = ParagraphStyle(
                "SSASExplanationParagraph",
                parent=body_style,
                fontName="Helvetica",
                fontSize=7.8,
                leading=11,
                textColor=colors.HexColor(
                    "#334155"
                ),
                spaceAfter=4,
            )

            explanation_footer_style = ParagraphStyle(
                "SSASExplanationFooter",
                parent=body_style,
                fontName="Helvetica",
                fontSize=8,
                leading=11,
                textColor=colors.HexColor(
                    "#334155"
                ),
                borderColor=colors.HexColor(
                    "#D9E2E7"
                ),
                borderWidth=0.6,
                borderPadding=7,
                backColor=colors.HexColor(
                    "#F8FAFC"
                ),
                spaceBefore=8,
                spaceAfter=10,
            )

            story.append(
                Spacer(
                    1,
                    5,
                )
            )

            story.append(
                Paragraph(
                    "SSAS EXPLANATION",
                    explanation_label_style,
                )
            )

            title = explanation.get(
                "title"
            ) or "Detailed Statistical Explanation"

            story.append(
                Paragraph(
                    escape(
                        str(title)
                    ),
                    explanation_title_style,
                )
            )

            introduction = explanation.get(
                "introduction"
            )

            if introduction:
                story.append(
                    Paragraph(
                        escape(
                            str(introduction)
                        ).replace(
                            "\n",
                            "<br/>",
                        ),
                        explanation_intro_style,
                    )
                )

            for section_index, section in enumerate(
                sections
            ):
                if not isinstance(
                    section,
                    dict,
                ):
                    continue

                heading = (
                    section.get(
                        "title"
                    )
                    or section.get(
                        "heading"
                    )
                    or section.get(
                        "name"
                    )
                    or f"Section {section_index + 1}"
                )

                story.append(
                    Paragraph(
                        escape(
                            str(heading)
                        ),
                        explanation_section_style,
                    )
                )

                paragraphs = section.get(
                    "paragraphs"
                )

                if not isinstance(
                    paragraphs,
                    list,
                ):
                    fallback_content = (
                        section.get("text")
                        or section.get("content")
                        or section.get("body")
                        or section.get("description")
                    )

                    paragraphs = (
                        [fallback_content]
                        if fallback_content
                        else []
                    )

                for paragraph in paragraphs:
                    if paragraph is None:
                        continue

                    story.append(
                        Paragraph(
                            escape(
                                str(paragraph)
                            ).replace(
                                "\n",
                                "<br/>",
                            ),
                            explanation_paragraph_style,
                        )
                    )

                # The web Explanation component separates each section
                # with a subtle horizontal rule. Keep the same hierarchy
                # in the PDF without enclosing each section in a new box.
                if section_index < len(sections) - 1:
                    story.append(
                        HRFlowable(
                            width="100%",
                            thickness=0.35,
                            color=colors.HexColor(
                                "#E5E7EB"
                            ),
                            spaceBefore=3,
                            spaceAfter=4,
                        )
                    )

            story.append(
                Paragraph(
                    (
                        "Statistical results should be interpreted "
                        "together with the research design, sample "
                        "quality, measurement quality, assumptions, "
                        "effect size and subject-matter knowledge."
                    ),
                    explanation_footer_style,
                )
            )

            return

        # ----------------------------------------------------
        # Generic dictionary fallback for older saved results
        # ----------------------------------------------------
        story.append(
            Paragraph(
                "<b>SSAS EXPLANATION</b>",
                body_style,
            )
        )

        for key, value in explanation.items():
            story.append(
                Paragraph(
                    "<b>"
                    + escape(
                        _humanize(key)
                    )
                    + "</b>",
                    body_style,
                )
            )
            story.append(
                Paragraph(
                    escape(
                        _display_value(
                            value,
                            3500,
                        )
                    ).replace(
                        "\n",
                        "<br/>",
                    ),
                    note_style,
                )
            )
        return

    # --------------------------------------------------------
    # Generic list fallback for older saved results
    # --------------------------------------------------------
    if isinstance(
        explanation,
        list,
    ):
        story.append(
            Paragraph(
                "<b>SSAS EXPLANATION</b>",
                body_style,
            )
        )

        for index, section in enumerate(
            explanation,
            1,
        ):
            if isinstance(
                section,
                dict,
            ):
                heading = (
                    section.get("title")
                    or section.get("heading")
                    or section.get("name")
                    or f"Explanation {index}"
                )

                content = (
                    section.get("text")
                    or section.get("content")
                    or section.get("body")
                    or section.get("description")
                    or section
                )
            else:
                heading = f"Explanation {index}"
                content = section

            story.append(
                Paragraph(
                    "<b>"
                    + escape(
                        str(heading)
                    )
                    + "</b>",
                    body_style,
                )
            )

            story.append(
                Paragraph(
                    escape(
                        _display_value(
                            content,
                            3500,
                        )
                    ).replace(
                        "\n",
                        "<br/>",
                    ),
                    note_style,
                )
            )


# ============================================================
# Generic analysis table - last-resort compatibility
# ============================================================

def _generic_analysis_table(
    analysis: dict[str, Any],
    small_style,
) -> Table:
    raw = _raw_analysis_result(
        analysis
    )

    if not raw:
        raw = analysis

    flattened = _flatten_result(
        raw
    )

    if not flattened:
        flattened = [
            (
                "Result",
                "No structured result values were available.",
            )
        ]

    rows = [
        [
            _paragraph(
                "Statistic / Field",
                small_style,
            ),
            _paragraph(
                "Result",
                small_style,
            ),
        ]
    ]

    for label, value in flattened[:80]:
        rows.append(
            [
                _paragraph(
                    label,
                    small_style,
                ),
                _paragraph(
                    value,
                    small_style,
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            62 * mm,
            98 * mm,
        ],
        repeatRows=1,
        hAlign="LEFT",
    )

    _apply_analysis_table_style(
        table
    )

    return table


# ============================================================
# Footer / page number
# ============================================================

def _page_footer(
    canvas,
    document,
):
    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        8,
    )

    canvas.setFillColor(
        colors.HexColor(
            "#667477"
        )
    )

    canvas.drawString(
        18 * mm,
        10 * mm,
        "Smart Statistical Analysis System (SSAS)",
    )

    canvas.drawRightString(
        A4[0] - 18 * mm,
        10 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


# ============================================================
# Main PDF generator
# ============================================================

def generate_pdf_report(
    report_data: dict[str, Any],
    output_path: str,
) -> str:
    output = Path(
        output_path
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    chart_directory = (
        output.parent
        / f".{output.stem}_charts"
    )

    if chart_directory.exists():
        shutil.rmtree(
            chart_directory,
            ignore_errors=True,
        )

    chart_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=report_data.get(
            "title",
            "SSAS Statistical Analysis Report",
        ),
        author=(
            "Smart Statistical Analysis System"
        ),
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SSASTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor(
            "#073C43"
        ),
        spaceAfter=7,
    )

    subtitle_style = ParagraphStyle(
        "SSASSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor(
            "#617174"
        ),
        spaceAfter=18,
    )

    section_style = ParagraphStyle(
        "SSASSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor(
            "#073C43"
        ),
        spaceBefore=12,
        spaceAfter=8,
    )

    subsection_style = ParagraphStyle(
        "SSASSubsection",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor(
            "#087F82"
        ),
        spaceBefore=9,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "SSASBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor(
            "#263235"
        ),
        alignment=TA_LEFT,
        spaceAfter=6,
    )

    small_style = ParagraphStyle(
        "SSASSmall",
        parent=body_style,
        fontSize=8,
        leading=10,
        spaceAfter=0,
    )

    note_style = ParagraphStyle(
        "SSASNote",
        parent=body_style,
        fontSize=8.5,
        leading=12,
        leftIndent=8,
        rightIndent=8,
        borderColor=colors.HexColor(
            "#C7DBDD"
        ),
        borderWidth=0.5,
        borderPadding=7,
        backColor=colors.HexColor(
            "#F5FAFA"
        ),
        spaceBefore=5,
        spaceAfter=9,
    )

    story = []

    # ========================================================
    # Report heading
    # ========================================================
    story.append(
        Paragraph(
            "SMART STATISTICAL ANALYSIS SYSTEM",
            title_style,
        )
    )

    story.append(
        Paragraph(
            escape(
                report_data.get(
                    "title",
                    "Statistical Analysis Report",
                )
            ),
            styles["Heading1"],
        )
    )

    story.append(
        Paragraph(
            (
                "Complete dataset analysis, statistical results, "
                "visualizations, interpretation and conclusion"
            ),
            subtitle_style,
        )
    )

    # ========================================================
    # 1. Dataset Summary
    # ========================================================
    story.append(
        Paragraph(
            "1. Dataset Summary",
            section_style,
        )
    )

    dataset_summary = report_data.get(
        "dataset_summary",
        {},
    )

    summary_rows = [
        [
            _paragraph(
                "File name",
                small_style,
            ),
            _paragraph(
                dataset_summary.get(
                    "file_name",
                    "—",
                ),
                small_style,
            ),
        ],
        [
            _paragraph(
                "Row count",
                small_style,
            ),
            _paragraph(
                dataset_summary.get(
                    "row_count",
                    0,
                ),
                small_style,
            ),
        ],
        [
            _paragraph(
                "Column count",
                small_style,
            ),
            _paragraph(
                dataset_summary.get(
                    "column_count",
                    0,
                ),
                small_style,
            ),
        ],
        [
            _paragraph(
                "Date generated",
                small_style,
            ),
            _paragraph(
                _format_datetime(
                    dataset_summary.get(
                        "date_generated",
                        report_data.get(
                            "generated_at"
                        ),
                    )
                ),
                small_style,
            ),
        ],
    ]

    summary_table = Table(
        [
            [
                _paragraph(
                    "Dataset Property",
                    small_style,
                ),
                _paragraph(
                    "Value",
                    small_style,
                ),
            ],
            *summary_rows,
        ],
        colWidths=[
            50 * mm,
            110 * mm,
        ],
        hAlign="LEFT",
    )

    _apply_table_style(
        summary_table
    )

    story.append(
        summary_table
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )

    # ========================================================
    # 2. Statistical Analysis Results
    # ========================================================
    story.append(
        Paragraph(
            "2. Statistical Analysis Results",
            section_style,
        )
    )

    analyses = report_data.get(
        "analyses",
        [],
    )

    if not analyses:
        story.append(
            Paragraph(
                (
                    "No stored statistical analysis results were "
                    "found for this dataset. Run an analysis in "
                    "SSAS and generate the report again."
                ),
                note_style,
            )
        )

    else:
        for index, analysis in enumerate(
            analyses,
            1,
        ):
            title = (
                analysis.get("title")
                or _humanize(
                    analysis.get(
                        "method",
                        f"Analysis {index}",
                    )
                )
            )

            story.append(
                Paragraph(
                    (
                        f"2.{index} "
                        + escape(
                            str(title)
                        )
                    ),
                    subsection_style,
                )
            )

            # ------------------------------------------------
            # Analysis setup / configuration
            # ------------------------------------------------
            configuration_rows = (
                _configuration_rows(
                    analysis
                )
            )

            configuration_table = (
                _key_value_table(
                    configuration_rows,
                    small_style,
                    "Analysis Setup",
                    "Value",
                )
            )

            if configuration_table is not None:
                story.append(
                    Paragraph(
                        "<b>Analysis Setup</b>",
                        body_style,
                    )
                )

                story.append(
                    configuration_table
                )

                story.append(
                    Spacer(
                        1,
                        8,
                    )
                )

            # ------------------------------------------------
            # Every table produced by the statistical method
            # ------------------------------------------------
            structured_tables = (
                _collect_structured_tables(
                    analysis
                )
            )

            rendered_any_table = False

            for table_data in structured_tables:
                table_title = (
                    table_data.get(
                        "title"
                    )
                    or "Results"
                )

                story.append(
                    Paragraph(
                        (
                            "<b>"
                            + escape(
                                str(table_title)
                            )
                            + "</b>"
                        ),
                        body_style,
                    )
                )

                flowable = (
                    _result_table_flowable(
                        table_data,
                        small_style,
                    )
                )

                if flowable is not None:
                    story.append(
                        flowable
                    )

                    story.append(
                        Spacer(
                            1,
                            8,
                        )
                    )

                    rendered_any_table = True

            # ------------------------------------------------
            # Extra scalar statistics not already represented
            # by one of the result tables
            # ------------------------------------------------
            additional_rows = (
                _additional_result_rows(
                    analysis
                )
            )

            additional_table = (
                _key_value_table(
                    additional_rows,
                    small_style,
                    "Additional Statistic",
                    "Result",
                )
            )

            if additional_table is not None:
                story.append(
                    Paragraph(
                        "<b>Additional Results</b>",
                        body_style,
                    )
                )

                story.append(
                    additional_table
                )

                story.append(
                    Spacer(
                        1,
                        8,
                    )
                )

                rendered_any_table = True

            # Only use the old flattened layout when the saved
            # result truly contains no structured result tables.
            if not rendered_any_table:
                story.append(
                    _generic_analysis_table(
                        analysis,
                        small_style,
                    )
                )

                story.append(
                    Spacer(
                        1,
                        8,
                    )
                )

            # ------------------------------------------------
            # Exact SSAS explanation from the Analysis screen
            # ------------------------------------------------
            # Analysis methods save ``detailed_explanation`` together
            # with the result. The PDF must reproduce that saved
            # explanation instead of generating a second, different
            # interpretation.
            raw_result = (
                _raw_analysis_result(
                    analysis
                )
            )

            detailed_explanation = (
                _extract_explanation(
                    analysis
                )
            )

            if detailed_explanation:
                _append_explanation(
                    story,
                    detailed_explanation,
                    body_style,
                    note_style,
                )
            else:
                # Older saved results may not contain the same detailed
                # explanation object. In that case, keep only the saved
                # interpretation as a compatibility fallback.
                fallback_interpretation = (
                    analysis.get(
                        "interpretation"
                    )
                )

                if not fallback_interpretation:
                    fallback_interpretation = (
                        raw_result.get(
                            "interpretation"
                        )
                        if isinstance(
                            raw_result,
                            dict,
                        )
                        else None
                    )

                if fallback_interpretation:
                    story.append(
                        Paragraph(
                            "<b>Interpretation</b>",
                            body_style,
                        )
                    )

                    story.append(
                        Paragraph(
                            escape(
                                _display_value(
                                    fallback_interpretation,
                                    4000,
                                )
                            ).replace(
                                "\n",
                                "<br/>",
                            ),
                            note_style,
                        )
                    )

            # ------------------------------------------------
            # Assumptions/checks not already shaped as a table
            # ------------------------------------------------
            assumptions = analysis.get(
                "assumptions"
            )

            if (
                assumptions
                and not (
                    isinstance(
                        assumptions,
                        dict,
                    )
                    and isinstance(
                        assumptions.get(
                            "rows"
                        ),
                        list,
                    )
                )
            ):
                assumption_rows = []

                if isinstance(
                    assumptions,
                    dict,
                ):
                    assumption_rows = [
                        (
                            _humanize(key),
                            value,
                        )
                        for key, value
                        in assumptions.items()
                    ]

                assumption_table = (
                    _key_value_table(
                        assumption_rows,
                        small_style,
                        "Assumption / Check",
                        "Result",
                    )
                )

                if assumption_table is not None:
                    story.append(
                        Paragraph(
                            "<b>Assumptions / Checks</b>",
                            body_style,
                        )
                    )

                    story.append(
                        assumption_table
                    )

                    story.append(
                        Spacer(
                            1,
                            8,
                        )
                    )

                elif assumptions:
                    story.append(
                        Paragraph(
                            (
                                "<b>Assumptions / checks:</b> "
                                + escape(
                                    _display_value(
                                        assumptions,
                                        2000,
                                    )
                                )
                            ),
                            body_style,
                        )
                    )

            # ------------------------------------------------
            # APA / statistical statement
            # ------------------------------------------------
            apa = (
                analysis.get("apa")
                or (
                    raw_result.get("apa")
                    if isinstance(
                        raw_result,
                        dict,
                    )
                    else None
                )
            )

            if apa:
                story.append(
                    Paragraph(
                        (
                            "<b>APA / statistical statement:</b> "
                            + escape(
                                _display_value(
                                    apa,
                                    2000,
                                )
                            )
                        ),
                        body_style,
                    )
                )

            story.append(
                Spacer(
                    1,
                    12,
                )
            )

    # ========================================================
    # 3. Visualization and Interpretation
    # ========================================================
    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "3. Visualization and Interpretation",
            section_style,
        )
    )

    visualizations = report_data.get(
        "visualizations",
        [],
    )

    dataset_data = report_data.get(
        "dataset_data",
        {},
    )

    if not visualizations:
        story.append(
            Paragraph(
                (
                    "No visualizations were stored for this "
                    "dataset. Generate a chart in SSAS and then "
                    "generate the report again."
                ),
                note_style,
            )
        )

    else:
        for index, visualization in enumerate(
            visualizations,
            1,
        ):
            chart_type = (
                visualization.get(
                    "visualization_type"
                )
                or visualization.get(
                    "chart_type"
                )
                or "Visualization"
            )

            story.append(
                Paragraph(
                    (
                        f"3.{index} "
                        + escape(
                            _humanize(
                                chart_type
                            )
                        )
                    ),
                    subsection_style,
                )
            )

            chart_path = render_visualization_png(
                visualization,
                dataset_data,
                chart_directory,
                index,
            )

            if chart_path:
                image = ReportLabImage(
                    chart_path,
                    width=160 * mm,
                    height=90 * mm,
                )

                story.append(
                    image
                )
                story.append(
                    Spacer(
                        1,
                        6,
                    )
                )
            else:
                story.append(
                    Paragraph(
                        (
                            "The saved visualization metadata was "
                            "found, but SSAS could not reconstruct "
                            "the chart image for this report."
                        ),
                        note_style,
                    )
                )

            interpretation = visualization.get(
                "report_interpretation",
                {},
            )

            if isinstance(
                interpretation,
                dict,
            ):
                summary = interpretation.get(
                    "summary"
                )
                findings = interpretation.get(
                    "key_findings",
                    [],
                )

                if summary:
                    story.append(
                        Paragraph(
                            "<b>Interpretation</b>",
                            body_style,
                        )
                    )
                    story.append(
                        Paragraph(
                            escape(
                                str(summary)
                            ),
                            note_style,
                        )
                    )

                if findings:
                    findings_text = "<br/>".join(
                        (
                            "• "
                            + escape(
                                str(item)
                            )
                        )
                        for item in findings
                    )
                    story.append(
                        Paragraph(
                            findings_text,
                            body_style,
                        )
                    )

            story.append(
                Spacer(
                    1,
                    10,
                )
            )

    # ========================================================
    # 4. Conclusion
    # ========================================================
    story.append(
        Paragraph(
            "4. Conclusion",
            section_style,
        )
    )

    conclusion = report_data.get(
        "conclusion"
    )

    if conclusion:
        # Split a long rule-based conclusion into readable
        # paragraph-sized pieces without changing its content.
        text = str(conclusion)
        chunks = []
        current = []

        for sentence in text.split(". "):
            current.append(sentence)

            if len(". ".join(current)) >= 500:
                chunks.append(
                    ". ".join(current).strip()
                    + (
                        ""
                        if current[-1].endswith(".")
                        else "."
                    )
                )
                current = []

        if current:
            chunks.append(
                ". ".join(current).strip()
            )

        for chunk in chunks:
            story.append(
                Paragraph(
                    escape(chunk),
                    body_style,
                )
            )
    else:
        story.append(
            Paragraph(
                (
                    "The report was generated from the analyses "
                    "and visualizations stored by SSAS for this "
                    "dataset."
                ),
                body_style,
            )
        )

    try:
        document.build(
            story,
            onFirstPage=_page_footer,
            onLaterPages=_page_footer,
        )
    finally:
        shutil.rmtree(
            chart_directory,
            ignore_errors=True,
        )

    return str(output)
