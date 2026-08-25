import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go


def error_bar_chart(
    dataframe,
    x,
    y,
    error_column,
    title=None,
):

    return px.scatter(
        dataframe,
        x=x,
        y=y,
        error_y=error_column,
        title=(
            title
            or "Error Bar Chart"
        ),
    )


def confidence_interval_plot(
    dataframe,
    x,
    y,
    lower_column,
    upper_column,
    title=None,
):

    data = dataframe[
        [
            x,
            y,
            lower_column,
            upper_column,
        ]
    ].dropna()

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=data[x],
            y=data[upper_column],
            mode="lines",
            line=dict(
                width=0
            ),
            showlegend=False,
        )
    )

    figure.add_trace(
        go.Scatter(
            x=data[x],
            y=data[lower_column],
            mode="lines",
            fill="tonexty",
            name="Confidence Interval",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=data[x],
            y=data[y],
            mode="lines+markers",
            name=y,
        )
    )

    figure.update_layout(
        title=(
            title
            or "Confidence Interval Plot"
        )
    )

    return figure


def pareto_chart(
    dataframe,
    category,
    value=None,
    title=None,
):

    if value:

        data = (
            dataframe
            .groupby(
                category,
                as_index=False
            )[value]
            .sum()
        )

        data = data.sort_values(
            value,
            ascending=False,
        )

        values = data[
            value
        ].to_numpy()

    else:

        data = (
            dataframe[
                category
            ]
            .value_counts()
            .reset_index()
        )

        data.columns = [
            category,
            "count",
        ]

        value = "count"

        values = data[
            value
        ].to_numpy()

    cumulative = (
        np.cumsum(
            values
        )
        / np.sum(
            values
        )
        * 100
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=data[
                category
            ],
            y=values,
            name="Frequency",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=data[
                category
            ],
            y=cumulative,
            name="Cumulative %",
            mode="lines+markers",
            yaxis="y2",
        )
    )

    figure.update_layout(
        title=(
            title
            or "Pareto Chart"
        ),
        yaxis=dict(
            title="Frequency"
        ),
        yaxis2=dict(
            title="Cumulative %",
            overlaying="y",
            side="right",
            range=[0, 100],
        ),
    )

    return figure


def lollipop_chart(
    dataframe,
    x,
    y,
    title=None,
):

    data = dataframe[
        [x, y]
    ].dropna()

    figure = go.Figure()

    for _, row in data.iterrows():

        figure.add_shape(
            type="line",
            x0=row[x],
            x1=row[x],
            y0=0,
            y1=row[y],
        )

    figure.add_trace(
        go.Scatter(
            x=data[x],
            y=data[y],
            mode="markers",
            name=y,
        )
    )

    figure.update_layout(
        title=(
            title
            or "Lollipop Chart"
        ),
        xaxis_title=x,
        yaxis_title=y,
    )

    return figure


def radar_chart(
    dataframe,
    category,
    value,
    group_by=None,
    title=None,
):

    figure = go.Figure()

    if group_by:

        for group_value, group_data in dataframe.groupby(
            group_by
        ):

            theta = group_data[
                category
            ].astype(str).tolist()

            r = group_data[
                value
            ].tolist()

            if theta:
                theta.append(
                    theta[0]
                )

                r.append(
                    r[0]
                )

            figure.add_trace(
                go.Scatterpolar(
                    r=r,
                    theta=theta,
                    fill="toself",
                    name=str(
                        group_value
                    ),
                )
            )

    else:

        theta = dataframe[
            category
        ].astype(str).tolist()

        r = dataframe[
            value
        ].tolist()

        if theta:
            theta.append(
                theta[0]
            )

            r.append(
                r[0]
            )

        figure.add_trace(
            go.Scatterpolar(
                r=r,
                theta=theta,
                fill="toself",
                name=value,
            )
        )

    figure.update_layout(
        title=(
            title
            or "Radar Chart"
        )
    )

    return figure


def waterfall_chart(
    dataframe,
    category,
    value,
    title=None,
):

    data = dataframe[
        [category, value]
    ].dropna()

    figure = go.Figure(
        go.Waterfall(
            x=data[
                category
            ],
            y=data[
                value
            ],
            measure=[
                "relative"
            ] * len(
                data
            ),
        )
    )

    figure.update_layout(
        title=(
            title
            or "Waterfall Chart"
        )
    )

    return figure


def funnel_chart(
    dataframe,
    category,
    value,
    title=None,
):

    return px.funnel(
        dataframe,
        y=category,
        x=value,
        title=(
            title
            or "Funnel Chart"
        ),
    )


def frequency_polygon(
    dataframe,
    x,
    bins=20,
    title=None,
):

    values = pd.to_numeric(
        dataframe[x],
        errors="coerce",
    ).dropna()

    frequencies, edges = np.histogram(
        values,
        bins=bins,
    )

    midpoints = (
        edges[:-1]
        + edges[1:]
    ) / 2

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=midpoints,
            y=frequencies,
            mode="lines+markers",
            name=x,
        )
    )

    figure.update_layout(
        title=(
            title
            or f"Frequency Polygon of {x}"
        ),
        xaxis_title=x,
        yaxis_title="Frequency",
    )

    return figure


def forest_plot(
    dataframe,
    estimate_column,
    label_column,
    lower_column,
    upper_column,
    title=None,
):

    data = dataframe[
        [
            estimate_column,
            label_column,
            lower_column,
            upper_column,
        ]
    ].dropna()

    estimate = data[
        estimate_column
    ]

    lower = data[
        lower_column
    ]

    upper = data[
        upper_column
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=estimate,
            y=data[
                label_column
            ],
            mode="markers",
            error_x=dict(
                type="data",
                symmetric=False,
                array=(
                    upper
                    - estimate
                ),
                arrayminus=(
                    estimate
                    - lower
                ),
            ),
        )
    )

    figure.add_vline(
        x=0,
        line_dash="dash",
    )

    figure.update_layout(
        title=(
            title
            or "Forest Plot"
        ),
        xaxis_title=estimate_column,
        yaxis_title=label_column,
    )

    return figure
