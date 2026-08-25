import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def moving_average_plot(
    dataframe,
    x,
    y,
    window=3,
    title=None,
):

    data = dataframe[
        [x, y]
    ].copy()

    data[y] = pd.to_numeric(
        data[y],
        errors="coerce",
    )

    data = data.dropna()

    data = data.sort_values(
        x
    )

    data[
        "moving_average"
    ] = (
        data[y]
        .rolling(
            window=window,
            min_periods=1,
        )
        .mean()
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=data[x],
            y=data[y],
            mode="lines+markers",
            name="Original",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=data[x],
            y=data[
                "moving_average"
            ],
            mode="lines",
            name=(
                f"{window}-Point "
                "Moving Average"
            ),
        )
    )

    figure.update_layout(
        title=(
            title
            or "Moving Average Plot"
        ),
        xaxis_title=x,
        yaxis_title=y,
    )

    return figure


def step_chart(
    dataframe,
    x,
    y,
    title=None,
):

    data = dataframe[
        [x, y]
    ].dropna()

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=data[x],
            y=data[y],
            mode="lines+markers",
            line_shape="hv",
        )
    )

    figure.update_layout(
        title=(
            title
            or "Step Chart"
        ),
        xaxis_title=x,
        yaxis_title=y,
    )

    return figure


def stacked_area_chart(
    dataframe,
    x,
    y,
    group_by,
    title=None,
):

    if not group_by:
        raise ValueError(
            "group_by is required for a stacked area chart."
        )

    return px.area(
        dataframe,
        x=x,
        y=y,
        color=group_by,
        title=(
            title
            or "Stacked Area Chart"
        ),
    )
