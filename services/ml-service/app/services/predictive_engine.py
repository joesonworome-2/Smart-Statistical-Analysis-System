import math

import numpy as np
import pandas as pd

from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import (
    KFold,
    TimeSeriesSplit,
    cross_val_score,
)
from sklearn.tree import DecisionTreeRegressor


# ==========================================================
# JSON SAFE
# ==========================================================

def json_safe(value):
    if value is None:
        return None

    if isinstance(value, (np.bool_, bool)):
        return bool(value)

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return None

        return number

    if isinstance(value, np.ndarray):
        return [
            json_safe(item)
            for item in value.tolist()
        ]

    if isinstance(value, dict):
        return {
            str(key): json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            json_safe(item)
            for item in value
        ]

    return value


# ==========================================================
# REGRESSION METRICS
# ==========================================================

def regression_metrics(
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

    rmse = math.sqrt(
        mean_squared_error(
            actual,
            predicted,
        )
    )

    mae = mean_absolute_error(
        actual,
        predicted,
    )

    r2 = r2_score(
        actual,
        predicted,
    )

    nonzero = (
        np.abs(actual)
        >
        1e-12
    )

    if np.any(nonzero):
        mape = float(
            np.mean(
                np.abs(
                    (
                        actual[nonzero]
                        -
                        predicted[nonzero]
                    )
                    /
                    actual[nonzero]
                )
            )
            *
            100
        )

    else:
        mape = None

    return {
        "R²":
            float(r2),

        "RMSE":
            float(rmse),

        "MAE":
            float(mae),

        "MAPE %":
            mape,
    }


# ==========================================================
# AVAILABLE MODELS
# ==========================================================

def build_models(
    random_seed,
):
    return {
        "Linear Regression":
            LinearRegression(),

        "Decision Tree":
            DecisionTreeRegressor(
                random_state=random_seed,
                min_samples_leaf=5,
            ),

        "Random Forest":
            RandomForestRegressor(
                n_estimators=250,
                random_state=random_seed,
                min_samples_leaf=2,
                n_jobs=-1,
            ),

        "Gradient Boosting":
            GradientBoostingRegressor(
                random_state=random_seed,
                n_estimators=150,
                learning_rate=0.05,
                max_depth=3,
            ),
    }


# ==========================================================
# TRAIN / TEST SPLIT
# ==========================================================

def split_data(
    dataframe,
    dependent_variable,
    predictors,
    test_size,
    random_seed,
    time_variable=None,
):
    required = [
        dependent_variable,
        *predictors,
    ]

    data = (
        dataframe
        .copy()
        .dropna(
            subset=required
        )
    )

    if len(data) < 30:
        raise ValueError(
            "At least 30 complete observations "
            "are required for automatic model comparison."
        )

    split_method = (
        "Random holdout"
    )

    # ------------------------------------------------------
    # CHRONOLOGICAL SPLIT
    # ------------------------------------------------------

    if (
        time_variable
        and
        time_variable
        in data.columns
    ):
        parsed_time = pd.to_datetime(
            data[
                time_variable
            ],
            errors="coerce",
        )

        valid_time = (
            parsed_time.notna()
        )

        if int(
            valid_time.sum()
        ) >= int(
            len(data)
            *
            0.75
        ):
            data = (
                data
                .loc[
                    valid_time
                ]
                .assign(
                    __time__=(
                        parsed_time.loc[
                            valid_time
                        ]
                    )
                )
                .sort_values(
                    "__time__"
                )
            )

            split_method = (
                "Chronological holdout"
            )

    # ------------------------------------------------------
    # BUILD X AND Y
    # ------------------------------------------------------

    X = (
        data[
            predictors
        ]
        .astype(float)
    )

    y = (
        data[
            dependent_variable
        ]
        .astype(float)
    )

    test_count = max(
        2,
        int(
            round(
                len(data)
                *
                test_size
            )
        ),
    )

    if test_count >= len(data):
        raise ValueError(
            "Test set is too large for the available data."
        )

    # ------------------------------------------------------
    # CHRONOLOGICAL HOLDOUT
    # ------------------------------------------------------

    if (
        split_method
        ==
        "Chronological holdout"
    ):
        X_train = (
            X.iloc[
                :-test_count
            ]
        )

        X_test = (
            X.iloc[
                -test_count:
            ]
        )

        y_train = (
            y.iloc[
                :-test_count
            ]
        )

        y_test = (
            y.iloc[
                -test_count:
            ]
        )

    # ------------------------------------------------------
    # RANDOM HOLDOUT
    # ------------------------------------------------------

    else:
        rng = (
            np.random.default_rng(
                random_seed
            )
        )

        indices = (
            rng.permutation(
                len(data)
            )
        )

        test_indices = (
            indices[
                :test_count
            ]
        )

        train_indices = (
            indices[
                test_count:
            ]
        )

        X_train = (
            X.iloc[
                train_indices
            ]
        )

        X_test = (
            X.iloc[
                test_indices
            ]
        )

        y_train = (
            y.iloc[
                train_indices
            ]
        )

        y_test = (
            y.iloc[
                test_indices
            ]
        )

    if len(X_train) < 20:
        raise ValueError(
            "The training sample is too small."
        )

    return {
        "X_train":
            X_train,

        "X_test":
            X_test,

        "y_train":
            y_train,

        "y_test":
            y_test,

        "split_method":
            split_method,

        "complete_cases":
            int(
                len(data)
            ),
    }


# ==========================================================
# CROSS-VALIDATION METHOD
# ==========================================================

def build_cv(
    split_method,
    cv_folds,
    n_train,
    random_seed,
):
    maximum_folds = max(
        3,
        min(
            10,
            n_train - 1,
        ),
    )

    folds = max(
        3,
        min(
            int(cv_folds),
            maximum_folds,
        ),
    )

    # Time-aware CV for future prediction
    if (
        split_method
        ==
        "Chronological holdout"
    ):
        return (
            TimeSeriesSplit(
                n_splits=folds
            ),
            folds,
        )

    return (
        KFold(
            n_splits=folds,
            shuffle=True,
            random_state=random_seed,
        ),
        folds,
    )


# ==========================================================
# MODEL COMPARISON
# ==========================================================

def compare_models(
    X_train,
    y_train,
    X_test,
    y_test,
    random_seed,
    cv_folds,
    split_method,
):
    models = build_models(
        random_seed
    )

    cv, actual_folds = (
        build_cv(
            split_method=(
                split_method
            ),
            cv_folds=(
                cv_folds
            ),
            n_train=(
                len(X_train)
            ),
            random_seed=(
                random_seed
            ),
        )
    )

    results = []

    fitted_models = {}

    for (
        model_name,
        model,
    ) in models.items():

        # --------------------------------------------------
        # CROSS-VALIDATION RMSE
        # --------------------------------------------------

        cv_rmse_scores = (
            -cross_val_score(
                model,
                X_train,
                y_train,
                cv=cv,
                scoring=(
                    "neg_root_mean_squared_error"
                ),
                n_jobs=(
                    -1
                    if model_name
                    ==
                    "Random Forest"
                    else None
                ),
            )
        )

        # --------------------------------------------------
        # CROSS-VALIDATION R²
        # --------------------------------------------------

        cv_r2_scores = (
            cross_val_score(
                model,
                X_train,
                y_train,
                cv=cv,
                scoring="r2",
                n_jobs=(
                    -1
                    if model_name
                    ==
                    "Random Forest"
                    else None
                ),
            )
        )

        # --------------------------------------------------
        # TRAIN MODEL
        # --------------------------------------------------

        model.fit(
            X_train,
            y_train,
        )

        train_prediction = (
            model.predict(
                X_train
            )
        )

        test_prediction = (
            model.predict(
                X_test
            )
        )

        train_metrics = (
            regression_metrics(
                y_train,
                train_prediction,
            )
        )

        test_metrics = (
            regression_metrics(
                y_test,
                test_prediction,
            )
        )

        fitted_models[
            model_name
        ] = model

        results.append({
            "Model":
                model_name,

            "CV RMSE":
                float(
                    np.mean(
                        cv_rmse_scores
                    )
                ),

            "CV R²":
                float(
                    np.mean(
                        cv_r2_scores
                    )
                ),

            "Train R²":
                train_metrics[
                    "R²"
                ],

            "Test R²":
                test_metrics[
                    "R²"
                ],

            "Test RMSE":
                test_metrics[
                    "RMSE"
                ],

            "Test MAE":
                test_metrics[
                    "MAE"
                ],

            "Test MAPE %":
                test_metrics[
                    "MAPE %"
                ],
        })

    # ------------------------------------------------------
    # SORT BEST → WORST
    # ------------------------------------------------------

    results.sort(
        key=lambda row:
            row[
                "CV RMSE"
            ]
    )

    best_row = (
        results[
            0
        ]
    )

    best_name = (
        best_row[
            "Model"
        ]
    )

    return {
        "comparison":
            results,

        "best_model_name":
            best_name,

        "best_model":
            fitted_models[
                best_name
            ],

        "best_metrics":
            best_row,

        "cv_folds":
            actual_folds,
    }


# ==========================================================
# FEATURE IMPORTANCE
# ==========================================================

def calculate_importance(
    model,
    X_test,
    y_test,
    predictor_names,
    random_seed,
):
    importance = (
        permutation_importance(
            model,
            X_test,
            y_test,
            scoring=(
                "neg_mean_squared_error"
            ),
            n_repeats=10,
            random_state=random_seed,
        )
    )

    values = (
        importance
        .importances_mean
    )

    absolute_sum = float(
        np.sum(
            np.abs(
                values
            )
        )
    )

    rows = []

    for (
        name,
        value,
    ) in zip(
        predictor_names,
        values,
    ):
        if absolute_sum > 0:
            relative = (
                abs(
                    float(
                        value
                    )
                )
                /
                absolute_sum
                *
                100
            )

        else:
            relative = 0.0

        rows.append({
            "Predictor":
                name,

            "Importance":
                float(
                    value
                ),

            "Relative Importance %":
                float(
                    relative
                ),
        })

    rows.sort(
        key=lambda row:
            row[
                "Relative Importance %"
            ],
        reverse=True,
    )

    return rows


# ==========================================================
# FUTURE SCENARIO
# ==========================================================

def prepare_future_scenario(
    X_train,
    predictors,
    future_values,
):
    values = {}

    for predictor in predictors:

        supplied = (
            future_values
            is not None
            and
            predictor
            in future_values
            and
            future_values[
                predictor
            ]
            is not None
        )

        if supplied:
            values[
                predictor
            ] = float(
                future_values[
                    predictor
                ]
            )

        else:
            values[
                predictor
            ] = float(
                X_train[
                    predictor
                ]
                .median()
            )

    scenario = pd.DataFrame(
        [
            values
        ],
        columns=predictors,
    )

    return (
        scenario,
        values,
    )


# ==========================================================
# SENSITIVITY ANALYSIS
# ==========================================================

def sensitivity_analysis(
    model,
    scenario,
    predictors,
):
    base_prediction = float(
        model.predict(
            scenario
        )[
            0
        ]
    )

    rows = []

    for predictor in predictors:

        original = float(
            scenario[
                predictor
            ]
            .iloc[
                0
            ]
        )

        amount = max(
            abs(
                original
            )
            *
            0.05,
            0.01,
        )

        increased = (
            scenario.copy()
        )

        decreased = (
            scenario.copy()
        )

        increased.loc[
            0,
            predictor
        ] = (
            original
            +
            amount
        )

        decreased.loc[
            0,
            predictor
        ] = (
            original
            -
            amount
        )

        increased_prediction = float(
            model.predict(
                increased
            )[
                0
            ]
        )

        decreased_prediction = float(
            model.predict(
                decreased
            )[
                0
            ]
        )

        rows.append({
            "Predictor":
                predictor,

            "Current Value":
                original,

            "+5% Scenario":
                float(
                    original
                    +
                    amount
                ),

            "Predicted Outcome (+5%)":
                increased_prediction,

            "Outcome Change (+5%)":
                (
                    increased_prediction
                    -
                    base_prediction
                ),

            "-5% Scenario":
                float(
                    original
                    -
                    amount
                ),

            "Predicted Outcome (-5%)":
                decreased_prediction,

            "Outcome Change (-5%)":
                (
                    decreased_prediction
                    -
                    base_prediction
                ),
        })

    return (
        base_prediction,
        rows,
    )


# ==========================================================
# RECOMMENDATION ENGINE
# ==========================================================

def build_recommendations(
    dependent_variable,
    future_prediction,
    historical_average,
    feature_importance,
    sensitivity_rows,
    best_model_name,
):
    recommendations = []

    # ------------------------------------------------------
    # PREDICTION VS HISTORICAL AVERAGE
    # ------------------------------------------------------

    if (
        abs(
            historical_average
        )
        >
        1e-12
    ):
        percent_difference = (
            (
                future_prediction
                -
                historical_average
            )
            /
            abs(
                historical_average
            )
            *
            100
        )

    else:
        percent_difference = None

    if (
        percent_difference
        is not None
    ):

        if (
            percent_difference
            >=
            10
        ):
            recommendations.append({
                "Priority":
                    "High",

                "Recommendation":
                    (
                        f"The predicted {dependent_variable} "
                        f"is approximately "
                        f"{abs(percent_difference):.1f}% "
                        f"above the historical average. "
                        f"Consider planning additional capacity, "
                        f"resources or inventory if higher values "
                        f"represent increased demand."
                    ),
            })

        elif (
            percent_difference
            <=
            -10
        ):
            recommendations.append({
                "Priority":
                    "High",

                "Recommendation":
                    (
                        f"The predicted {dependent_variable} "
                        f"is approximately "
                        f"{abs(percent_difference):.1f}% "
                        f"below the historical average. "
                        f"Consider reviewing demand, pricing, "
                        f"operations or other relevant drivers "
                        f"before committing resources."
                    ),
            })

        else:
            recommendations.append({
                "Priority":
                    "Normal",

                "Recommendation":
                    (
                        f"The predicted {dependent_variable} "
                        f"is relatively close to the historical "
                        f"average. Maintain current planning "
                        f"while continuing to monitor the "
                        f"main predictors."
                    ),
            })

    # ------------------------------------------------------
    # IMPORTANT FEATURES
    #
    # Only recommend monitoring predictors with at least
    # 1% relative permutation importance.
    # ------------------------------------------------------

    important_features = [
        item
        for item
        in feature_importance
        if float(
            item.get(
                "Relative Importance %",
                0,
            )
            or 0
        )
        >=
        1.0
    ]

    for item in (
        important_features[
            :3
        ]
    ):
        recommendations.append({
            "Priority":
                "Review",

            "Recommendation":
                (
                    f"{item['Predictor']} is one of the "
                    f"most influential variables in the "
                    f"selected {best_model_name} model "
                    f"({item['Relative Importance %']:.1f}% "
                    f"relative permutation importance). "
                    f"Consider monitoring this variable closely."
                ),
        })

    # ------------------------------------------------------
    # SENSITIVITY RECOMMENDATION
    #
    # Ignore predictors whose scenario produces no
    # meaningful model response.
    # ------------------------------------------------------

    meaningful_sensitivity = [
        row
        for row
        in sensitivity_rows
        if abs(
            float(
                row.get(
                    "Outcome Change (+5%)",
                    0,
                )
                or 0
            )
        )
        >
        1e-12
    ]

    if meaningful_sensitivity:

        strongest = max(
            meaningful_sensitivity,
            key=lambda row:
                abs(
                    float(
                        row[
                            "Outcome Change (+5%)"
                        ]
                    )
                ),
        )

        change = float(
            strongest[
                "Outcome Change (+5%)"
            ]
        )

        direction = (
            "increase"
            if change > 0
            else
            "decrease"
        )

        recommendations.append({
            "Priority":
                "Scenario",

            "Recommendation":
                (
                    f"In the current scenario, increasing "
                    f"{strongest['Predictor']} by about 5% "
                    f"changes the model prediction by "
                    f"{abs(change):.3f} units, producing "
                    f"a predicted {direction} in "
                    f"{dependent_variable}. Treat this as "
                    f"model sensitivity, not as evidence "
                    f"of causation."
                ),
        })

    return recommendations


# ==========================================================
# MAIN SMART PREDICTIVE ENGINE
# ==========================================================

def run_predictive_ml(
    dataframe,
    dependent_variable,
    predictors,
    test_size,
    random_seed,
    cv_folds,
    future_values=None,
    time_variable=None,
):
    # ------------------------------------------------------
    # BASIC VALIDATION
    # ------------------------------------------------------

    if (
        dependent_variable
        in predictors
    ):
        raise ValueError(
            "The dependent variable cannot also "
            "be used as a predictor."
        )

    required = [
        dependent_variable,
        *predictors,
    ]

    missing = [
        column
        for column
        in required
        if column
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
    # CONVERT PREDICTIVE COLUMNS TO NUMERIC
    # ------------------------------------------------------

    converted = (
        dataframe.copy()
    )

    for column in required:
        converted[
            column
        ] = pd.to_numeric(
            converted[
                column
            ],
            errors="coerce",
        )

    # ------------------------------------------------------
    # SPLIT DATA
    # ------------------------------------------------------

    split = split_data(
        dataframe=(
            converted
        ),

        dependent_variable=(
            dependent_variable
        ),

        predictors=(
            predictors
        ),

        test_size=(
            test_size
        ),

        random_seed=(
            random_seed
        ),

        time_variable=(
            time_variable
        ),
    )

    X_train = (
        split[
            "X_train"
        ]
    )

    X_test = (
        split[
            "X_test"
        ]
    )

    y_train = (
        split[
            "y_train"
        ]
    )

    y_test = (
        split[
            "y_test"
        ]
    )

    # ------------------------------------------------------
    # COMPARE ALL MODELS
    # ------------------------------------------------------

    comparison = (
        compare_models(
            X_train=(
                X_train
            ),

            y_train=(
                y_train
            ),

            X_test=(
                X_test
            ),

            y_test=(
                y_test
            ),

            random_seed=(
                random_seed
            ),

            cv_folds=(
                cv_folds
            ),

            split_method=(
                split[
                    "split_method"
                ]
            ),
        )
    )

    best_model = (
        comparison[
            "best_model"
        ]
    )

    best_model_name = (
        comparison[
            "best_model_name"
        ]
    )

    # ------------------------------------------------------
    # FINAL TEST PERFORMANCE
    # ------------------------------------------------------

    test_prediction = (
        best_model.predict(
            X_test
        )
    )

    test_metrics = (
        regression_metrics(
            y_test,
            test_prediction,
        )
    )

    # ------------------------------------------------------
    # FEATURE IMPORTANCE
    # ------------------------------------------------------

    importance = (
        calculate_importance(
            model=(
                best_model
            ),

            X_test=(
                X_test
            ),

            y_test=(
                y_test
            ),

            predictor_names=(
                predictors
            ),

            random_seed=(
                random_seed
            ),
        )
    )

    # ------------------------------------------------------
    # CREATE FUTURE SCENARIO
    # ------------------------------------------------------

    (
        scenario,
        scenario_values,
    ) = prepare_future_scenario(
        X_train=(
            X_train
        ),

        predictors=(
            predictors
        ),

        future_values=(
            future_values
        ),
    )

    # ------------------------------------------------------
    # FUTURE PREDICTION + SENSITIVITY
    # ------------------------------------------------------

    (
        future_prediction,
        sensitivity_rows,
    ) = sensitivity_analysis(
        model=(
            best_model
        ),

        scenario=(
            scenario
        ),

        predictors=(
            predictors
        ),
    )

    historical_average = float(
        y_train.mean()
    )

    # ------------------------------------------------------
    # RECOMMENDATIONS
    # ------------------------------------------------------

    recommendations = (
        build_recommendations(
            dependent_variable=(
                dependent_variable
            ),

            future_prediction=(
                future_prediction
            ),

            historical_average=(
                historical_average
            ),

            feature_importance=(
                importance
            ),

            sensitivity_rows=(
                sensitivity_rows
            ),

            best_model_name=(
                best_model_name
            ),
        )
    )

    # ------------------------------------------------------
    # HOLDOUT PREDICTIONS
    # ------------------------------------------------------

    prediction_rows = []

    actual_values = (
        y_test
        .to_numpy()
    )

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
            actual_values[
                index
            ]
        )

        predicted = float(
            test_prediction[
                index
            ]
        )

        prediction_rows.append({
            "Case":
                int(
                    index + 1
                ),

            "Actual":
                actual,

            "Predicted":
                predicted,

            "Residual":
                (
                    actual
                    -
                    predicted
                ),

            "Absolute Error":
                abs(
                    actual
                    -
                    predicted
                ),
        })

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return json_safe({
        "analysis_name":
            "Smart Predictive Analytics",

        "best_model":
            best_model_name,

        "model_selection_reason":
            (
                f"{best_model_name} was selected because "
                f"it produced the lowest average "
                f"cross-validation RMSE among the "
                f"candidate models."
            ),

        "split_method":
            split[
                "split_method"
            ],

        "cv_folds":
            comparison[
                "cv_folds"
            ],

        "complete_cases":
            split[
                "complete_cases"
            ],

        "training_cases":
            int(
                len(
                    X_train
                )
            ),

        "testing_cases":
            int(
                len(
                    X_test
                )
            ),

        "model_comparison":
            comparison[
                "comparison"
            ],

        "test_metrics":
            test_metrics,

        "feature_importance":
            importance,

        "future_scenario":
            scenario_values,

        "future_prediction":
            future_prediction,

        "historical_average":
            historical_average,

        "sensitivity_analysis":
            sensitivity_rows,

        "recommendations":
            recommendations,

        "holdout_predictions":
            prediction_rows,
    })
