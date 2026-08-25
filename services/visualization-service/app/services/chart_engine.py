from app.services.distribution_charts import (
    histogram,
    density_plot,
    box_plot,
    violin_plot,
    ecdf_plot,
)

from app.services.categorical_charts import (
    bar_chart,
    grouped_bar_chart,
    stacked_bar_chart,
    pie_chart,
    donut_chart,
)

from app.services.relationship_charts import (
    scatter_plot,
    bubble_chart,
    line_chart,
    area_chart,
)

from app.services.correlation_charts import (
    correlation_heatmap,
)

from app.services.multivariate_charts import (
    scatter_matrix,
    parallel_coordinates,
    scatter_3d,
)

from app.services.data_quality_charts import (
    missing_values_bar,
    missing_values_heatmap,
)
from app.services.regression_charts import (
    regression_line_plot,
    actual_vs_predicted_plot,
    residual_vs_fitted_plot,
    qq_plot,
    pp_plot,
    scale_location_plot,
    standardized_residual_plot,
    leverage_plot,
    cooks_distance_plot,
)

from app.services.advanced_charts import (
    error_bar_chart,
    confidence_interval_plot,
    pareto_chart,
    lollipop_chart,
    radar_chart,
    waterfall_chart,
    funnel_chart,
    frequency_polygon,
    forest_plot,
)

from app.services.time_series_charts import (
    moving_average_plot,
    step_chart,
    stacked_area_chart,
)

from app.services.hierarchical_charts import (
    treemap_chart,
    sunburst_chart,
    dendrogram_chart,
)


SUPPORTED_CHARTS = [
    "histogram",
    "density",
    "box",
    "violin",
    "ecdf",

    "bar",
    "horizontal_bar",
    "grouped_bar",
    "stacked_bar",
    "pie",
    "donut",

    "scatter",
    "bubble",
    "line",
    "area",

    "correlation_heatmap",

    "scatter_matrix",
    "parallel_coordinates",
    "scatter_3d",

    "missing_values_bar",
    "missing_values_heatmap",
    # Regression / diagnostics
    "regression_line",
    "actual_vs_predicted",
    "residual_vs_fitted",
    "qq_plot",
    "pp_plot",
    "scale_location",
    "standardized_residuals",
    "leverage",
    "cooks_distance",

    # Advanced statistical
    "error_bar",
    "confidence_interval",
    "pareto",
    "lollipop",
    "radar",
    "waterfall",
    "funnel",
    "frequency_polygon",
    "forest_plot",

    # Time series
    "moving_average",
    "step",
    "stacked_area",

    # Hierarchical
    "treemap",
    "sunburst",
    "dendrogram",
]


def generate_chart(
    dataframe,
    request,
):

    chart_type = (
        request.chart_type
        .strip()
        .lower()
    )

    if chart_type not in SUPPORTED_CHARTS:
        raise ValueError(
            f"Unsupported chart type '{chart_type}'."
        )

    if chart_type == "histogram":

        return histogram(
            dataframe,
            x=request.x,
            bins=request.bins or 20,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "density":

        return density_plot(
            dataframe,
            x=request.x,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "box":

        return box_plot(
            dataframe,
            x=request.x,
            y=request.y,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "violin":

        return violin_plot(
            dataframe,
            x=request.x,
            y=request.y,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "ecdf":

        return ecdf_plot(
            dataframe,
            x=request.x,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type in [
        "bar",
        "horizontal_bar",
    ]:

        orientation = (
            "horizontal"
            if chart_type
            == "horizontal_bar"
            else "vertical"
        )

        return bar_chart(
            dataframe,
            x=request.x,
            y=request.y,
            group_by=request.group_by,
            title=request.title,
            orientation=orientation,
        )

    if chart_type == "grouped_bar":

        return grouped_bar_chart(
            dataframe,
            x=request.x,
            y=request.y,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "stacked_bar":

        return stacked_bar_chart(
            dataframe,
            x=request.x,
            y=request.y,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "pie":

        return pie_chart(
            dataframe,
            category=(
                request.category
                or request.x
            ),
            value=request.value,
            title=request.title,
        )

    if chart_type == "donut":

        return donut_chart(
            dataframe,
            category=(
                request.category
                or request.x
            ),
            value=request.value,
            title=request.title,
        )

    if chart_type == "scatter":

        return scatter_plot(
            dataframe,
            x=request.x,
            y=request.y,
            group_by=request.group_by,
            size=request.size,
            title=request.title,
        )

    if chart_type == "bubble":

        return bubble_chart(
            dataframe,
            x=request.x,
            y=request.y,
            size=request.size,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "line":

        return line_chart(
            dataframe,
            x=request.x,
            y=request.y,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "area":

        return area_chart(
            dataframe,
            x=request.x,
            y=request.y,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "correlation_heatmap":

        return correlation_heatmap(
            dataframe,
            columns=request.columns,
            title=request.title,
        )

    if chart_type == "scatter_matrix":

        return scatter_matrix(
            dataframe,
            columns=request.columns,
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "parallel_coordinates":

        return parallel_coordinates(
            dataframe,
            columns=request.columns,
            title=request.title,
        )

    if chart_type == "scatter_3d":

        return scatter_3d(
            dataframe,
            x=request.x,
            y=request.y,
            z=request.z,
            group_by=request.group_by,
            size=request.size,
            title=request.title,
        )

    if chart_type == "missing_values_bar":

        return missing_values_bar(
            dataframe,
            title=request.title,
        )

    if chart_type == "missing_values_heatmap":

        return missing_values_heatmap(
            dataframe,
            title=request.title,
        )

    # ========================================================
    # Regression Visualizations
    # ========================================================

    if chart_type == "regression_line":

        return regression_line_plot(
            dataframe,
            x=request.x,
            y=request.y,
            title=request.title,
        )

    if chart_type == "actual_vs_predicted":

        return actual_vs_predicted_plot(
            dataframe,
            response_variable=request.y,
            predictor_variables=(
                request.columns or []
            ),
            title=request.title,
        )

    if chart_type == "residual_vs_fitted":

        return residual_vs_fitted_plot(
            dataframe,
            response_variable=request.y,
            predictor_variables=(
                request.columns or []
            ),
            title=request.title,
        )

    if chart_type == "qq_plot":

        return qq_plot(
            dataframe,
            response_variable=request.y,
            predictor_variables=(
                request.columns or []
            ),
            title=request.title,
        )

    if chart_type == "pp_plot":

        return pp_plot(
            dataframe,
            response_variable=request.y,
            predictor_variables=(
                request.columns or []
            ),
            title=request.title,
        )

    if chart_type == "scale_location":

        return scale_location_plot(
            dataframe,
            response_variable=request.y,
            predictor_variables=(
                request.columns or []
            ),
            title=request.title,
        )

    if chart_type == "standardized_residuals":

        return standardized_residual_plot(
            dataframe,
            response_variable=request.y,
            predictor_variables=(
                request.columns or []
            ),
            title=request.title,
        )

    if chart_type == "leverage":

        return leverage_plot(
            dataframe,
            response_variable=request.y,
            predictor_variables=(
                request.columns or []
            ),
            title=request.title,
        )

    if chart_type == "cooks_distance":

        return cooks_distance_plot(
            dataframe,
            response_variable=request.y,
            predictor_variables=(
                request.columns or []
            ),
            title=request.title,
        )

    # ========================================================
    # Advanced Statistical Charts
    # ========================================================

    if chart_type == "error_bar":

        return error_bar_chart(
            dataframe,
            x=request.x,
            y=request.y,
            error_column=request.options.get(
                "error_column"
            ),
            title=request.title,
        )

    if chart_type == "confidence_interval":

        return confidence_interval_plot(
            dataframe,
            x=request.x,
            y=request.y,
            lower_column=request.options.get(
                "lower_column"
            ),
            upper_column=request.options.get(
                "upper_column"
            ),
            title=request.title,
        )

    if chart_type == "pareto":

        return pareto_chart(
            dataframe,
            category=(
                request.category
                or request.x
            ),
            value=request.value,
            title=request.title,
        )

    if chart_type == "lollipop":

        return lollipop_chart(
            dataframe,
            x=request.x,
            y=request.y,
            title=request.title,
        )

    if chart_type == "radar":

        return radar_chart(
            dataframe,
            category=(
                request.category
                or request.x
            ),
            value=(
                request.value
                or request.y
            ),
            group_by=request.group_by,
            title=request.title,
        )

    if chart_type == "waterfall":

        return waterfall_chart(
            dataframe,
            category=(
                request.category
                or request.x
            ),
            value=(
                request.value
                or request.y
            ),
            title=request.title,
        )

    if chart_type == "funnel":

        return funnel_chart(
            dataframe,
            category=(
                request.category
                or request.x
            ),
            value=(
                request.value
                or request.y
            ),
            title=request.title,
        )

    if chart_type == "frequency_polygon":

        return frequency_polygon(
            dataframe,
            x=request.x,
            bins=(
                request.bins
                or 20
            ),
            title=request.title,
        )

    if chart_type == "forest_plot":

        return forest_plot(
            dataframe,
            estimate_column=request.x,
            label_column=request.y,
            lower_column=request.options.get(
                "lower_column"
            ),
            upper_column=request.options.get(
                "upper_column"
            ),
            title=request.title,
        )

    # ========================================================
    # Time-Series
    # ========================================================

    if chart_type == "moving_average":

        return moving_average_plot(
            dataframe,
            x=request.x,
            y=request.y,
            window=request.options.get(
                "window",
                3,
            ),
            title=request.title,
        )

    if chart_type == "step":

        return step_chart(
            dataframe,
            x=request.x,
            y=request.y,
            title=request.title,
        )

    if chart_type == "stacked_area":

        return stacked_area_chart(
            dataframe,
            x=request.x,
            y=request.y,
            group_by=request.group_by,
            title=request.title,
        )

    # ========================================================
    # Hierarchical
    # ========================================================

    if chart_type == "treemap":

        return treemap_chart(
            dataframe,
            path_columns=(
                request.columns or []
            ),
            value=request.value,
            title=request.title,
        )

    if chart_type == "sunburst":

        return sunburst_chart(
            dataframe,
            path_columns=(
                request.columns or []
            ),
            value=request.value,
            title=request.title,
        )

    if chart_type == "dendrogram":

        return dendrogram_chart(
            dataframe,
            columns=(
                request.columns or []
            ),
            method=request.options.get(
                "method",
                "ward",
            ),
            title=request.title,
        )
