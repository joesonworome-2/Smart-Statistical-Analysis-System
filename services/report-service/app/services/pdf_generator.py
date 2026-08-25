from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _stringify(
    value: Any,
) -> str:

    if value is None:
        return "-"

    if isinstance(
        value,
        (
            dict,
            list,
        ),
    ):
        return json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    return str(
        value
    )


def _truncate(
    value: Any,
    limit: int = 300,
) -> str:

    text = _stringify(
        value
    )

    if len(text) <= limit:
        return text

    return (
        text[:limit]
        + "..."
    )


def generate_pdf_report(
    report_data: dict[str, Any],
    output_path: str,
) -> str:

    Path(
        output_path
    ).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=report_data.get(
            "title",
            "SSAS Report",
        ),
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SSASTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "SSASSubtitle",
        parent=styles[
            "Normal"
        ],
        alignment=TA_CENTER,
        fontSize=10,
        spaceAfter=18,
    )

    section_style = ParagraphStyle(
        "SSASSection",
        parent=styles[
            "Heading2"
        ],
        fontSize=14,
        spaceBefore=10,
        spaceAfter=8,
    )

    normal_style = styles[
        "BodyText"
    ]

    story = []

    # ========================================================
    # Cover / heading
    # ========================================================

    story.append(
        Paragraph(
            (
                "SMART STATISTICAL "
                "ANALYSIS SYSTEM"
            ),
            title_style,
        )
    )

    story.append(
        Paragraph(
            report_data.get(
                "title",
                "Statistical Analysis Report",
            ),
            styles[
                "Heading1"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "Generated: "
                + str(
                    report_data.get(
                        "generated_at",
                        "",
                    )
                )
            ),
            subtitle_style,
        )
    )

    story.append(
        Spacer(
            1,
            10,
        )
    )

    # ========================================================
    # Dataset summary
    # ========================================================

    story.append(
        Paragraph(
            "1. Dataset Summary",
            section_style,
        )
    )

    dataset = report_data.get(
        "dataset",
        {},
    )

    dataset_rows = [
        [
            "Property",
            "Value",
        ]
    ]

    preferred_fields = [
        "original_filename",
        "filename",
        "file_name",
        "status",
        "file_size",
        "row_count",
        "column_count",
        "created_at",
    ]

    dataset_rows.append(
        [
            "Dataset ID",
            report_data.get(
                "dataset_id",
                "",
            ),
        ]
    )

    used = set()

    for field in preferred_fields:

        if field in dataset:

            dataset_rows.append(
                [
                    field.replace(
                        "_",
                        " ",
                    ).title(),
                    _truncate(
                        dataset[
                            field
                        ]
                    ),
                ]
            )

            used.add(
                field
            )

    for key, value in dataset.items():

        if (
            key in used
            or key == "_id"
            or isinstance(
                value,
                (
                    dict,
                    list,
                ),
            )
        ):
            continue

        dataset_rows.append(
            [
                str(key),
                _truncate(
                    value
                ),
            ]
        )

    dataset_table = Table(
        dataset_rows,
        colWidths=[
            55 * mm,
            105 * mm,
        ],
        repeatRows=1,
    )

    dataset_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        0,
                    ),
                    colors.lightgrey,
                ),
                (
                    "FONTNAME",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        0,
                    ),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.4,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "TOP",
                ),
                (
                    "FONTSIZE",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    8,
                ),
            ]
        )
    )

    story.append(
        dataset_table
    )

    story.append(
        Spacer(
            1,
            12,
        )
    )

    # ========================================================
    # Report overview
    # ========================================================

    story.append(
        Paragraph(
            "2. Report Overview",
            section_style,
        )
    )

    summary = report_data.get(
        "summary",
        {},
    )

    overview_rows = [
        [
            "Item",
            "Value",
        ],
        [
            "Analysis Results",
            summary.get(
                "analysis_count",
                0,
            ),
        ],
        [
            "Visualizations",
            summary.get(
                "visualization_count",
                0,
            ),
        ],
        [
            (
                "Smart Interpretation "
                "Available"
            ),
            str(
                summary.get(
                    (
                        "smart_"
                        "interpretation_"
                        "available"
                    ),
                    False,
                )
            ),
        ],
    ]

    overview_table = Table(
        overview_rows,
        colWidths=[
            90 * mm,
            70 * mm,
        ],
    )

    overview_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        0,
                    ),
                    colors.lightgrey,
                ),
                (
                    "FONTNAME",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        0,
                    ),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.4,
                    colors.grey,
                ),
            ]
        )
    )

    story.append(
        overview_table
    )

    # ========================================================
    # Analysis results
    # ========================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "3. Statistical Analysis Results",
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
                    "No stored statistical "
                    "analysis results were found "
                    "for this dataset."
                ),
                normal_style,
            )
        )

    else:

        for index, analysis in enumerate(
            analyses,
            1,
        ):

            analysis_type = (
                analysis.get(
                    "analysis_type"
                )
                or analysis.get(
                    "type"
                )
                or analysis.get(
                    "test_type"
                )
                or (
                    f"Analysis {index}"
                )
            )

            story.append(
                Paragraph(
                    (
                        f"3.{index} "
                        f"{str(analysis_type).replace('_', ' ').title()}"
                    ),
                    styles[
                        "Heading3"
                    ],
                )
            )

            rows = [
                [
                    "Field",
                    "Result",
                ]
            ]

            for key, value in (
                analysis.items()
            ):

                if key in {
                    "_id",
                    "user_id",
                    "dataset_id",
                }:
                    continue

                rows.append(
                    [
                        str(key).replace(
                            "_",
                            " ",
                        ).title(),
                        _truncate(
                            value,
                            500,
                        ),
                    ]
                )

            table = Table(
                rows,
                colWidths=[
                    55 * mm,
                    105 * mm,
                ],
                repeatRows=1,
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (
                                0,
                                0,
                            ),
                            (
                                -1,
                                0,
                            ),
                            colors.whitesmoke,
                        ),
                        (
                            "FONTNAME",
                            (
                                0,
                                0,
                            ),
                            (
                                -1,
                                0,
                            ),
                            "Helvetica-Bold",
                        ),
                        (
                            "GRID",
                            (
                                0,
                                0,
                            ),
                            (
                                -1,
                                -1,
                            ),
                            0.3,
                            colors.grey,
                        ),
                        (
                            "VALIGN",
                            (
                                0,
                                0,
                            ),
                            (
                                -1,
                                -1,
                            ),
                            "TOP",
                        ),
                        (
                            "FONTSIZE",
                            (
                                0,
                                0,
                            ),
                            (
                                -1,
                                -1,
                            ),
                            7,
                        ),
                    ]
                )
            )

            story.append(
                table
            )

            story.append(
                Spacer(
                    1,
                    12,
                )
            )

    # ========================================================
    # Visualization history
    # ========================================================

    story.append(
        Paragraph(
            "4. Visualizations",
            section_style,
        )
    )

    visualizations = (
        report_data.get(
            "visualizations",
            [],
        )
    )

    if not visualizations:

        story.append(
            Paragraph(
                (
                    "No stored visualization "
                    "records were found."
                ),
                normal_style,
            )
        )

    else:

        visualization_rows = [
            [
                "#",
                "Type",
                "Mode",
                "Created",
            ]
        ]

        for index, item in enumerate(
            visualizations,
            1,
        ):

            visualization_rows.append(
                [
                    index,
                    item.get(
                        "visualization_type",
                        item.get(
                            "chart_type",
                            "-",
                        ),
                    ),
                    item.get(
                        "generation_mode",
                        "-",
                    ),
                    item.get(
                        "created_at",
                        "-",
                    ),
                ]
            )

        visualization_table = Table(
            visualization_rows,
            colWidths=[
                12 * mm,
                55 * mm,
                40 * mm,
                53 * mm,
            ],
            repeatRows=1,
        )

        visualization_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            0,
                        ),
                        colors.lightgrey,
                    ),
                    (
                        "FONTNAME",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            0,
                        ),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            -1,
                        ),
                        0.4,
                        colors.grey,
                    ),
                    (
                        "FONTSIZE",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            -1,
                        ),
                        8,
                    ),
                ]
            )
        )

        story.append(
            visualization_table
        )

    # ========================================================
    # Smart interpretation
    # ========================================================

    story.append(
        Spacer(
            1,
            14,
        )
    )

    story.append(
        Paragraph(
            (
                "5. Smart Visualization "
                "Interpretation"
            ),
            section_style,
        )
    )

    smart = report_data.get(
        "smart_interpretation"
    )

    if (
        smart
        and smart.get(
            "available"
        )
    ):

        interpretation = smart.get(
            "interpretation",
            {},
        )

        result = interpretation.get(
            "interpretation",
            {},
        )

        recommendation = (
            interpretation.get(
                "recommendation",
                {},
            )
        )

        story.append(
            Paragraph(
                (
                    "<b>Recommended Chart:</b> "
                    + str(
                        recommendation.get(
                            "chart_type",
                            "-",
                        )
                    )
                ),
                normal_style,
            )
        )

        story.append(
            Paragraph(
                (
                    "<b>Confidence:</b> "
                    + str(
                        recommendation.get(
                            (
                                "confidence_"
                                "percent"
                            ),
                            "-",
                        )
                    )
                    + "%"
                ),
                normal_style,
            )
        )

        story.append(
            Spacer(
                1,
                6,
            )
        )

        story.append(
            Paragraph(
                str(
                    result.get(
                        "summary",
                        (
                            "No interpretation "
                            "summary available."
                        ),
                    )
                ),
                normal_style,
            )
        )

        findings = result.get(
            "key_findings",
            [],
        )

        if findings:

            story.append(
                Paragraph(
                    "Key Findings",
                    styles[
                        "Heading3"
                    ],
                )
            )

            for finding in findings:

                story.append(
                    Paragraph(
                        (
                            "• "
                            + str(
                                finding
                            )
                        ),
                        normal_style,
                    )
                )

        cautions = result.get(
            "cautions",
            [],
        )

        if cautions:

            story.append(
                Paragraph(
                    "Statistical Cautions",
                    styles[
                        "Heading3"
                    ],
                )
            )

            for caution in cautions:

                story.append(
                    Paragraph(
                        (
                            "• "
                            + str(
                                caution
                            )
                        ),
                        normal_style,
                    )
                )

    else:

        story.append(
            Paragraph(
                (
                    "Smart interpretation "
                    "was not available when "
                    "this report was generated."
                ),
                normal_style,
            )
        )

    # ========================================================
    # Conclusion
    # ========================================================

    story.append(
        Spacer(
            1,
            14,
        )
    )

    story.append(
        Paragraph(
            "6. Conclusion",
            section_style,
        )
    )

    story.append(
        Paragraph(
            (
                "This report was generated "
                "automatically by the Smart "
                "Statistical Analysis System. "
                "Statistical findings should "
                "be interpreted together with "
                "the reported assumptions, "
                "warnings and sample-size "
                "limitations."
            ),
            normal_style,
        )
    )

    document.build(
        story
    )

    return output_path
