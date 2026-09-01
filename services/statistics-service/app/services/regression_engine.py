import math

import numpy as np
import pandas as pd

from scipy import stats


# ==========================================================
# JSON SAFE
# ==========================================================

def json_safe(value):
    if value is None:
        return None

    if isinstance(
        value,
        (
            np.bool_,
            bool,
        ),
    ):
        return bool(value)

    if isinstance(
        value,
        np.integer,
    ):
        return int(value)

    if isinstance(
        value,
        np.floating,
    ):
        value = float(
            value
        )

        if (
            math.isnan(value)
            or
            math.isinf(value)
        ):
            return None

        return value

    if isinstance(
        value,
        np.ndarray,
    ):
        return [
            json_safe(item)
            for item
            in value.tolist()
        ]

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key):
                json_safe(item)
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            json_safe(item)
            for item in value
        ]

    return value


# ==========================================================
# NUMERIC SERIES
# ==========================================================

def numeric_series(
    series,
):
    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    existing = int(
        series.notna().sum()
    )

    valid = int(
        numeric.notna().sum()
    )

    if (
        existing > 0
        and
        valid / existing >= 0.75
    ):
        return numeric.astype(
            float
        )

    dates = pd.to_datetime(
        series,
        errors="coerce",
    )

    date_valid = int(
        dates.notna().sum()
    )

    if (
        existing > 0
        and
        date_valid / existing >= 0.75
    ):
        converted = pd.Series(
            np.nan,
            index=series.index,
            dtype=float,
        )

        mask = dates.notna()

        converted.loc[
            mask
        ] = (
            dates.loc[
                mask
            ].astype(
                "int64"
            )
            /
            86_400_000_000_000
        )

        return converted

    return pd.Series(
        np.nan,
        index=series.index,
        dtype=float,
    )


# ==========================================================
# SHAPIRO
# ==========================================================

def shapiro_result(
    values,
):
    values = pd.Series(
        values
    ).dropna()

    if len(values) < 3:
        return {
            "statistic": None,
            "p_value": None,
        }

    sample = values

    if len(sample) > 5000:
        sample = sample.sample(
            5000,
            random_state=42,
        )

    statistic, p_value = (
        stats.shapiro(
            sample
        )
    )

    return {
        "statistic":
            float(
                statistic
            ),

        "p_value":
            float(
                p_value
            ),
    }


# ==========================================================
# OLS FIT
# ==========================================================

def fit_ols(
    y,
    X,
    include_intercept=True,
):
    y = np.asarray(
        y,
        dtype=float,
    )

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
        design = np.column_stack(
            [
                np.ones(
                    len(y)
                ),
                X,
            ]
        )
    else:
        design = X


    # ------------------------------------------------------
    # BETA
    # ------------------------------------------------------

    xtx_inverse = (
        np.linalg.pinv(
            design.T @ design
        )
    )

    beta = (
        xtx_inverse
        @ design.T
        @ y
    )

    fitted = (
        design @ beta
    )

    residuals = (
        y - fitted
    )


    n = len(y)

    number_parameters = (
        design.shape[1]
    )

    df_residual = (
        n
        -
        number_parameters
    )

    if df_residual <= 0:
        raise ValueError(
            "Not enough observations for the selected predictors."
        )


    # ------------------------------------------------------
    # SUMS OF SQUARES
    # ------------------------------------------------------

    if include_intercept:
        y_reference = (
            np.mean(y)
        )
    else:
        y_reference = 0.0


    ss_total = float(
        np.sum(
            (
                y
                -
                y_reference
            )
            ** 2
        )
    )

    ss_residual = float(
        np.sum(
            residuals ** 2
        )
    )

    ss_regression = (
        ss_total
        -
        ss_residual
    )


    if ss_total > 0:
        r_squared = (
            1
            -
            ss_residual
            /
            ss_total
        )
    else:
        r_squared = 0.0


    predictor_count = (
        X.shape[1]
    )


    adjusted_r_squared = (
        1
        -
        (
            1
            -
            r_squared
        )
        *
        (
            n - 1
        )
        /
        (
            n
            -
            predictor_count
            -
            1
        )
        if (
            n
            >
            predictor_count
            +
            1
        )
        else None
    )


    mse = (
        ss_residual
        /
        df_residual
    )

    rmse = math.sqrt(
        mse
    )


    covariance = (
        mse
        *
        xtx_inverse
    )

    standard_errors = (
        np.sqrt(
            np.diag(
                covariance
            )
        )
    )

    t_statistics = (
        beta
        /
        standard_errors
    )

    p_values = (
        2
        *
        (
            1
            -
            stats.t.cdf(
                np.abs(
                    t_statistics
                ),
                df=df_residual,
            )
        )
    )


    return {
        "beta":
            beta,

        "standard_errors":
            standard_errors,

        "t_statistics":
            t_statistics,

        "p_values":
            p_values,

        "fitted":
            fitted,

        "residuals":
            residuals,

        "n":
            n,

        "predictor_count":
            predictor_count,

        "df_residual":
            df_residual,

        "ss_total":
            ss_total,

        "ss_regression":
            ss_regression,

        "ss_residual":
            ss_residual,

        "r_squared":
            float(
                r_squared
            ),

        "adjusted_r_squared":
            (
                float(
                    adjusted_r_squared
                )
                if adjusted_r_squared
                is not None
                else None
            ),

        "mse":
            float(
                mse
            ),

        "rmse":
            float(
                rmse
            ),
    }


# ==========================================================
# VIF
# ==========================================================

def calculate_vif(
    X,
    predictor_names,
):
    X = np.asarray(
        X,
        dtype=float,
    )

    rows = []


    if X.shape[1] == 1:
        return [
            {
                "Predictor":
                    predictor_names[
                        0
                    ],

                "VIF":
                    1.0,

                "Tolerance":
                    1.0,

                "Status":
                    "No multicollinearity",
            }
        ]


    for index, name in enumerate(
        predictor_names
    ):
        target = (
            X[
                :,
                index
            ]
        )

        others = (
            np.delete(
                X,
                index,
                axis=1,
            )
        )


        model = fit_ols(
            target,
            others,
            include_intercept=True,
        )


        r_squared = (
            model[
                "r_squared"
            ]
        )


        tolerance = max(
            1
            -
            r_squared,
            0.0,
        )


        if tolerance <= 1e-12:
            vif = None
            status = (
                "Severe multicollinearity"
            )

        else:
            vif = (
                1
                /
                tolerance
            )

            if vif >= 10:
                status = (
                    "Severe multicollinearity"
                )

            elif vif >= 5:
                status = (
                    "Potential multicollinearity"
                )

            else:
                status = (
                    "Acceptable"
                )


        rows.append({
            "Predictor":
                name,

            "VIF":
                (
                    float(vif)
                    if vif
                    is not None
                    else None
                ),

            "Tolerance":
                float(
                    tolerance
                ),

            "Status":
                status,
        })


    return rows


# ==========================================================
# DURBIN-WATSON
# ==========================================================

def durbin_watson(
    residuals,
):
    residuals = (
        np.asarray(
            residuals,
            dtype=float,
        )
    )

    denominator = (
        np.sum(
            residuals ** 2
        )
    )

    if denominator == 0:
        return None

    numerator = (
        np.sum(
            np.diff(
                residuals
            )
            ** 2
        )
    )

    return float(
        numerator
        /
        denominator
    )


# ==========================================================
# BREUSCH-PAGAN
# ==========================================================

def breusch_pagan(
    residuals,
    X,
):
    residuals = np.asarray(
        residuals,
        dtype=float,
    )

    squared = (
        residuals ** 2
    )


    auxiliary = fit_ols(
        squared,
        X,
        include_intercept=True,
    )


    sample_size = (
        len(
            residuals
        )
    )

    lm_statistic = (
        sample_size
        *
        auxiliary[
            "r_squared"
        ]
    )


    df = (
        np.asarray(
            X
        ).shape[
            1
        ]
    )


    p_value = (
        1
        -
        stats.chi2.cdf(
            lm_statistic,
            df,
        )
    )


    return {
        "statistic":
            float(
                lm_statistic
            ),

        "df":
            int(
                df
            ),

        "p_value":
            float(
                p_value
            ),
    }


# ==========================================================
# MAIN REGRESSION
# ==========================================================

def run_regression_analysis(
    dataframe,
    dependent_variable,
    predictors,
    alpha,
    confidence_level,
    include_intercept=True,
):
    if (
        dependent_variable
        in predictors
    ):
        raise ValueError(
            "The dependent variable cannot also be used as a predictor."
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


    converted = {}


    for variable in required:
        values = numeric_series(
            dataframe[
                variable
            ]
        )

        usable = int(
            values
            .notna()
            .sum()
        )

        if usable < 3:
            raise ValueError(
                (
                    f"{variable} does not contain enough "
                    f"numeric or date values for regression."
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
    )


    if len(
        analysis_data
    ) <= len(
        predictors
    ) + 2:
        raise ValueError(
            "Not enough complete observations for this regression model."
        )


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


    # ------------------------------------------------------
    # CONSTANT PREDICTOR CHECK
    # ------------------------------------------------------

    constant_predictors = [
        predictor
        for predictor
        in predictors
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
    # MODEL
    # ------------------------------------------------------

    model = fit_ols(
        y,
        X,
        include_intercept=(
            include_intercept
        ),
    )


    n = (
        model[
            "n"
        ]
    )

    predictor_count = (
        model[
            "predictor_count"
        ]
    )


    # ------------------------------------------------------
    # MODEL F TEST
    # ------------------------------------------------------

    df_regression = (
        predictor_count
    )

    df_residual = (
        model[
            "df_residual"
        ]
    )


    ms_regression = (
        model[
            "ss_regression"
        ]
        /
        df_regression
    )


    ms_residual = (
        model[
            "ss_residual"
        ]
        /
        df_residual
    )


    if ms_residual > 0:
        f_statistic = (
            ms_regression
            /
            ms_residual
        )

        model_p_value = (
            1
            -
            stats.f.cdf(
                f_statistic,
                df_regression,
                df_residual,
            )
        )

    else:
        f_statistic = None
        model_p_value = None


    # ------------------------------------------------------
    # COEFFICIENT CI
    # ------------------------------------------------------

    critical = (
        stats.t.ppf(
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
    )


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


    if include_intercept:
        names = [
            "Intercept",
            *predictors,
        ]
    else:
        names = [
            *predictors
        ]


    dependent_sd = float(
        np.std(
            y,
            ddof=1,
        )
    )


    coefficient_rows = []


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


        standardized_beta = None


        if name != "Intercept":
            predictor_sd = float(
                np.std(
                    analysis_data[
                        name
                    ],
                    ddof=1,
                )
            )

            if dependent_sd > 0:
                standardized_beta = (
                    coefficient
                    *
                    predictor_sd
                    /
                    dependent_sd
                )


        coefficient_rows.append({
            "Predictor":
                name,

            "B":
                coefficient,

            "Std. Error":
                standard_error,

            "Standardized Beta":
                (
                    float(
                        standardized_beta
                    )
                    if standardized_beta
                    is not None
                    else None
                ),

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

            "Significant":
                (
                    "Yes"
                    if p_value
                    < alpha
                    else "No"
                ),
        })


    # ------------------------------------------------------
    # RESIDUAL DIAGNOSTICS
    # ------------------------------------------------------

    residuals = (
        model[
            "residuals"
        ]
    )


    shapiro = (
        shapiro_result(
            residuals
        )
    )


    dw = (
        durbin_watson(
            residuals
        )
    )


    bp = (
        breusch_pagan(
            residuals,
            X,
        )
    )


    residual_sd = float(
        np.std(
            residuals,
            ddof=1,
        )
    )


    if residual_sd > 0:
        standardized_residuals = (
            residuals
            /
            residual_sd
        )

        extreme_residuals = int(
            np.sum(
                np.abs(
                    standardized_residuals
                )
                >
                3
            )
        )

    else:
        extreme_residuals = 0


    vif_rows = (
        calculate_vif(
            X,
            predictors,
        )
    )


    # ------------------------------------------------------
    # TABLES
    # ------------------------------------------------------

    model_summary_rows = [
        {
            "n":
                int(
                    n
                ),

            "Predictors":
                int(
                    predictor_count
                ),

            "R²":
                float(
                    model[
                        "r_squared"
                    ]
                ),

            "Adjusted R²":
                model[
                    "adjusted_r_squared"
                ],

            "RMSE":
                float(
                    model[
                        "rmse"
                    ]
                ),
        }
    ]


    anova_rows = [
        {
            "Source":
                "Regression",

            "Sum of Squares":
                float(
                    model[
                        "ss_regression"
                    ]
                ),

            "df":
                int(
                    df_regression
                ),

            "Mean Square":
                float(
                    ms_regression
                ),

            "F":
                (
                    float(
                        f_statistic
                    )
                    if f_statistic
                    is not None
                    else None
                ),

            "p-value":
                (
                    float(
                        model_p_value
                    )
                    if model_p_value
                    is not None
                    else None
                ),
        },

        {
            "Source":
                "Residual",

            "Sum of Squares":
                float(
                    model[
                        "ss_residual"
                    ]
                ),

            "df":
                int(
                    df_residual
                ),

            "Mean Square":
                float(
                    ms_residual
                ),

            "F":
                None,

            "p-value":
                None,
        },

        {
            "Source":
                "Total",

            "Sum of Squares":
                float(
                    model[
                        "ss_total"
                    ]
                ),

            "df":
                int(
                    n - 1
                ),

            "Mean Square":
                None,

            "F":
                None,

            "p-value":
                None,
        },
    ]


    diagnostics_rows = [
        {
            "Diagnostic":
                "Residual Normality",

            "Statistic":
                shapiro[
                    "statistic"
                ],

            "p-value":
                shapiro[
                    "p_value"
                ],

            "Interpretation":
                (
                    "Review residual distribution"
                    if (
                        shapiro[
                            "p_value"
                        ]
                        is not None
                        and
                        shapiro[
                            "p_value"
                        ]
                        <
                        alpha
                    )
                    else
                    "No strong normality warning"
                ),
        },

        {
            "Diagnostic":
                "Durbin-Watson",

            "Statistic":
                dw,

            "p-value":
                None,

            "Interpretation":
                (
                    "Values near 2 suggest little residual autocorrelation"
                ),
        },

        {
            "Diagnostic":
                "Breusch-Pagan",

            "Statistic":
                bp[
                    "statistic"
                ],

            "p-value":
                bp[
                    "p_value"
                ],

            "Interpretation":
                (
                    "Possible heteroscedasticity"
                    if bp[
                        "p_value"
                    ]
                    <
                    alpha
                    else
                    "No strong heteroscedasticity warning"
                ),
        },

        {
            "Diagnostic":
                "Extreme Standardized Residuals",

            "Statistic":
                extreme_residuals,

            "p-value":
                None,

            "Interpretation":
                (
                    "Cases with |standardized residual| > 3"
                ),
        },
    ]


    # ------------------------------------------------------
    # INTERPRETATION
    # ------------------------------------------------------

    significant_predictors = [
        row[
            "Predictor"
        ]
        for row
        in coefficient_rows
        if (
            row[
                "Predictor"
            ]
            !=
            "Intercept"
            and
            row[
                "Significant"
            ]
            ==
            "Yes"
        )
    ]


    if (
        model_p_value
        is not None
        and
        model_p_value
        <
        alpha
    ):
        model_decision = (
            "The regression model is statistically significant."
        )
    else:
        model_decision = (
            "The regression model is not statistically significant."
        )


    interpretation = (
        f"{model_decision} "
        f"The model explains approximately "
        f"{model['r_squared'] * 100:.2f}% "
        f"of the variation in {dependent_variable}. "
    )


    if significant_predictors:
        interpretation += (
            "Statistically significant predictors include "
            +
            ", ".join(
                significant_predictors
            )
            +
            ". "
        )

    else:
        interpretation += (
            "No predictor was statistically significant "
            "at the selected alpha level. "
        )


    interpretation += (
        "Regression coefficients describe association "
        "while controlling for the other predictors in "
        "the model; they do not by themselves establish causation."
    )


    # ------------------------------------------------------
    # APA
    # ------------------------------------------------------

    if (
        model_p_value
        is not None
    ):
        if model_p_value < 0.001:
            p_text = "p < .001"
        else:
            p_text = (
                f"p = {model_p_value:.3f}"
            )
    else:
        p_text = "p not available"


    regression_type = (
        "simple linear regression"
        if len(
            predictors
        ) == 1
        else
        "multiple linear regression"
    )


    apa = (
        f"A {regression_type} was performed to predict "
        f"{dependent_variable} from "
        f"{', '.join(predictors)}. "
        f"The model explained "
        f"{model['r_squared'] * 100:.1f}% "
        f"of the variance, "
        f"R² = {model['r_squared']:.3f}, "
        f"F({df_regression}, {df_residual}) = "
        f"{f_statistic:.3f}, "
        f"{p_text}."
        if f_statistic
        is not None
        else
        "Regression model statistics were unavailable."
    )


    return json_safe({
        "test_name":
            (
                "Simple Linear Regression"
                if len(
                    predictors
                )
                ==
                1
                else
                "Multiple Linear Regression"
            ),

        "configuration": {
            "dependent_variable":
                dependent_variable,

            "predictors":
                predictors,

            "alpha":
                alpha,

            "confidence_level":
                confidence_level,

            "include_intercept":
                include_intercept,
        },

        "tables": [
            {
                "title":
                    "Model Summary",

                "columns": [
                    "n",
                    "Predictors",
                    "R²",
                    "Adjusted R²",
                    "RMSE",
                ],

                "rows":
                    model_summary_rows,
            },

            {
                "title":
                    "ANOVA",

                "columns": [
                    "Source",
                    "Sum of Squares",
                    "df",
                    "Mean Square",
                    "F",
                    "p-value",
                ],

                "rows":
                    anova_rows,
            },

            {
                "title":
                    "Regression Coefficients",

                "columns": [
                    "Predictor",
                    "B",
                    "Std. Error",
                    "Standardized Beta",
                    "t",
                    "p-value",
                    "CI Lower",
                    "CI Upper",
                    "Significant",
                ],

                "rows":
                    coefficient_rows,
            },

            {
                "title":
                    "Multicollinearity",

                "columns": [
                    "Predictor",
                    "VIF",
                    "Tolerance",
                    "Status",
                ],

                "rows":
                    vif_rows,
            },
        ],

        "diagnostics": {
            "title":
                "Regression Diagnostics",

            "columns": [
                "Diagnostic",
                "Statistic",
                "p-value",
                "Interpretation",
            ],

            "rows":
                diagnostics_rows,
        },

        "interpretation":
            interpretation,

        "apa":
            apa,
    })
