import pandas as pd
import plotly.express as px


def histogram(
    dataframe: pd.DataFrame,
    x: str,
    bins: int = 20,
    group_by: str | None = None,
    title: str | None = None,
):

    if x not in dataframe.columns:
        raise ValueError(
            f"Column '{x}' was not found."
        )

    figure = px.histogram(
        dataframe,
        x=x,
        color=group_by,
        nbins=bins,
        title=(
            title
            or f"Distribution of {x}"
        ),
    )

    return figure


def density_plot(
    dataframe: pd.DataFrame,
    x: str,
    group_by: str | None = None,
    title: str | None = None,
):

    if x not in dataframe.columns:
        raise ValueError(
            f"Column '{x}' was not found."
        )

    figure = px.histogram(
        dataframe,
        x=x,
        color=group_by,
        histnorm="probability density",
        marginal="rug",
        title=(
            title
            or f"Density Distribution of {x}"
        ),
    )

    return figure


def box_plot(
    dataframe: pd.DataFrame,
    x: str | None,
    y: str,
    group_by: str | None = None,
    title: str | None = None,
):

    if y not in dataframe.columns:
        raise ValueError(
            f"Column '{y}' was not found."
        )

    figure = px.box(
        dataframe,
        x=x,
        y=y,
        color=group_by,
        points="all",
        title=(
            title
            or f"Box Plot of {y}"
        ),
    )

    return figure


def violin_plot(
    dataframe: pd.DataFrame,
    x: str | None,
    y: str,
    group_by: str | None = None,
    title: str | None = None,
):

    figure = px.violin(
        dataframe,
        x=x,
        y=y,
        color=group_by,
        box=True,
        points="all",
        title=(
            title
            or f"Violin Plot of {y}"
        ),
    )

    return figure


def ecdf_plot(
    dataframe: pd.DataFrame,
    x: str,
    group_by: str | None = None,
    title: str | None = None,
):

    figure = px.ecdf(
        dataframe,
        x=x,
        color=group_by,
        title=(
            title
            or f"ECDF of {x}"
        ),
    )

    return figure
