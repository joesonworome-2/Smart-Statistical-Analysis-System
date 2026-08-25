import pandas as pd
import plotly.express as px


def missing_values_bar(
    dataframe: pd.DataFrame,
    title: str | None = None,
):

    missing = (
        dataframe
        .isna()
        .sum()
        .reset_index()
    )

    missing.columns = [
        "column",
        "missing_count",
    ]

    figure = px.bar(
        missing,
        x="column",
        y="missing_count",
        title=(
            title
            or "Missing Values by Column"
        ),
    )

    return figure


def missing_values_heatmap(
    dataframe: pd.DataFrame,
    title: str | None = None,
):

    missing_matrix = (
        dataframe.isna().astype(int)
    )

    figure = px.imshow(
        missing_matrix,
        aspect="auto",
        title=(
            title
            or "Missing Values Heatmap"
        ),
    )

    return figure
