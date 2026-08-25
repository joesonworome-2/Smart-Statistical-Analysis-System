import pandas as pd
import plotly.express as px


def bar_chart(
    dataframe: pd.DataFrame,
    x: str,
    y: str | None = None,
    group_by: str | None = None,
    title: str | None = None,
    orientation: str = "vertical",
):

    if y is None:

        counts = (
            dataframe[x]
            .value_counts(
                dropna=False
            )
            .reset_index()
        )

        counts.columns = [
            x,
            "count",
        ]

        x_value = x
        y_value = "count"

    else:

        x_value = x
        y_value = y
        counts = dataframe

    if orientation == "horizontal":

        figure = px.bar(
            counts,
            x=y_value,
            y=x_value,
            color=group_by,
            orientation="h",
            title=title,
        )

    else:

        figure = px.bar(
            counts,
            x=x_value,
            y=y_value,
            color=group_by,
            title=title,
        )

    return figure


def grouped_bar_chart(
    dataframe: pd.DataFrame,
    x: str,
    y: str,
    group_by: str,
    title: str | None = None,
):

    return px.bar(
        dataframe,
        x=x,
        y=y,
        color=group_by,
        barmode="group",
        title=title,
    )


def stacked_bar_chart(
    dataframe: pd.DataFrame,
    x: str,
    y: str,
    group_by: str,
    title: str | None = None,
):

    return px.bar(
        dataframe,
        x=x,
        y=y,
        color=group_by,
        barmode="stack",
        title=title,
    )


def pie_chart(
    dataframe: pd.DataFrame,
    category: str,
    value: str | None = None,
    title: str | None = None,
):

    if value:

        figure = px.pie(
            dataframe,
            names=category,
            values=value,
            title=title,
        )

    else:

        counts = (
            dataframe[
                category
            ]
            .value_counts(
                dropna=False
            )
            .reset_index()
        )

        counts.columns = [
            category,
            "count",
        ]

        figure = px.pie(
            counts,
            names=category,
            values="count",
            title=title,
        )

    return figure


def donut_chart(
    dataframe: pd.DataFrame,
    category: str,
    value: str | None = None,
    title: str | None = None,
):

    figure = pie_chart(
        dataframe,
        category,
        value,
        title,
    )

    figure.update_traces(
        hole=0.45
    )

    return figure
