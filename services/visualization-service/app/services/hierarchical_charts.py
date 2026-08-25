import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from scipy.cluster.hierarchy import (
    dendrogram,
    linkage,
)


def treemap_chart(
    dataframe,
    path_columns,
    value=None,
    title=None,
):

    if not path_columns:
        raise ValueError(
            "At least one hierarchy column is required."
        )

    return px.treemap(
        dataframe,
        path=path_columns,
        values=value,
        title=(
            title
            or "Treemap"
        ),
    )


def sunburst_chart(
    dataframe,
    path_columns,
    value=None,
    title=None,
):

    if not path_columns:
        raise ValueError(
            "At least one hierarchy column is required."
        )

    return px.sunburst(
        dataframe,
        path=path_columns,
        values=value,
        title=(
            title
            or "Sunburst Chart"
        ),
    )


def dendrogram_chart(
    dataframe,
    columns,
    method="ward",
    title=None,
):

    if not columns:
        raise ValueError(
            "Numeric columns are required."
        )

    data = dataframe[
        columns
    ].copy()

    for column in columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    data = data.dropna()

    if len(data) < 2:
        raise ValueError(
            "At least two complete observations are required."
        )

    linkage_matrix = linkage(
        data.to_numpy(
            dtype=float
        ),
        method=method,
    )

    result = dendrogram(
        linkage_matrix,
        no_plot=True,
    )

    figure = go.Figure()

    for x_values, y_values in zip(
        result["icoord"],
        result["dcoord"],
    ):

        figure.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines",
                showlegend=False,
            )
        )

    figure.update_layout(
        title=(
            title
            or "Hierarchical Clustering Dendrogram"
        ),
        xaxis_title="Observations",
        yaxis_title="Distance",
    )

    return figure
