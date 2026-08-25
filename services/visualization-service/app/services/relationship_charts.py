import pandas as pd
import plotly.express as px


def scatter_plot(
    dataframe: pd.DataFrame,
    x: str,
    y: str,
    group_by: str | None = None,
    size: str | None = None,
    title: str | None = None,
):

    return px.scatter(
        dataframe,
        x=x,
        y=y,
        color=group_by,
        size=size,
        title=(
            title
            or f"{y} vs {x}"
        ),
    )


def bubble_chart(
    dataframe: pd.DataFrame,
    x: str,
    y: str,
    size: str,
    group_by: str | None = None,
    title: str | None = None,
):

    return px.scatter(
        dataframe,
        x=x,
        y=y,
        size=size,
        color=group_by,
        title=title,
    )


def line_chart(
    dataframe: pd.DataFrame,
    x: str,
    y: str,
    group_by: str | None = None,
    title: str | None = None,
):

    return px.line(
        dataframe,
        x=x,
        y=y,
        color=group_by,
        markers=True,
        title=title,
    )


def area_chart(
    dataframe: pd.DataFrame,
    x: str,
    y: str,
    group_by: str | None = None,
    title: str | None = None,
):

    return px.area(
        dataframe,
        x=x,
        y=y,
        color=group_by,
        title=title,
    )
