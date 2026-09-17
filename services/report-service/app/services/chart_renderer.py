from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ============================================================
# Helpers
# ============================================================

def _config(
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
        suggested = recommendation.get(
            "suggested_config",
            {},
        )
        if isinstance(suggested, dict):
            return suggested

    return {}


def _chart_type(
    visualization: dict[str, Any],
) -> str:
    return str(
        visualization.get(
            "visualization_type"
        )
        or visualization.get(
            "chart_type"
        )
        or "visualization"
    ).lower()


def _humanize(
    value: str,
) -> str:
    return (
        value
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )


def _numeric(
    dataframe: pd.DataFrame,
    column: str | None,
) -> pd.Series:
    if (
        not column
        or column not in dataframe.columns
    ):
        return pd.Series(
            dtype=float
        )

    return pd.to_numeric(
        dataframe[column],
        errors="coerce",
    ).dropna()


def _first_numeric_columns(
    dataframe: pd.DataFrame,
    count: int = 2,
) -> list[str]:
    output = []

    for column in dataframe.columns:
        numeric = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        if numeric.notna().sum() >= 2:
            output.append(column)

        if len(output) >= count:
            break

    return output


def _first_categorical_column(
    dataframe: pd.DataFrame,
) -> str | None:
    for column in dataframe.columns:
        series = dataframe[
            column
        ].dropna()

        if (
            not series.empty
            and series.nunique() <= 30
        ):
            return column

    return (
        dataframe.columns[0]
        if len(dataframe.columns)
        else None
    )


def _line_x_values(
    dataframe: pd.DataFrame,
    x: str | None,
):
    if (
        x
        and x in dataframe.columns
    ):
        original = dataframe[x]

        parsed_dates = pd.to_datetime(
            original,
            errors="coerce",
        )

        if parsed_dates.notna().mean() >= 0.7:
            return parsed_dates

        return original

    return np.arange(
        len(dataframe)
    )


# ============================================================
# Render saved SSAS visualization to PNG
# ============================================================

def render_visualization_png(
    visualization: dict[str, Any],
    dataset_data: dict[str, Any],
    output_directory: str | Path,
    index: int,
) -> str | None:
    rows = dataset_data.get(
        "rows",
        [],
    )

    columns = dataset_data.get(
        "columns",
        [],
    )

    if not rows:
        return None

    dataframe = pd.DataFrame(
        rows,
        columns=(
            columns or None
        ),
    )

    if dataframe.empty:
        return None

    chart_type = _chart_type(
        visualization
    )

    config = _config(
        visualization
    )

    x = config.get("x")
    y = config.get("y")
    category = (
        config.get("category")
        or config.get("group_by")
    )

    requested_columns = config.get(
        "columns"
    )

    if not isinstance(
        requested_columns,
        list,
    ):
        requested_columns = []

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_directory
        / f"visualization_{index:03d}.png"
    )

    fig, ax = plt.subplots(
        figsize=(8.2, 4.6),
        dpi=145,
    )

    title = _humanize(
        chart_type
    )

    try:
        # ====================================================
        # Missing-data charts
        # ====================================================
        if chart_type == "missing_values_bar":
            missing = dataframe.isna().sum()
            missing = missing[
                missing > 0
            ]

            if missing.empty:
                missing = dataframe.isna().sum()

            ax.bar(
                missing.index.astype(str),
                missing.values,
            )
            ax.set_ylabel(
                "Missing values"
            )
            ax.tick_params(
                axis="x",
                rotation=40,
            )

        elif chart_type == "missing_values_heatmap":
            matrix = dataframe.isna().astype(int)
            ax.imshow(
                matrix.values,
                aspect="auto",
                interpolation="nearest",
            )
            ax.set_xticks(
                np.arange(
                    len(matrix.columns)
                )
            )
            ax.set_xticklabels(
                matrix.columns,
                rotation=45,
                ha="right",
            )
            ax.set_ylabel(
                "Case"
            )

        # ====================================================
        # Correlation heatmap
        # ====================================================
        elif chart_type == "correlation_heatmap":
            selected = [
                column
                for column in requested_columns
                if column in dataframe.columns
            ]

            if not selected:
                selected = _first_numeric_columns(
                    dataframe,
                    count=min(
                        8,
                        len(dataframe.columns),
                    ),
                )

            numeric = dataframe[
                selected
            ].apply(
                pd.to_numeric,
                errors="coerce",
            )

            correlation = numeric.corr()

            image = ax.imshow(
                correlation.values,
                vmin=-1,
                vmax=1,
                aspect="auto",
            )

            ax.set_xticks(
                np.arange(
                    len(correlation.columns)
                )
            )
            ax.set_yticks(
                np.arange(
                    len(correlation.index)
                )
            )
            ax.set_xticklabels(
                correlation.columns,
                rotation=45,
                ha="right",
            )
            ax.set_yticklabels(
                correlation.index,
            )

            fig.colorbar(
                image,
                ax=ax,
                fraction=0.035,
                pad=0.04,
            )

        # ====================================================
        # Histogram / density / ECDF
        # ====================================================
        elif chart_type in {
            "histogram",
            "density",
            "ecdf",
            "frequency_polygon",
        }:
            variable = x or y

            if not variable:
                numeric_columns = _first_numeric_columns(
                    dataframe,
                    1,
                )
                variable = (
                    numeric_columns[0]
                    if numeric_columns
                    else None
                )

            values = _numeric(
                dataframe,
                variable,
            )

            if values.empty:
                raise ValueError(
                    "No numeric data available."
                )

            if chart_type == "ecdf":
                ordered = np.sort(
                    values.to_numpy()
                )
                probabilities = (
                    np.arange(
                        1,
                        len(ordered) + 1,
                    )
                    / len(ordered)
                )
                ax.step(
                    ordered,
                    probabilities,
                    where="post",
                )
                ax.set_ylabel(
                    "Cumulative proportion"
                )

            elif chart_type == "frequency_polygon":
                counts, edges = np.histogram(
                    values,
                    bins=int(
                        config.get(
                            "bins",
                            20,
                        )
                    ),
                )
                centers = (
                    edges[:-1]
                    + edges[1:]
                ) / 2
                ax.plot(
                    centers,
                    counts,
                    marker="o",
                )
                ax.set_ylabel(
                    "Frequency"
                )

            else:
                ax.hist(
                    values,
                    bins=int(
                        config.get(
                            "bins",
                            20,
                        )
                    ),
                    density=(
                        chart_type == "density"
                    ),
                    alpha=0.85,
                )
                ax.set_ylabel(
                    "Density"
                    if chart_type == "density"
                    else "Frequency"
                )

            if variable:
                ax.set_xlabel(
                    variable
                )

        # ====================================================
        # Box / violin
        # ====================================================
        elif chart_type in {
            "box",
            "violin",
        }:
            numeric_variable = y or x
            group_variable = (
                x
                if y
                else category
            )

            if (
                numeric_variable
                and numeric_variable
                in dataframe.columns
                and group_variable
                and group_variable
                in dataframe.columns
                and group_variable
                != numeric_variable
            ):
                groups = []
                labels = []

                for name, group in dataframe.groupby(
                    group_variable
                ):
                    values = pd.to_numeric(
                        group[numeric_variable],
                        errors="coerce",
                    ).dropna()

                    if not values.empty:
                        groups.append(
                            values.to_numpy()
                        )
                        labels.append(
                            str(name)
                        )

                if chart_type == "violin":
                    ax.violinplot(
                        groups,
                        showmeans=True,
                        showmedians=True,
                    )
                    ax.set_xticks(
                        np.arange(
                            1,
                            len(labels) + 1,
                        )
                    )
                    ax.set_xticklabels(
                        labels,
                        rotation=35,
                        ha="right",
                    )
                else:
                    ax.boxplot(
                        groups,
                        labels=labels,
                    )
                    ax.tick_params(
                        axis="x",
                        rotation=35,
                    )

                ax.set_ylabel(
                    numeric_variable
                )

            else:
                values = _numeric(
                    dataframe,
                    numeric_variable,
                )

                if values.empty:
                    numeric_columns = _first_numeric_columns(
                        dataframe,
                        1,
                    )
                    numeric_variable = (
                        numeric_columns[0]
                        if numeric_columns
                        else None
                    )
                    values = _numeric(
                        dataframe,
                        numeric_variable,
                    )

                if chart_type == "violin":
                    ax.violinplot(
                        values.to_numpy(),
                        showmeans=True,
                        showmedians=True,
                    )
                    ax.set_xticks([1])
                    ax.set_xticklabels(
                        [numeric_variable or "Value"]
                    )
                else:
                    ax.boxplot(
                        values.to_numpy(),
                        labels=[
                            numeric_variable or "Value"
                        ],
                    )

        # ====================================================
        # Scatter / regression / bubble
        # ====================================================
        elif chart_type in {
            "scatter",
            "bubble",
            "regression_line",
            "actual_vs_predicted",
            "residual_vs_fitted",
        }:
            if (
                not x
                or not y
                or x not in dataframe.columns
                or y not in dataframe.columns
            ):
                numeric_columns = _first_numeric_columns(
                    dataframe,
                    2,
                )
                if len(numeric_columns) < 2:
                    raise ValueError(
                        "Two numeric variables are required."
                    )
                x, y = numeric_columns[:2]

            working = dataframe[
                [x, y]
            ].apply(
                pd.to_numeric,
                errors="coerce",
            ).dropna()

            if working.empty:
                raise ValueError(
                    "No usable paired values."
                )

            ax.scatter(
                working[x],
                working[y],
                alpha=0.75,
            )

            if chart_type in {
                "regression_line",
                "actual_vs_predicted",
            } and working[x].nunique() > 1:
                coefficients = np.polyfit(
                    working[x],
                    working[y],
                    1,
                )
                ordered_x = np.linspace(
                    working[x].min(),
                    working[x].max(),
                    100,
                )
                predicted = (
                    coefficients[0]
                    * ordered_x
                    + coefficients[1]
                )
                ax.plot(
                    ordered_x,
                    predicted,
                )

            ax.set_xlabel(x)
            ax.set_ylabel(y)

        # ====================================================
        # Pie / donut / sunburst representation
        # ====================================================
        elif chart_type in {
            "pie",
            "donut",
            "sunburst",
        }:
            variable = (
                category
                or x
                or _first_categorical_column(
                    dataframe
                )
            )

            if not variable:
                raise ValueError(
                    "A categorical variable is required."
                )

            counts = dataframe[
                variable
            ].dropna().astype(str).value_counts().head(12)

            wedge_properties = None

            if chart_type == "donut":
                wedge_properties = {
                    "width": 0.45
                }

            ax.pie(
                counts.values,
                labels=counts.index,
                autopct="%1.1f%%",
                wedgeprops=wedge_properties,
            )
            ax.set_ylabel("")

        # ====================================================
        # Treemap representation as ranked category blocks
        # ====================================================
        elif chart_type == "treemap":
            variable = (
                category
                or x
                or _first_categorical_column(
                    dataframe
                )
            )

            counts = dataframe[
                variable
            ].dropna().astype(str).value_counts().head(15)

            ax.barh(
                counts.index[::-1],
                counts.values[::-1],
            )
            ax.set_xlabel(
                "Frequency"
            )

        # ====================================================
        # Bar charts
        # ====================================================
        elif chart_type in {
            "bar",
            "horizontal_bar",
        }:
            if (
                x
                and y
                and x in dataframe.columns
                and y in dataframe.columns
            ):
                working = dataframe[
                    [x, y]
                ].copy()
                working[y] = pd.to_numeric(
                    working[y],
                    errors="coerce",
                )
                grouped = (
                    working
                    .dropna()
                    .groupby(x)[y]
                    .mean()
                    .sort_values(
                        ascending=False
                    )
                    .head(20)
                )

                labels = grouped.index.astype(str)
                values = grouped.values

                if chart_type == "horizontal_bar":
                    ax.barh(
                        labels[::-1],
                        values[::-1],
                    )
                    ax.set_xlabel(y)
                else:
                    ax.bar(
                        labels,
                        values,
                    )
                    ax.set_ylabel(y)
                    ax.tick_params(
                        axis="x",
                        rotation=35,
                    )

            else:
                variable = (
                    x
                    or category
                    or _first_categorical_column(
                        dataframe
                    )
                )

                counts = dataframe[
                    variable
                ].dropna().astype(str).value_counts().head(20)

                if chart_type == "horizontal_bar":
                    ax.barh(
                        counts.index[::-1],
                        counts.values[::-1],
                    )
                    ax.set_xlabel(
                        "Frequency"
                    )
                else:
                    ax.bar(
                        counts.index,
                        counts.values,
                    )
                    ax.set_ylabel(
                        "Frequency"
                    )
                    ax.tick_params(
                        axis="x",
                        rotation=35,
                    )

        # ====================================================
        # Line / area / step / moving average / stacked area
        # ====================================================
        elif chart_type in {
            "line",
            "area",
            "step",
            "moving_average",
            "stacked_area",
        }:
            if not y:
                numeric_columns = _first_numeric_columns(
                    dataframe,
                    3,
                )
                if not numeric_columns:
                    raise ValueError(
                        "No numeric variable available."
                    )
                y = numeric_columns[0]

            x_values = _line_x_values(
                dataframe,
                x,
            )

            if chart_type == "stacked_area":
                y_columns = requested_columns

                if not y_columns:
                    y_columns = _first_numeric_columns(
                        dataframe,
                        4,
                    )

                y_columns = [
                    column
                    for column in y_columns
                    if column in dataframe.columns
                ]

                arrays = []
                labels = []

                for column in y_columns:
                    values = pd.to_numeric(
                        dataframe[column],
                        errors="coerce",
                    ).fillna(0)
                    arrays.append(
                        values.to_numpy()
                    )
                    labels.append(column)

                ax.stackplot(
                    x_values,
                    *arrays,
                    labels=labels,
                )
                ax.legend(
                    loc="best",
                    fontsize=7,
                )

            else:
                values = pd.to_numeric(
                    dataframe[y],
                    errors="coerce",
                )

                mask = values.notna()

                plot_x = np.asarray(
                    x_values
                )[mask.to_numpy()]
                plot_y = values[
                    mask
                ].to_numpy()

                if chart_type == "area":
                    ax.fill_between(
                        plot_x,
                        plot_y,
                        alpha=0.55,
                    )
                    ax.plot(
                        plot_x,
                        plot_y,
                    )

                elif chart_type == "step":
                    ax.step(
                        plot_x,
                        plot_y,
                        where="mid",
                    )

                elif chart_type == "moving_average":
                    window = int(
                        config.get(
                            "window",
                            3,
                        )
                    )
                    moving = pd.Series(
                        plot_y
                    ).rolling(
                        window=max(
                            2,
                            window,
                        ),
                        min_periods=1,
                    ).mean()
                    ax.plot(
                        plot_x,
                        plot_y,
                        alpha=0.45,
                        label=y,
                    )
                    ax.plot(
                        plot_x,
                        moving,
                        label=(
                            f"{window}-period moving average"
                        ),
                    )
                    ax.legend(
                        fontsize=8
                    )

                else:
                    ax.plot(
                        plot_x,
                        plot_y,
                        marker="o",
                        markersize=3,
                    )

                ax.set_ylabel(y)

            if x:
                ax.set_xlabel(x)

        # ====================================================
        # Fallback
        # ====================================================
        else:
            numeric_columns = _first_numeric_columns(
                dataframe,
                1,
            )

            if numeric_columns:
                variable = numeric_columns[0]
                values = _numeric(
                    dataframe,
                    variable,
                )
                ax.plot(
                    np.arange(
                        len(values)
                    ),
                    values.to_numpy(),
                )
                ax.set_ylabel(variable)
                ax.set_xlabel("Case")
            else:
                variable = _first_categorical_column(
                    dataframe
                )
                counts = dataframe[
                    variable
                ].dropna().astype(str).value_counts().head(20)
                ax.bar(
                    counts.index,
                    counts.values,
                )
                ax.tick_params(
                    axis="x",
                    rotation=35,
                )

        ax.set_title(
            title
        )
        ax.grid(
            True,
            alpha=0.15,
        )

        fig.tight_layout()

        fig.savefig(
            output_path,
            bbox_inches="tight",
        )

        plt.close(fig)

        return str(
            output_path
        )

    except Exception:
        plt.close(fig)
        return None
