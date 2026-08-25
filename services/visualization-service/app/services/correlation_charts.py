import pandas as pd
import plotly.express as px


def correlation_heatmap(
    dataframe: pd.DataFrame,
    columns: list[str] | None = None,
    title: str | None = None,
):

    if columns:

        numeric_data = dataframe[
            columns
        ].select_dtypes(
            include="number"
        )

    else:

        numeric_data = (
            dataframe.select_dtypes(
                include="number"
            )
        )

    if numeric_data.shape[1] < 2:
        raise ValueError(
            "At least two numeric columns "
            "are required."
        )

    correlation = (
        numeric_data.corr()
    )

    figure = px.imshow(
        correlation,
        text_auto=True,
        aspect="auto",
        title=(
            title
            or "Correlation Heatmap"
        ),
    )

    return figure
