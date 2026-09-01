import math

import numpy as np
import pandas as pd

from scipy import stats

from app.services.regression_engine import (
    fit_ols,
    json_safe,
    numeric_series,
)


# ==========================================================
# DESIGN MATRIX
# ==========================================================

def design_matrix(
    X,
    include_intercept=True,
):
    X = np.asarray(
        X,
        dtype=float,
    )

    if X.ndim == 1:
        X = X.reshape(
            -1,
            1,
        )

    if include_intercept:
        return np.column_stack(
            [
                np.ones(
                    X.shape[0]
                ),
                X,
            ]
        )

    return X


# ==========================================================
# PREDICTION
# ==========================================================

def predict_values(
    X,
    coefficients,
    include_intercept=True,
):
    design = design_matrix(
        X,
        include_intercept,
    )

    return (
        design
        @
        np.asarray(
            coefficients,
            dtype=float,
        )
    )


# ==========================================================
# ACCURACY METRICS
# ==========================================================

def calculate_metrics(
    actual,
    predicted,
):
    actual = np.asarray(
        actual,
        dtype=float,
    )

    predicted = np.asarray(
        predicted,
        dtype=float,
    )

    residuals = (
        actual
        -
        predicted
    )

    mae = float(
        np.mean(
            np.abs(
                residuals
            )
        )
    )

    mse = float(
        np.mean(
            residuals ** 2
        )
    )

    rmse = float(
        math.sqrt(
            mse
        )
    )

    ss_residual = float(
        np.sum(
            residuals ** 2
        )
    )

    ss_total = float(
        np.sum(
            (
                actual
                -
                np.mean(
                    actual
                )
            )
            ** 2
        )
    )

    if ss_total > 0:
        r_squared = float(
            1
            -
            ss_residual
            /
            ss_total
        )
    else:
        r_squared = None

    nonzero = (
        np.abs(
            actual
        )
        >
        1e-12
    )

    if np.any(
        nonzero
    ):
        mape = float(
            np.mean(
                np.abs(
                    (
                        actual[
                            nonzero
                        ]
                        -
                        predicted[
                            nonzero
                        ]
                    )
                    /
                    actual[
                        nonzero
                    ]
                )
            )
            *
            100
        )
    else:
        mape = None

    return {
        "R²":
            r_squared,

        "RMSE":
            rmse,

        "MAE":
            mae,

        "MAPE %":
            mape,

        "Residual Mean":
            float(
                np.mean(
                    residuals
                )
            ),
    }


# ==========================================================
# COEFFICIENT TABLE
# ==========================================================

def build_coefficient_rows(
    model,
    predictors,
    confidence_level,
    include_intercept,
):
    beta = (
        model[
            "beta"
        ]
    )

    standard_errors = (
        model[
            "standard_errors"
        ]
    )

    t_statistics = (
        model[
            "t_statistics"
        ]
    )

    p_values = (
        model[
            "p_values"
        ]
    )

    df_residual = (
        model[
            "df_residual"
        ]
    )

    critical = stats.t.ppf(
        1
        -
        (
            1
            -
            confidence_level
        )
        /
        2,
        df_residual,
    )

    if include_intercept:
        names = [
            "Intercept",
            *predictors,
        ]
    else:
        names = [
            *predictors
        ]

    rows = []

    for index, name in enumerate(
        names
    ):
        coefficient = float(
            beta[
                index
            ]
        )

        standard_error = float(
            standard_errors[
                index
            ]
        )

        t_value = float(
            t_statistics[
                index
            ]
        )

        p_value = float(
            p_values[
                index
            ]
        )

        lower = (
            coefficient
            -
            critical
            *
            standard_error
        )

        upper = (
            coefficient
            +
            critical
            *
            standard_error
        )

        rows.append({
            "Predictor":
                name,

            "B":
                coefficient,

            "Std. Error":
                standard_error,

            "t":
                t_value,

            "p-value":
                p_value,

            "CI Lower":
                float(
                    lower
                ),

            "CI Upper":
                float(
                    upper
                ),
        })

    return rows


# ==========================================================
# GENERALIZATION ASSESSMENT
# ==========================================================

def generalization_status(
    train_r2,
    test_r2,
):
    if test_r2 is None:
        return (
            "Test R² could not be evaluated."
        )

    if test_r2 < 0:
        return (
            "Poor generalization: the model performs "
            "worse than the mean-based baseline on "
            "the holdout data."
        )

    if train_r2 is None:
        return (
            "Generalization should be reviewed."
        )

    gap = (
        train_r2
        -
        test_r2
    )

    if gap >= 0.20:
        return (
            "Possible overfitting: training performance "
            "is substantially better than testing performance."
        )

    if gap >= 0.10:
        return (
            "Moderate difference between training "
            "and testing performance."
        )

    return (
        "Training and testing performance "
        "are reasonably consistent."
    )


# ==========================================================
# MAIN PREDICTIVE ANALYSIS
# ==========================================================

def run_predictive_analysis(
    dataframe,
    dependent_variable,
    predictors,
    test_size,
    random_seed,
    confidence_level,
    include_intercept=True,
):
    # ------------------------------------------------------
    # VARIABLE VALIDATION
    # ------------------------------------------------------

    if (
        dependent_variable
        in predictors
    ):
        raise ValueError(
            "The dependent variable cannot "
            "also be a predictor."
        )

    required = [
        dependent_variable,
        *predictors,
    ]

    missing = [
        variable
        for variable in required
        if variable
        not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            (
                "Dataset does not contain: "
                +
                ", ".join(
                    missing
                )
            )
        )

    # ------------------------------------------------------
    # CONVERT VARIABLES
    # ------------------------------------------------------

    converted = {}

    for variable in required:
        values = numeric_series(
            dataframe[
                variable
            ]
        )

        usable = int(
            values.notna().sum()
        )

        if usable < 10:
            raise ValueError(
                (
                    f"{variable} does not contain "
                    f"enough usable numeric/date values."
                )
            )

        converted[
            variable
        ] = values

    analysis_data = (
        pd.DataFrame(
            converted
        )
        .dropna()
        .copy()
    )

    # Keep original case position
    analysis_data[
        "__case__"
    ] = analysis_data.index

    analysis_data = (
        analysis_data
        .reset_index(
            drop=True
        )
    )

    sample_size = int(
        len(
            analysis_data
        )
    )

    if sample_size < 20:
        raise ValueError(
            "At least 20 complete observations "
            "are required for predictive analysis."
        )

    # ------------------------------------------------------
    # CONSTANT VARIABLE CHECKS
    # ------------------------------------------------------

    if (
        analysis_data[
            dependent_variable
        ].nunique()
        <
        2
    ):
        raise ValueError(
            "The dependent variable is constant."
        )

    constant_predictors = [
        predictor
        for predictor in predictors
        if (
            analysis_data[
                predictor
            ].nunique()
            <
            2
        )
    ]

    if constant_predictors:
        raise ValueError(
            (
                "Constant predictors cannot be used: "
                +
                ", ".join(
                    constant_predictors
                )
            )
        )

    # ------------------------------------------------------
    # ARRAYS
    # ------------------------------------------------------

    y = (
        analysis_data[
            dependent_variable
        ]
        .to_numpy(
            dtype=float
        )
    )

    X = (
        analysis_data[
            predictors
        ]
        .to_numpy(
            dtype=float
        )
    )

    case_ids = (
        analysis_data[
            "__case__"
        ]
        .to_numpy()
    )

    # ------------------------------------------------------
    # TRAIN / TEST SPLIT
    # ------------------------------------------------------

    random_generator = (
        np.random.default_rng(
            random_seed
        )
    )

    shuffled_indices = (
        random_generator.permutation(
            sample_size
        )
    )

    test_count = int(
        round(
            sample_size
            *
            test_size
        )
    )

    test_count = max(
        2,
        test_count,
    )

    train_count = (
        sample_size
        -
        test_count
    )

    minimum_train = (
        len(
            predictors
        )
        +
        5
    )

    if train_count <= minimum_train:
        raise ValueError(
            "Training sample is too small "
            "for the selected predictors."
        )

    test_indices = (
        shuffled_indices[
            :test_count
        ]
    )

    train_indices = (
        shuffled_indices[
            test_count:
        ]
    )

    X_train = (
        X[
            train_indices
        ]
    )

    y_train = (
        y[
            train_indices
        ]
    )

    X_test = (
        X[
            test_indices
        ]
    )

    y_test = (
        y[
            test_indices
        ]
    )

    test_cases = (
        case_ids[
            test_indices
        ]
    )

    # ------------------------------------------------------
    # FIT MODEL
    # ------------------------------------------------------

    model = fit_ols(
        y_train,
        X_train,
        include_intercept=(
            include_intercept
        ),
    )

    # ------------------------------------------------------
    # GENERATE PREDICTIONS
    # ------------------------------------------------------

    train_predictions = (
        predict_values(
            X_train,
            model[
                "beta"
            ],
            include_intercept,
        )
    )

    test_predictions = (
        predict_values(
            X_test,
            model[
                "beta"
            ],
            include_intercept,
        )
    )

    # ------------------------------------------------------
    # TRAINING / TEST METRICS
    # ------------------------------------------------------

    train_metrics = (
        calculate_metrics(
            y_train,
            train_predictions,
        )
    )

    test_metrics = (
        calculate_metrics(
            y_test,
            test_predictions,
        )
    )

    # ------------------------------------------------------
    # BASELINE
    # ------------------------------------------------------

    baseline_prediction = float(
        np.mean(
            y_train
        )
    )

    baseline_values = np.full(
        len(
            y_test
        ),
        baseline_prediction,
        dtype=float,
    )

    baseline_metrics = (
        calculate_metrics(
            y_test,
            baseline_values,
        )
    )

    if (
        baseline_metrics[
            "RMSE"
        ]
        >
        0
    ):
        rmse_improvement = float(
            (
                baseline_metrics[
                    "RMSE"
                ]
                -
                test_metrics[
                    "RMSE"
                ]
            )
            /
            baseline_metrics[
                "RMSE"
            ]
            *
            100
        )

    else:
        rmse_improvement = None

    # ------------------------------------------------------
    # COEFFICIENTS
    # ------------------------------------------------------

    coefficient_rows = (
        build_coefficient_rows(
            model,
            predictors,
            confidence_level,
            include_intercept,
        )
    )

    # ------------------------------------------------------
    # TEST PREDICTION TABLE
    # ------------------------------------------------------

    prediction_rows = []

    maximum_rows = min(
        100,
        len(
            y_test
        ),
    )

    for index in range(
        maximum_rows
    ):
        actual = float(
            y_test[
                index
            ]
        )

        predicted = float(
            test_predictions[
                index
            ]
        )

        residual = (
            actual
            -
            predicted
        )

        case_value = (
            test_cases[
                index
            ]
        )

        if isinstance(
            case_value,
            np.integer,
        ):
            case_value = int(
                case_value
            )

        prediction_rows.append({
            "Case":
                case_value,

            "Actual":
                actual,

            "Predicted":
                predicted,

            "Residual":
                float(
                    residual
                ),

            "Absolute Error":
                float(
                    abs(
                        residual
                    )
                ),
        })

    # ------------------------------------------------------
    # GENERALIZATION
    # ------------------------------------------------------

    status = (
        generalization_status(
            train_metrics[
                "R²"
            ],
            test_metrics[
                "R²"
            ],
        )
    )

    # ------------------------------------------------------
    # SPLIT TABLE
    # ------------------------------------------------------

    split_rows = [
        {
            "Complete Cases":
                sample_size,

            "Training Cases":
                int(
                    train_count
                ),

            "Testing Cases":
                int(
                    test_count
                ),

            "Test %":
                float(
                    test_size
                    *
                    100
                ),

            "Random Seed":
                int(
                    random_seed
                ),
        }
    ]

    # ------------------------------------------------------
    # ACCURACY TABLE
    # ------------------------------------------------------

    accuracy_rows = [
        {
            "Dataset":
                "Training",

            **train_metrics,
        },

        {
            "Dataset":
                "Testing",

            **test_metrics,
        },

        {
            "Dataset":
                "Baseline",

            **baseline_metrics,
        },
    ]

    # ------------------------------------------------------
    # PERFORMANCE SUMMARY
    # ------------------------------------------------------

    comparison_rows = [
        {
            "Metric":
                "Test R²",

            "Value":
                test_metrics[
                    "R²"
                ],

            "Interpretation":
                (
                    "Explained variance on "
                    "unseen holdout data."
                ),
        },

        {
            "Metric":
                "Test RMSE",

            "Value":
                test_metrics[
                    "RMSE"
                ],

            "Interpretation":
                (
                    "Typical prediction error "
                    "in outcome units."
                ),
        },

        {
            "Metric":
                "Test MAE",

            "Value":
                test_metrics[
                    "MAE"
                ],

            "Interpretation":
                (
                    "Average absolute "
                    "prediction error."
                ),
        },

        {
            "Metric":
                "RMSE Improvement vs Baseline (%)",

            "Value":
                rmse_improvement,

            "Interpretation":
                (
                    "Positive values mean the model "
                    "performed better than the baseline."
                ),
        },

        {
            "Metric":
                "Generalization",

            "Value":
                None,

            "Interpretation":
                status,
        },
    ]

    # ------------------------------------------------------
    # INTERPRETATION
    # ------------------------------------------------------

    test_r2 = (
        test_metrics[
            "R²"
        ]
    )

    if test_r2 is None:
        r2_text = (
            "Test R² could not be calculated."
        )

    elif test_r2 >= 0:
        r2_text = (
            f"The model explains approximately "
            f"{test_r2 * 100:.2f}% of variation "
            f"in unseen {dependent_variable} values."
        )

    else:
        r2_text = (
            "The test R² is negative. "
            "The predictive model performed worse "
            "than a mean-based baseline on the "
            "holdout observations."
        )

    interpretation = (
        f"{r2_text} "
        f"The holdout RMSE is "
        f"{test_metrics['RMSE']:.4f}, "
        f"and the holdout MAE is "
        f"{test_metrics['MAE']:.4f}. "
        f"{status} "
        "Predictive performance should be judged "
        "using unseen data rather than training "
        "accuracy alone."
    )

    # ------------------------------------------------------
    # APA SUMMARY
    # ------------------------------------------------------

    if test_r2 is not None:
        r2_apa = (
            f"R² = {test_r2:.3f}"
        )
    else:
        r2_apa = (
            "R² unavailable"
        )

    apa = (
        f"An OLS predictive model was trained "
        f"to predict {dependent_variable} from "
        f"{', '.join(predictors)}. "
        f"The model was trained on "
        f"{train_count} observations and "
        f"evaluated on {test_count} held-out "
        f"observations. On the test set, "
        f"{r2_apa}, "
        f"RMSE = {test_metrics['RMSE']:.3f}, "
        f"and MAE = {test_metrics['MAE']:.3f}."
    )

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return json_safe({
        "analysis_name":
            "Predictive Analytics",

        "model_name":
            (
                "Simple Linear Prediction"
                if len(
                    predictors
                )
                ==
                1
                else
                "Multiple Linear Prediction"
            ),

        "configuration": {
            "dependent_variable":
                dependent_variable,

            "predictors":
                predictors,

            "test_size":
                test_size,

            "random_seed":
                random_seed,

            "confidence_level":
                confidence_level,

            "include_intercept":
                include_intercept,
        },

        "metrics": {
            "training":
                train_metrics,

            "testing":
                test_metrics,

            "baseline":
                baseline_metrics,

            "rmse_improvement_percent":
                rmse_improvement,

            "generalization_status":
                status,
        },

        "tables": [
            {
                "title":
                    "Training and Testing Split",

                "columns": [
                    "Complete Cases",
                    "Training Cases",
                    "Testing Cases",
                    "Test %",
                    "Random Seed",
                ],

                "rows":
                    split_rows,
            },

            {
                "title":
                    "Prediction Accuracy",

                "columns": [
                    "Dataset",
                    "R²",
                    "RMSE",
                    "MAE",
                    "MAPE %",
                    "Residual Mean",
                ],

                "rows":
                    accuracy_rows,
            },

            {
                "title":
                    "Model Coefficients",

                "columns": [
                    "Predictor",
                    "B",
                    "Std. Error",
                    "t",
                    "p-value",
                    "CI Lower",
                    "CI Upper",
                ],

                "rows":
                    coefficient_rows,
            },

            {
                "title":
                    "Predictive Performance Summary",

                "columns": [
                    "Metric",
                    "Value",
                    "Interpretation",
                ],

                "rows":
                    comparison_rows,
            },

            {
                "title":
                    "Holdout Predictions",

                "columns": [
                    "Case",
                    "Actual",
                    "Predicted",
                    "Residual",
                    "Absolute Error",
                ],

                "rows":
                    prediction_rows,
            },
        ],

        "interpretation":
            interpretation,

        "apa":
            apa,
    })
