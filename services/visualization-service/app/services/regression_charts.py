import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from scipy import stats


def _prepare_regression(
    dataframe: pd.DataFrame,
    response_variable: str,
    predictor_variables: list[str],
):
    if not predictor_variables:
        raise ValueError(
            "At least one predictor variable is required."
        )

    variables = predictor_variables + [response_variable]

    missing = [
        variable
        for variable in variables
        if variable not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            f"Variables not found: {missing}"
        )

    data = dataframe[variables].copy()

    for column in variables:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    data = data.dropna()

    n = len(data)
    p = len(predictor_variables) + 1

    if n <= p:
        raise ValueError(
            "Not enough observations for regression visualization."
        )

    X = data[
        predictor_variables
    ].to_numpy(dtype=float)

    y = data[
        response_variable
    ].to_numpy(dtype=float)

    X_design = np.column_stack(
        [
            np.ones(n),
            X,
        ]
    )

    coefficients = np.linalg.lstsq(
        X_design,
        y,
        rcond=None,
    )[0]

    predicted = (
        X_design @ coefficients
    )

    residuals = (
        y - predicted
    )

    sse = np.sum(
        residuals ** 2
    )

    mse = (
        sse / (n - p)
    )

    residual_std = np.sqrt(
        mse
    )

    if residual_std == 0:
        standardized_residuals = np.zeros(n)
    else:
        standardized_residuals = (
            residuals
            / residual_std
        )

    xtx_inverse = np.linalg.pinv(
        X_design.T @ X_design
    )

    hat_matrix = (
        X_design
        @ xtx_inverse
        @ X_design.T
    )

    leverage = np.diag(
        hat_matrix
    )

    if mse == 0:
        cooks_distance = np.zeros(n)

    else:
        cooks_distance = (
            (
                residuals ** 2
            )
            / (
                p * mse
            )
        ) * (
            leverage
            / (
                1 - leverage
            ) ** 2
        )

    return {
        "data": data,
        "actual": y,
        "predicted": predicted,
        "residuals": residuals,
        "standardized_residuals": standardized_residuals,
        "leverage": leverage,
        "cooks_distance": cooks_distance,
    }


def regression_line_plot(
    dataframe,
    x,
    y,
    title=None,
):

    data = dataframe[
        [x, y]
    ].copy()

    data[x] = pd.to_numeric(
        data[x],
        errors="coerce",
    )

    data[y] = pd.to_numeric(
        data[y],
        errors="coerce",
    )

    data = data.dropna()

    if len(data) < 2:
        raise ValueError(
            "At least two observations are required."
        )

    coefficients = np.polyfit(
        data[x],
        data[y],
        1,
    )

    x_line = np.linspace(
        data[x].min(),
        data[x].max(),
        100,
    )

    y_line = (
        coefficients[0]
        * x_line
        + coefficients[1]
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=data[x],
            y=data[y],
            mode="markers",
            name="Observed",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            name="Regression Line",
        )
    )

    figure.update_layout(
        title=(
            title
            or f"{y} vs {x} Regression"
        ),
        xaxis_title=x,
        yaxis_title=y,
    )

    return figure


def actual_vs_predicted_plot(
    dataframe,
    response_variable,
    predictor_variables,
    title=None,
):

    result = _prepare_regression(
        dataframe,
        response_variable,
        predictor_variables,
    )

    actual = result["actual"]
    predicted = result["predicted"]

    minimum = min(
        actual.min(),
        predicted.min(),
    )

    maximum = max(
        actual.max(),
        predicted.max(),
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=actual,
            y=predicted,
            mode="markers",
            name="Observations",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=[
                minimum,
                maximum,
            ],
            y=[
                minimum,
                maximum,
            ],
            mode="lines",
            name="Perfect Prediction",
        )
    )

    figure.update_layout(
        title=(
            title
            or "Actual vs Predicted"
        ),
        xaxis_title="Actual",
        yaxis_title="Predicted",
    )

    return figure


def residual_vs_fitted_plot(
    dataframe,
    response_variable,
    predictor_variables,
    title=None,
):

    result = _prepare_regression(
        dataframe,
        response_variable,
        predictor_variables,
    )

    figure = px.scatter(
        x=result["predicted"],
        y=result["residuals"],
        labels={
            "x": "Fitted Values",
            "y": "Residuals",
        },
        title=(
            title
            or "Residuals vs Fitted Values"
        ),
    )

    figure.add_hline(
        y=0
    )

    return figure


def qq_plot(
    dataframe,
    response_variable,
    predictor_variables,
    title=None,
):

    result = _prepare_regression(
        dataframe,
        response_variable,
        predictor_variables,
    )

    residuals = result[
        "residuals"
    ]

    probability_result = stats.probplot(
        residuals,
        dist="norm",
        fit=True,
    )

    theoretical = (
        probability_result[0][0]
    )

    ordered = (
        probability_result[0][1]
    )

    slope = (
        probability_result[1][0]
    )

    intercept = (
        probability_result[1][1]
    )

    reference = (
        slope * theoretical
        + intercept
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=theoretical,
            y=ordered,
            mode="markers",
            name="Residuals",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=theoretical,
            y=reference,
            mode="lines",
            name="Normal Reference",
        )
    )

    figure.update_layout(
        title=(
            title
            or "Q-Q Plot of Regression Residuals"
        ),
        xaxis_title="Theoretical Quantiles",
        yaxis_title="Ordered Residuals",
    )

    return figure


def pp_plot(
    dataframe,
    response_variable,
    predictor_variables,
    title=None,
):

    result = _prepare_regression(
        dataframe,
        response_variable,
        predictor_variables,
    )

    residuals = result[
        "residuals"
    ]

    std = np.std(
        residuals,
        ddof=1,
    )

    if std == 0:
        standardized = np.zeros(
            len(residuals)
        )
    else:
        standardized = (
            residuals
            - np.mean(residuals)
        ) / std

    standardized = np.sort(
        standardized
    )

    n = len(
        standardized
    )

    observed_probability = (
        np.arange(
            1,
            n + 1,
        )
        - 0.5
    ) / n

    theoretical_probability = (
        stats.norm.cdf(
            standardized
        )
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=theoretical_probability,
            y=observed_probability,
            mode="markers",
            name="Observed",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Reference",
        )
    )

    figure.update_layout(
        title=(
            title
            or "P-P Plot"
        ),
        xaxis_title="Theoretical Probability",
        yaxis_title="Observed Probability",
    )

    return figure


def scale_location_plot(
    dataframe,
    response_variable,
    predictor_variables,
    title=None,
):

    result = _prepare_regression(
        dataframe,
        response_variable,
        predictor_variables,
    )

    values = np.sqrt(
        np.abs(
            result[
                "standardized_residuals"
            ]
        )
    )

    return px.scatter(
        x=result["predicted"],
        y=values,
        labels={
            "x": "Fitted Values",
            "y": "√|Standardized Residual|",
        },
        title=(
            title
            or "Scale-Location Plot"
        ),
    )


def standardized_residual_plot(
    dataframe,
    response_variable,
    predictor_variables,
    title=None,
):

    result = _prepare_regression(
        dataframe,
        response_variable,
        predictor_variables,
    )

    observations = np.arange(
        1,
        len(
            result[
                "standardized_residuals"
            ]
        ) + 1,
    )

    figure = px.scatter(
        x=observations,
        y=result[
            "standardized_residuals"
        ],
        labels={
            "x": "Observation",
            "y": "Standardized Residual",
        },
        title=(
            title
            or "Standardized Residual Plot"
        ),
    )

    figure.add_hline(
        y=0
    )

    figure.add_hline(
        y=2,
        line_dash="dash",
    )

    figure.add_hline(
        y=-2,
        line_dash="dash",
    )

    return figure


def leverage_plot(
    dataframe,
    response_variable,
    predictor_variables,
    title=None,
):

    result = _prepare_regression(
        dataframe,
        response_variable,
        predictor_variables,
    )

    return px.scatter(
        x=result["leverage"],
        y=result[
            "standardized_residuals"
        ],
        labels={
            "x": "Leverage",
            "y": "Standardized Residual",
        },
        title=(
            title
            or "Leverage Plot"
        ),
    )


def cooks_distance_plot(
    dataframe,
    response_variable,
    predictor_variables,
    title=None,
):

    result = _prepare_regression(
        dataframe,
        response_variable,
        predictor_variables,
    )

    observations = np.arange(
        1,
        len(
            result[
                "cooks_distance"
            ]
        ) + 1,
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=observations,
            y=result[
                "cooks_distance"
            ],
            name="Cook's Distance",
        )
    )

    figure.update_layout(
        title=(
            title
            or "Cook's Distance"
        ),
        xaxis_title="Observation",
        yaxis_title="Cook's Distance",
    )

    return figure
