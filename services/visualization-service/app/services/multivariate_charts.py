import pandas as pd
import plotly.express as px


def scatter_matrix(
    dataframe: pd.DataFrame,
    columns: list[str],
    group_by: str | None = None,
    title: str | None = None,
):

    return px.scatter_matrix(
        dataframe,
        dimensions=columns,
        color=group_by,
        title=(
            title
            or "Scatter Matrix"
        ),
    )


def parallel_coordinates(
    dataframe: pd.DataFrame,
    columns: list[str],
    title: str | None = None,
):

    numeric_data = dataframe[
        columns
    ].select_dtypes(
        include="number"
    )

    return px.parallel_coordinates(
        numeric_data,
        dimensions=list(
            numeric_data.columns
        ),
        title=title,
    )


def scatter_3d(
    dataframe: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    group_by: str | None = None,
    size: str | None = None,
    title: str | None = None,
):

    return px.scatter_3d(
        dataframe,
        x=x,
        y=y,
        z=z,
        color=group_by,
        size=size,
        title=title,
    )
