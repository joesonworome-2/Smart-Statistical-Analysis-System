from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)
from openpyxl.utils import get_column_letter

from app.services.chart_renderer import (
    render_visualization_png,
)


# ============================================================
# SSAS Excel report theme
# ============================================================

TEAL = "007D80"
DARK_TEAL = "083F43"
LIGHT_TEAL = "E6F4F3"
PALE_TEAL = "F4FAFA"
WHITE = "FFFFFF"
TEXT = "202124"
MUTED = "5F6B6D"
BORDER_COLOR = "AAB8BA"
LIGHT_BORDER = "D9E2E3"
WARNING_FILL = "FFF7E6"
ERROR_FILL = "FDECEC"

THIN_BORDER = Side(
    style="thin",
    color=BORDER_COLOR,
)

LIGHT_SIDE = Side(
    style="thin",
    color=LIGHT_BORDER,
)


# ============================================================
# Formatting helpers
# ============================================================


def _humanize(value: Any) -> str:
    return (
        str(value or "")
        .replace("_", " ")
        .replace("-", " ")
        .strip()
        .title()
    )


def _format_number(value: Any) -> str:
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
    limit: int = 4000,
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


def _format_datetime(value: Any) -> str:
    text = str(value or "")

    if not text:
        return "—"

    try:
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


def _analysis_interpretation(
    analysis: dict[str, Any],
) -> str | None:
    interpretation = analysis.get(
        "interpretation"
    )

    if interpretation:
        return _display_value(
            interpretation,
            5000,
        )

    metadata = analysis.get(
        "metadata",
        {},
    )

    if isinstance(metadata, dict):
        metadata_interpretation = (
            metadata.get(
                "report_interpretation"
            )
        )

        if metadata_interpretation:
            return _display_value(
                metadata_interpretation,
                5000,
            )

    # Use the same report-builder interpretation logic used
    # by the PDF generator when an interpretation was not
    # explicitly saved with the statistical result.
    try:
        from app.services.report_builder import (
            build_analysis_interpretation,
        )

        generated = (
            build_analysis_interpretation(
                analysis
            )
        )

        if generated:
            return _display_value(
                generated,
                5000,
            )
    except Exception:
        pass

    return None


# ============================================================
# Worksheet style helpers
# ============================================================


def _style_cell(
    cell,
    *,
    font: Font | None = None,
    fill: PatternFill | None = None,
    alignment: Alignment | None = None,
    border: Border | None = None,
) -> None:
    if font is not None:
        cell.font = font

    if fill is not None:
        cell.fill = fill

    if alignment is not None:
        cell.alignment = alignment

    if border is not None:
        cell.border = border


def _merge_and_write(
    worksheet,
    row: int,
    start_column: int,
    end_column: int,
    value: Any,
    *,
    font: Font | None = None,
    fill: PatternFill | None = None,
    alignment: Alignment | None = None,
    border: Border | None = None,
    height: float | None = None,
) -> None:
    start = get_column_letter(
        start_column
    )
    end = get_column_letter(
        end_column
    )

    worksheet.merge_cells(
        f"{start}{row}:{end}{row}"
    )

    cell = worksheet.cell(
        row=row,
        column=start_column,
        value=_display_value(value),
    )

    _style_cell(
        cell,
        font=font,
        fill=fill,
        alignment=alignment,
        border=border,
    )

    if height is not None:
        worksheet.row_dimensions[
            row
        ].height = height


def _apply_range_border(
    worksheet,
    min_row: int,
    max_row: int,
    min_col: int,
    max_col: int,
    side: Side = THIN_BORDER,
) -> None:
    border = Border(
        left=side,
        right=side,
        top=side,
        bottom=side,
    )

    for row in worksheet.iter_rows(
        min_row=min_row,
        max_row=max_row,
        min_col=min_col,
        max_col=max_col,
    ):
        for cell in row:
            cell.border = border


def _section_title(
    worksheet,
    row: int,
    text: str,
    end_column: int,
) -> int:
    _merge_and_write(
        worksheet,
        row,
        1,
        end_column,
        text,
        font=Font(
            name="Arial",
            size=14,
            bold=True,
            color=WHITE,
        ),
        fill=PatternFill(
            "solid",
            fgColor=TEAL,
        ),
        alignment=Alignment(
            horizontal="left",
            vertical="center",
        ),
        height=26,
    )

    return row + 2


def _subsection_title(
    worksheet,
    row: int,
    text: str,
    end_column: int,
) -> int:
    _merge_and_write(
        worksheet,
        row,
        1,
        end_column,
        text,
        font=Font(
            name="Arial",
            size=12,
            bold=True,
            color=DARK_TEAL,
        ),
        fill=PatternFill(
            "solid",
            fgColor=LIGHT_TEAL,
        ),
        alignment=Alignment(
            horizontal="left",
            vertical="center",
        ),
        height=23,
    )

    return row + 1


def _label_text_block(
    worksheet,
    row: int,
    label: str,
    text: Any,
    end_column: int,
) -> int:
    _merge_and_write(
        worksheet,
        row,
        1,
        end_column,
        label,
        font=Font(
            name="Arial",
            size=10,
            bold=True,
            color=DARK_TEAL,
        ),
        fill=PatternFill(
            "solid",
            fgColor=PALE_TEAL,
        ),
        alignment=Alignment(
            horizontal="left",
            vertical="center",
        ),
        height=21,
    )

    row += 1

    display = _display_value(
        text,
        7000,
    )

    line_count = max(
        1,
        min(
            10,
            (len(display) // 105) + 1,
        ),
    )

    _merge_and_write(
        worksheet,
        row,
        1,
        end_column,
        display,
        font=Font(
            name="Arial",
            size=10,
            color=TEXT,
        ),
        alignment=Alignment(
            horizontal="left",
            vertical="top",
            wrap_text=True,
        ),
        border=Border(
            left=LIGHT_SIDE,
            right=LIGHT_SIDE,
            top=LIGHT_SIDE,
            bottom=LIGHT_SIDE,
        ),
        height=max(
            24,
            line_count * 17,
        ),
    )

    return row + 2


# ============================================================
# Dataset summary renderer
# ============================================================


def _write_dataset_summary(
    worksheet,
    row: int,
    report_data: dict[str, Any],
    end_column: int,
) -> int:
    dataset_summary = report_data.get(
        "dataset_summary",
        {},
    )

    rows = [
        (
            "File name",
            dataset_summary.get(
                "file_name",
                "—",
            ),
        ),
        (
            "Row count",
            dataset_summary.get(
                "row_count",
                0,
            ),
        ),
        (
            "Column count",
            dataset_summary.get(
                "column_count",
                0,
            ),
        ),
        (
            "Date generated",
            _format_datetime(
                dataset_summary.get(
                    "date_generated",
                    report_data.get(
                        "generated_at"
                    ),
                )
            ),
        ),
    ]

    # Header
    worksheet.cell(
        row=row,
        column=1,
        value="Dataset Property",
    )

    worksheet.merge_cells(
        start_row=row,
        start_column=2,
        end_row=row,
        end_column=end_column,
    )

    worksheet.cell(
        row=row,
        column=2,
        value="Value",
    )

    for column in range(
        1,
        end_column + 1,
    ):
        cell = worksheet.cell(
            row=row,
            column=column,
        )

        cell.font = Font(
            name="Arial",
            size=10,
            bold=True,
            color=DARK_TEAL,
        )
        cell.fill = PatternFill(
            "solid",
            fgColor=LIGHT_TEAL,
        )
        cell.alignment = Alignment(
            horizontal="left",
            vertical="center",
        )

    header_row = row
    row += 1

    for label, value in rows:
        worksheet.cell(
            row=row,
            column=1,
            value=label,
        )

        worksheet.merge_cells(
            start_row=row,
            start_column=2,
            end_row=row,
            end_column=end_column,
        )

        worksheet.cell(
            row=row,
            column=2,
            value=_display_value(
                value
            ),
        )

        worksheet.cell(
            row=row,
            column=1,
        ).font = Font(
            name="Arial",
            size=10,
            bold=True,
            color=TEXT,
        )

        worksheet.cell(
            row=row,
            column=2,
        ).font = Font(
            name="Arial",
            size=10,
            color=TEXT,
        )

        worksheet.cell(
            row=row,
            column=1,
        ).alignment = Alignment(
            vertical="top",
        )

        worksheet.cell(
            row=row,
            column=2,
        ).alignment = Alignment(
            vertical="top",
            wrap_text=True,
        )

        row += 1

    _apply_range_border(
        worksheet,
        header_row,
        row - 1,
        1,
        end_column,
    )

    return row + 1


# ============================================================
# Statistical result table renderer
# ============================================================


def _write_result_table(
    worksheet,
    row: int,
    table_data: dict[str, Any],
) -> int:
    columns = table_data.get(
        "columns",
        [],
    )

    rows = table_data.get(
        "rows",
        [],
    )

    if not isinstance(columns, list):
        return row

    if not columns:
        return row

    start_row = row

    # Header
    for column_index, column_name in enumerate(
        columns,
        1,
    ):
        cell = worksheet.cell(
            row=row,
            column=column_index,
            value=_display_value(
                column_name
            ),
        )

        cell.font = Font(
            name="Arial",
            size=10,
            bold=True,
            color=DARK_TEAL,
        )

        cell.fill = PatternFill(
            "solid",
            fgColor=LIGHT_TEAL,
        )

        cell.alignment = Alignment(
            horizontal=(
                "left"
                if column_index == 1
                else "right"
            ),
            vertical="center",
            wrap_text=True,
        )

    row += 1

    # Data rows
    for result_row in rows:
        for column_index, column_name in enumerate(
            columns,
            1,
        ):
            if isinstance(
                result_row,
                dict,
            ):
                raw_value = result_row.get(
                    column_name
                )
            elif isinstance(
                result_row,
                (list, tuple),
            ):
                list_index = (
                    column_index - 1
                )
                raw_value = (
                    result_row[list_index]
                    if list_index < len(
                        result_row
                    )
                    else ""
                )
            else:
                raw_value = result_row

            # Keep ordinary numeric values numeric in Excel,
            # while preserving very small values in scientific
            # notation so they are not displayed as zero.
            if isinstance(
                raw_value,
                bool,
            ):
                value = (
                    "Yes"
                    if raw_value
                    else "No"
                )

            elif isinstance(
                raw_value,
                int,
            ):
                value = raw_value

            elif isinstance(
                raw_value,
                float,
            ):
                if (
                    raw_value != 0
                    and abs(raw_value) < 0.001
                ):
                    value = _format_number(
                        raw_value
                    )
                else:
                    value = raw_value

            else:
                value = _display_value(
                    raw_value,
                    2500,
                )

            cell = worksheet.cell(
                row=row,
                column=column_index,
                value=value,
            )

            cell.font = Font(
                name="Arial",
                size=10,
                color=TEXT,
                bold=(
                    column_index == 1
                ),
            )

            cell.alignment = Alignment(
                horizontal=(
                    "left"
                    if column_index == 1
                    else "right"
                ),
                vertical="top",
                wrap_text=True,
            )

            if isinstance(
                value,
                int,
            ):
                cell.number_format = "#,##0"

            elif isinstance(
                value,
                float,
            ):
                cell.number_format = "#,##0.###"

        row += 1

    _apply_range_border(
        worksheet,
        start_row,
        max(
            start_row,
            row - 1,
        ),
        1,
        len(columns),
    )

    return row + 1


def _flatten_result(
    value: Any,
    prefix: str = "",
    output: list[
        tuple[str, Any]
    ] | None = None,
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
                "tables",
                "configuration",
                "interpretation",
                "assumptions",
                "apa",
                "metadata",
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
                    (
                        label,
                        item,
                    )
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
                        _display_value(
                            item
                        )
                        for item in value
                    ),
                )
            )
        else:
            for index, item in enumerate(
                value,
                1,
            ):
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


def _write_generic_analysis_table(
    worksheet,
    row: int,
    analysis: dict[str, Any],
) -> int:
    pairs = _flatten_result(
        analysis
    )

    if not pairs:
        return row

    start_row = row

    worksheet.cell(
        row=row,
        column=1,
        value="Field",
    )

    worksheet.cell(
        row=row,
        column=2,
        value="Result",
    )

    for column in (
        1,
        2,
    ):
        cell = worksheet.cell(
            row=row,
            column=column,
        )

        cell.font = Font(
            name="Arial",
            size=10,
            bold=True,
            color=DARK_TEAL,
        )

        cell.fill = PatternFill(
            "solid",
            fgColor=LIGHT_TEAL,
        )

        cell.alignment = Alignment(
            horizontal="left",
            vertical="center",
        )

    row += 1

    for field, value in pairs:
        worksheet.cell(
            row=row,
            column=1,
            value=field,
        )

        worksheet.cell(
            row=row,
            column=2,
            value=_display_value(
                value,
                3000,
            ),
        )

        worksheet.cell(
            row=row,
            column=1,
        ).font = Font(
            name="Arial",
            size=10,
            bold=True,
        )

        worksheet.cell(
            row=row,
            column=2,
        ).font = Font(
            name="Arial",
            size=10,
        )

        worksheet.cell(
            row=row,
            column=1,
        ).alignment = Alignment(
            vertical="top",
            wrap_text=True,
        )

        worksheet.cell(
            row=row,
            column=2,
        ).alignment = Alignment(
            vertical="top",
            wrap_text=True,
        )

        row += 1

    _apply_range_border(
        worksheet,
        start_row,
        row - 1,
        1,
        2,
    )

    return row + 1


# ============================================================
# Visualization renderer
# ============================================================


def _write_visualization(
    worksheet,
    row: int,
    visualization: dict[str, Any],
    dataset_data: dict[str, Any],
    chart_directory: Path,
    index: int,
    end_column: int,
) -> int:
    chart_type = (
        visualization.get(
            "visualization_type"
        )
        or visualization.get(
            "chart_type"
        )
        or "Visualization"
    )

    row = _subsection_title(
        worksheet,
        row,
        (
            f"3.{index} "
            f"{_humanize(chart_type)}"
        ),
        end_column,
    )

    chart_path = None

    try:
        chart_path = (
            render_visualization_png(
                visualization,
                dataset_data,
                chart_directory,
                index,
            )
        )
    except Exception:
        chart_path = None

    if chart_path:
        try:
            image = ExcelImage(
                chart_path
            )

            target_width = 820

            if image.width:
                scale = min(
                    1.0,
                    target_width
                    / float(image.width),
                )
            else:
                scale = 1.0

            image.width = int(
                image.width * scale
            )
            image.height = int(
                image.height * scale
            )

            # Guarantee a readable report-sized chart even
            # when the source image was unexpectedly small.
            if image.width < 600:
                ratio = (
                    image.height /
                    image.width
                    if image.width
                    else 0.56
                )
                image.width = 760
                image.height = int(
                    760 * ratio
                )

            worksheet.add_image(
                image,
                f"A{row}",
            )

            # Excel images float above cells. Reserve enough
            # rows so the interpretation starts below the chart.
            approximate_pixels_per_row = 23
            reserved_rows = max(
                18,
                int(
                    image.height /
                    approximate_pixels_per_row
                ) + 2,
            )

            for reserve_row in range(
                row,
                row + reserved_rows,
            ):
                worksheet.row_dimensions[
                    reserve_row
                ].height = 17

            row += reserved_rows

        except Exception:
            row = _label_text_block(
                worksheet,
                row,
                "Chart",
                (
                    "The visualization was stored, but the "
                    "chart image could not be embedded in the "
                    "Excel report."
                ),
                end_column,
            )

    else:
        row = _label_text_block(
            worksheet,
            row,
            "Chart",
            (
                "The saved visualization metadata was found, "
                "but SSAS could not reconstruct the chart image "
                "for this report."
            ),
            end_column,
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
            row = _label_text_block(
                worksheet,
                row,
                "Interpretation",
                summary,
                end_column,
            )

        if findings:
            findings_text = "\n".join(
                (
                    f"• {item}"
                    for item in findings
                )
            )

            row = _label_text_block(
                worksheet,
                row,
                "Key findings",
                findings_text,
                end_column,
            )

    elif interpretation:
        row = _label_text_block(
            worksheet,
            row,
            "Interpretation",
            interpretation,
            end_column,
        )

    return row + 1


# ============================================================
# Optional dataset-data reference sheet
# ============================================================


def _create_dataset_data_sheet(
    workbook: Workbook,
    report_data: dict[str, Any],
) -> None:
    dataset_data = report_data.get(
        "dataset_data",
        {},
    )

    columns = dataset_data.get(
        "columns",
        [],
    )

    rows = dataset_data.get(
        "rows",
        [],
    )

    if not columns:
        return

    worksheet = workbook.create_sheet(
        "Dataset Data"
    )

    worksheet.sheet_view.showGridLines = False
    worksheet.freeze_panes = "A2"

    for column_index, name in enumerate(
        columns,
        1,
    ):
        cell = worksheet.cell(
            row=1,
            column=column_index,
            value=name,
        )

        cell.font = Font(
            name="Arial",
            size=10,
            bold=True,
            color=WHITE,
        )

        cell.fill = PatternFill(
            "solid",
            fgColor=TEAL,
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    for row_index, data_row in enumerate(
        rows,
        2,
    ):
        for column_index, column_name in enumerate(
            columns,
            1,
        ):
            if isinstance(
                data_row,
                dict,
            ):
                value = data_row.get(
                    column_name
                )
            elif isinstance(
                data_row,
                (list, tuple),
            ):
                list_index = (
                    column_index - 1
                )
                value = (
                    data_row[list_index]
                    if list_index < len(
                        data_row
                    )
                    else ""
                )
            else:
                value = data_row

            cell = worksheet.cell(
                row=row_index,
                column=column_index,
                value=(
                    value
                    if isinstance(
                        value,
                        (int, float)
                    )
                    and not isinstance(
                        value,
                        bool,
                    )
                    else _display_value(
                        value,
                        2000,
                    )
                ),
            )

            cell.font = Font(
                name="Arial",
                size=10,
                color=TEXT,
            )

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=False,
            )

    # Auto-size with a conservative cap.
    for column_index, column_name in enumerate(
        columns,
        1,
    ):
        max_length = len(
            str(column_name)
        )

        # Sample the first 250 rows to keep report generation
        # fast for large datasets.
        for row_index in range(
            2,
            min(
                worksheet.max_row,
                251,
            ) + 1,
        ):
            value = worksheet.cell(
                row=row_index,
                column=column_index,
            ).value

            max_length = max(
                max_length,
                len(
                    str(
                        value
                        if value is not None
                        else ""
                    )
                ),
            )

        worksheet.column_dimensions[
            get_column_letter(
                column_index
            )
        ].width = min(
            max(
                12,
                max_length + 2,
            ),
            32,
        )

    worksheet.auto_filter.ref = (
        f"A1:{get_column_letter(len(columns))}"
        f"{worksheet.max_row}"
    )


# ============================================================
# Main Excel report generator
# ============================================================


def generate_excel_report(
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
        / f".{output.stem}_excel_charts"
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

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "SSAS Report"

    # Report is deliberately designed to look like the PDF
    # report instead of a raw field/value database export.
    end_column = 8

    worksheet.sheet_view.showGridLines = False
    worksheet.sheet_properties.pageSetUpPr.fitToPage = True
    worksheet.page_setup.orientation = "portrait"
    worksheet.page_setup.paperSize = worksheet.PAPERSIZE_A4
    worksheet.page_setup.fitToWidth = 1
    worksheet.page_setup.fitToHeight = 0
    worksheet.print_options.horizontalCentered = True

    worksheet.page_margins.left = 0.35
    worksheet.page_margins.right = 0.35
    worksheet.page_margins.top = 0.45
    worksheet.page_margins.bottom = 0.45
    worksheet.page_margins.header = 0.2
    worksheet.page_margins.footer = 0.2

    worksheet.oddFooter.left.text = (
        "Smart Statistical Analysis System"
    )
    worksheet.oddFooter.right.text = (
        "Page &P of &N"
    )

    # Widths chosen to give the report a PDF-like page shape.
    widths = {
        "A": 24,
        "B": 17,
        "C": 17,
        "D": 17,
        "E": 17,
        "F": 17,
        "G": 17,
        "H": 17,
    }

    for column, width in widths.items():
        worksheet.column_dimensions[
            column
        ].width = width

    row = 1

    # ========================================================
    # Heading
    # ========================================================

    _merge_and_write(
        worksheet,
        row,
        1,
        end_column,
        "SMART STATISTICAL ANALYSIS SYSTEM",
        font=Font(
            name="Arial",
            size=20,
            bold=True,
            color=WHITE,
        ),
        fill=PatternFill(
            "solid",
            fgColor=TEAL,
        ),
        alignment=Alignment(
            horizontal="center",
            vertical="center",
        ),
        height=34,
    )

    row += 1

    _merge_and_write(
        worksheet,
        row,
        1,
        end_column,
        report_data.get(
            "title",
            "SSAS Statistical Analysis Report",
        ),
        font=Font(
            name="Arial",
            size=16,
            bold=True,
            color=DARK_TEAL,
        ),
        alignment=Alignment(
            horizontal="center",
            vertical="center",
        ),
        height=28,
    )

    row += 1

    _merge_and_write(
        worksheet,
        row,
        1,
        end_column,
        (
            "Complete dataset analysis, statistical results, "
            "visualizations, interpretation and conclusion"
        ),
        font=Font(
            name="Arial",
            size=10,
            italic=True,
            color=MUTED,
        ),
        alignment=Alignment(
            horizontal="center",
            vertical="center",
        ),
        height=22,
    )

    row += 2

    # ========================================================
    # 1. Dataset Summary
    # ========================================================

    row = _section_title(
        worksheet,
        row,
        "1. Dataset Summary",
        end_column,
    )

    row = _write_dataset_summary(
        worksheet,
        row,
        report_data,
        end_column,
    )

    # ========================================================
    # 2. Statistical Analysis Results
    # ========================================================

    row = _section_title(
        worksheet,
        row,
        "2. Statistical Analysis Results",
        end_column,
    )

    analyses = report_data.get(
        "analyses",
        [],
    )

    if not analyses:
        row = _label_text_block(
            worksheet,
            row,
            "Statistical analysis",
            (
                "No stored statistical analysis results were "
                "found for this dataset. Run an analysis in "
                "SSAS and generate the report again."
            ),
            end_column,
        )

    else:
        for index, analysis in enumerate(
            analyses,
            1,
        ):
            title = (
                analysis.get(
                    "title"
                )
                or _humanize(
                    analysis.get(
                        "method",
                        f"Analysis {index}",
                    )
                )
            )

            row = _subsection_title(
                worksheet,
                row,
                f"2.{index} {title}",
                end_column,
            )

            configuration = analysis.get(
                "configuration",
                {},
            )

            if configuration:
                config_text = ", ".join(
                    (
                        f"{_humanize(key)}: "
                        f"{_display_value(value, 250)}"
                    )
                    for key, value
                    in configuration.items()
                )

                row = _label_text_block(
                    worksheet,
                    row,
                    "Configuration",
                    config_text,
                    end_column,
                )

            tables = analysis.get(
                "tables",
                [],
            )

            rendered_table = False

            if isinstance(tables, list):
                for table_data in tables:
                    if not isinstance(
                        table_data,
                        dict,
                    ):
                        continue

                    table_title = table_data.get(
                        "title"
                    )

                    if table_title:
                        _merge_and_write(
                            worksheet,
                            row,
                            1,
                            end_column,
                            table_title,
                            font=Font(
                                name="Arial",
                                size=10,
                                bold=True,
                                color=TEXT,
                            ),
                            alignment=Alignment(
                                horizontal="left",
                                vertical="center",
                            ),
                            height=21,
                        )

                        row += 1

                    next_row = _write_result_table(
                        worksheet,
                        row,
                        table_data,
                    )

                    if next_row != row:
                        rendered_table = True
                        row = next_row

            if not rendered_table:
                row = _write_generic_analysis_table(
                    worksheet,
                    row,
                    analysis,
                )

            interpretation = _analysis_interpretation(
                analysis
            )

            if interpretation:
                row = _label_text_block(
                    worksheet,
                    row,
                    "Interpretation",
                    interpretation,
                    end_column,
                )

            assumptions = analysis.get(
                "assumptions"
            )

            if assumptions:
                row = _label_text_block(
                    worksheet,
                    row,
                    "Assumptions / checks",
                    assumptions,
                    end_column,
                )

            apa = analysis.get(
                "apa"
            )

            if apa:
                row = _label_text_block(
                    worksheet,
                    row,
                    "APA / statistical statement",
                    apa,
                    end_column,
                )

            row += 1

    # ========================================================
    # 3. Visualization and Interpretation
    # ========================================================

    row = _section_title(
        worksheet,
        row,
        "3. Visualization and Interpretation",
        end_column,
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
        row = _label_text_block(
            worksheet,
            row,
            "Visualizations",
            (
                "No visualizations were stored for this dataset. "
                "Generate a chart in SSAS and generate the "
                "report again."
            ),
            end_column,
        )

    else:
        for index, visualization in enumerate(
            visualizations,
            1,
        ):
            row = _write_visualization(
                worksheet,
                row,
                visualization,
                dataset_data,
                chart_directory,
                index,
                end_column,
            )

    # ========================================================
    # 4. Conclusion
    # ========================================================

    row = _section_title(
        worksheet,
        row,
        "4. Conclusion",
        end_column,
    )

    conclusion = report_data.get(
        "conclusion"
    )

    if conclusion:
        row = _label_text_block(
            worksheet,
            row,
            "Overall conclusion",
            conclusion,
            end_column,
        )
    else:
        row = _label_text_block(
            worksheet,
            row,
            "Overall conclusion",
            (
                "No conclusion was available for this report."
            ),
            end_column,
        )

    # ========================================================
    # Final report formatting
    # ========================================================

    worksheet.print_area = (
        f"A1:H{max(1, row)}"
    )

    # Make all regular cells use Arial and keep long text
    # readable. Existing specialized styles remain unchanged.
    for sheet_row in worksheet.iter_rows(
        min_row=1,
        max_row=worksheet.max_row,
        min_col=1,
        max_col=end_column,
    ):
        for cell in sheet_row:
            if not cell.font.name:
                cell.font = Font(
                    name="Arial",
                    size=10,
                    color=TEXT,
                )

            if cell.alignment is None:
                cell.alignment = Alignment(
                    vertical="top",
                    wrap_text=True,
                )

    # Keep the underlying dataset as a reference sheet so the
    # Excel report still contains the data used to reconstruct
    # charts, without cluttering the PDF-like report sheet.
    _create_dataset_data_sheet(
        workbook,
        report_data,
    )

    try:
        workbook.save(
            output_path
        )
    finally:
        # Images are already embedded into the workbook after
        # save, so the temporary chart files can be removed.
        shutil.rmtree(
            chart_directory,
            ignore_errors=True,
        )

    return output_path
