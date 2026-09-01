import math

import numpy as np
import pandas as pd

from scipy import stats


# ==========================================================
# JSON SAFE
# ==========================================================

def json_safe(
    value,
):
    if value is None:
        return None


    if isinstance(
        value,
        (
            bool,
            np.bool_,
        ),
    ):
        return bool(
            value
        )


    if isinstance(
        value,
        np.integer,
    ):
        return int(
            value
        )


    if isinstance(
        value,
        np.floating,
    ):
        number = float(
            value
        )

        if (
            math.isnan(
                number
            )
            or
            math.isinf(
                number
            )
        ):
            return None

        return number


    if isinstance(
        value,
        np.ndarray,
    ):
        return [
            json_safe(
                item
            )
            for item
            in value.tolist()
        ]


    if isinstance(
        value,
        dict,
    ):
        return {
            str(
                key
            ):
                json_safe(
                    item
                )
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
            json_safe(
                item
            )
            for item
            in value
        ]


    return value


# ==========================================================
# P-VALUE FORMATTER
# ==========================================================

def format_p(
    value,
):
    if value is None:
        return "p unavailable"

    value = float(
        value
    )

    if value < 0.001:
        return "p < .001"

    return (
        f"p = {value:.3f}"
    )


# ==========================================================
# EFFECT SIZE INTERPRETATION
# ==========================================================

def effect_size_label(
    eta_squared,
):
    if (
        eta_squared
        is None
    ):
        return "Unavailable"


    eta_squared = float(
        eta_squared
    )


    if eta_squared < 0.01:
        return "Negligible"

    if eta_squared < 0.06:
        return "Small"

    if eta_squared < 0.14:
        return "Medium"

    return "Large"


# ==========================================================
# OLS FIT
# ==========================================================

def fit_ols(
    X,
    y,
):
    X = np.asarray(
        X,
        dtype=float,
    )

    y = np.asarray(
        y,
        dtype=float,
    )


    beta = (
        np.linalg.pinv(
            X
        )
        @
        y
    )


    fitted = (
        X
        @
        beta
    )


    residuals = (
        y
        -
        fitted
    )


    sse = float(
        np.sum(
            residuals
            **
            2
        )
    )


    rank = int(
        np.linalg.matrix_rank(
            X
        )
    )


    n = int(
        len(
            y
        )
    )


    df_residual = (
        n
        -
        rank
    )


    if df_residual <= 0:
        raise ValueError(
            "The ANCOVA model does not "
            "have enough residual degrees "
            "of freedom."
        )


    mse = (
        sse
        /
        df_residual
    )


    xtx_inverse = (
        np.linalg.pinv(
            X.T
            @
            X
        )
    )


    covariance_beta = (
        mse
        *
        xtx_inverse
    )


    standard_errors = (
        np.sqrt(
            np.maximum(
                np.diag(
                    covariance_beta
                ),
                0,
            )
        )
    )


    return {
        "beta":
            beta,

        "fitted":
            fitted,

        "residuals":
            residuals,

        "sse":
            sse,

        "rank":
            rank,

        "df_residual":
            df_residual,

        "mse":
            mse,

        "covariance_beta":
            covariance_beta,

        "standard_errors":
            standard_errors,
    }


# ==========================================================
# DESIGN MATRIX
# ==========================================================

def build_design_matrix(
    dataframe,
    factor_variable,
    covariates,
    categories,
):
    n = len(
        dataframe
    )


    columns = [
        np.ones(
            n,
            dtype=float,
        )
    ]


    names = [
        "Intercept"
    ]


    factor_values = (
        dataframe[
            factor_variable
        ]
        .astype(
            str
        )
        .to_numpy()
    )


    dummy_arrays = []


    for category in categories[
        1:
    ]:
        dummy = (
            factor_values
            ==
            category
        ).astype(
            float
        )


        dummy_arrays.append(
            dummy
        )


        columns.append(
            dummy
        )


        names.append(
            (
                f"{factor_variable}"
                f"[{category}]"
            )
        )


    for covariate in covariates:
        values = (
            dataframe[
                covariate
            ]
            .to_numpy(
                dtype=float
            )
        )

        columns.append(
            values
        )

        names.append(
            covariate
        )


    X = np.column_stack(
        columns
    )


    return {
        "X":
            X,

        "names":
            names,

        "dummy_arrays":
            dummy_arrays,
    }


# ==========================================================
# PREPARE DATA
# ==========================================================

def prepare_data(
    dataframe,
    dependent_variable,
    factor_variable,
    covariates,
):
    required = [
        dependent_variable,
        factor_variable,
        *covariates,
    ]


    missing_columns = [
        column
        for column
        in required
        if column
        not in dataframe.columns
    ]


    if missing_columns:
        raise ValueError(
            (
                "Dataset does not contain: "
                +
                ", ".join(
                    missing_columns
                )
            )
        )


    working = (
        dataframe[
            required
        ]
        .copy()
    )


    working[
        dependent_variable
    ] = pd.to_numeric(
        working[
            dependent_variable
        ],
        errors="coerce",
    )


    for covariate in covariates:
        working[
            covariate
        ] = pd.to_numeric(
            working[
                covariate
        ],
        errors="coerce",
    )


    working[
        factor_variable
    ] = (
        working[
            factor_variable
        ]
        .replace(
            r"^\s*$",
            np.nan,
            regex=True,
        )
    )


    working = (
        working
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .dropna(
            subset=required
        )
    )


    if len(
        working
    ) < 20:
        raise ValueError(
            "ANCOVA requires at least "
            "20 complete observations."
        )


    working[
        factor_variable
    ] = (
        working[
            factor_variable
        ]
        .astype(
            str
        )
    )


    categories = sorted(
        working[
            factor_variable
        ]
        .unique()
        .tolist()
    )


    if len(
        categories
    ) < 2:
        raise ValueError(
            "The factor variable must "
            "contain at least two groups."
        )


    if len(
        categories
    ) > 20:
        raise ValueError(
            "The selected factor contains "
            "too many categories for this "
            "ANCOVA implementation."
        )


    for category in categories:
        group_count = int(
            (
                working[
                    factor_variable
                ]
                ==
                category
            ).sum()
        )


        if group_count < 2:
            raise ValueError(
                (
                    f"Factor group '{category}' "
                    f"contains fewer than "
                    f"two observations."
                )
            )


    for covariate in covariates:
        if (
            working[
                covariate
            ]
            .nunique()
            <
            2
        ):
            raise ValueError(
                (
                    f"Covariate '{covariate}' "
                    f"is constant and cannot "
                    f"be used in ANCOVA."
                )
            )


    return (
        working,
        categories,
    )


# ==========================================================
# PARTIAL F TEST
# ==========================================================

def partial_f_test(
    full_fit,
    reduced_fit,
    full_rank,
    reduced_rank,
):
    df_effect = (
        full_rank
        -
        reduced_rank
    )


    if df_effect <= 0:
        return {
            "ss":
                0.0,

            "df":
                0,

            "ms":
                None,

            "f":
                None,

            "p":
                None,
        }


    ss_effect = max(
        0.0,
        (
            reduced_fit[
                "sse"
            ]
            -
            full_fit[
                "sse"
            ]
        ),
    )


    ms_effect = (
        ss_effect
        /
        df_effect
    )


    mse_error = (
        full_fit[
            "mse"
        ]
    )


    if mse_error <= 0:
        f_statistic = None
        p_value = None

    else:
        f_statistic = (
            ms_effect
            /
            mse_error
        )


        p_value = float(
            stats.f.sf(
                f_statistic,
                df_effect,
                full_fit[
                    "df_residual"
                ],
            )
        )


    return {
        "ss":
            ss_effect,

        "df":
            df_effect,

        "ms":
            ms_effect,

        "f":
            f_statistic,

        "p":
            p_value,
    }


# ==========================================================
# ANCOVA TABLE
# ==========================================================

def build_ancova_table(
    working,
    dependent_variable,
    factor_variable,
    covariates,
    categories,
    design,
    full_fit,
):
    X_full = (
        design[
            "X"
        ]
    )


    n_factor_columns = (
        len(
            categories
        )
        -
        1
    )


    rows = []


    # ------------------------------------------------------
    # FACTOR EFFECT
    # ------------------------------------------------------

    keep_columns = (
        [0]
        +
        list(
            range(
                1
                +
                n_factor_columns,
                X_full.shape[
                    1
                ],
            )
        )
    )


    X_reduced_factor = (
        X_full[
            :,
            keep_columns
        ]
    )


    reduced_factor_fit = (
        fit_ols(
            X_reduced_factor,
            working[
                dependent_variable
            ].to_numpy(
                dtype=float
            ),
        )
    )


    factor_test = (
        partial_f_test(
            full_fit=(
                full_fit
            ),

            reduced_fit=(
                reduced_factor_fit
            ),

            full_rank=(
                full_fit[
                    "rank"
                ]
            ),

            reduced_rank=(
                reduced_factor_fit[
                    "rank"
                ]
            ),
        )
    )


    factor_eta = (
        factor_test[
            "ss"
        ]
        /
        (
            factor_test[
                "ss"
            ]
            +
            full_fit[
                "sse"
            ]
        )
        if (
            factor_test[
                "ss"
            ]
            +
            full_fit[
                "sse"
            ]
        )
        >
        0
        else None
    )


    rows.append({
        "Effect":
            factor_variable,

        "SS":
            factor_test[
                "ss"
            ],

        "df":
            factor_test[
                "df"
            ],

        "MS":
            factor_test[
                "ms"
            ],

        "F":
            factor_test[
                "f"
            ],

        "p":
            factor_test[
                "p"
            ],

        "Partial Eta²":
            factor_eta,

        "Effect Size":
            effect_size_label(
                factor_eta
            ),
    })


    # ------------------------------------------------------
    # EACH COVARIATE
    # ------------------------------------------------------

    for covariate in covariates:

        column_index = (
            design[
                "names"
            ]
            .index(
                covariate
            )
        )


        keep = [
            index
            for index
            in range(
                X_full.shape[
                    1
                ]
            )
            if index
            !=
            column_index
        ]


        X_reduced = (
            X_full[
                :,
                keep
            ]
        )


        reduced_fit = (
            fit_ols(
                X_reduced,
                working[
                    dependent_variable
                ]
                .to_numpy(
                    dtype=float
                ),
            )
        )


        covariate_test = (
            partial_f_test(
                full_fit=(
                    full_fit
                ),

                reduced_fit=(
                    reduced_fit
                ),

                full_rank=(
                    full_fit[
                        "rank"
                    ]
                ),

                reduced_rank=(
                    reduced_fit[
                        "rank"
                    ]
                ),
            )
        )


        eta = (
            covariate_test[
                "ss"
            ]
            /
            (
                covariate_test[
                    "ss"
                ]
                +
                full_fit[
                    "sse"
                ]
            )
            if (
                covariate_test[
                    "ss"
                ]
                +
                full_fit[
                    "sse"
                ]
            )
            >
            0
            else None
        )


        rows.append({
            "Effect":
                covariate,

            "SS":
                covariate_test[
                    "ss"
                ],

            "df":
                covariate_test[
                    "df"
                ],

            "MS":
                covariate_test[
                    "ms"
                ],

            "F":
                covariate_test[
                    "f"
                ],

            "p":
                covariate_test[
                    "p"
                ],

            "Partial Eta²":
                eta,

            "Effect Size":
                effect_size_label(
                    eta
                ),
        })


    # ------------------------------------------------------
    # ERROR
    # ------------------------------------------------------

    rows.append({
        "Effect":
            "Error",

        "SS":
            full_fit[
                "sse"
            ],

        "df":
            full_fit[
                "df_residual"
            ],

        "MS":
            full_fit[
                "mse"
            ],

        "F":
            None,

        "p":
            None,

        "Partial Eta²":
            None,

        "Effect Size":
            None,
    })


    # ------------------------------------------------------
    # TOTAL
    # ------------------------------------------------------

    y = (
        working[
            dependent_variable
        ]
        .to_numpy(
            dtype=float
        )
    )


    total_ss = float(
        np.sum(
            (
                y
                -
                np.mean(
                    y
                )
            )
            **
            2
        )
    )


    rows.append({
        "Effect":
            "Total",

        "SS":
            total_ss,

        "df":
            len(
                y
            )
            -
            1,

        "MS":
            None,

        "F":
            None,

        "p":
            None,

        "Partial Eta²":
            None,

        "Effect Size":
            None,
    })


    return (
        rows,
        factor_test,
        factor_eta,
    )


# ==========================================================
# COEFFICIENT TABLE
# ==========================================================

def coefficient_table(
    design,
    full_fit,
    confidence_level,
):
    beta = (
        full_fit[
            "beta"
        ]
    )


    se = (
        full_fit[
            "standard_errors"
        ]
    )


    df = (
        full_fit[
            "df_residual"
        ]
    )


    alpha_ci = (
        1
        -
        confidence_level
    )


    critical = float(
        stats.t.ppf(
            1
            -
            alpha_ci
            /
            2,
            df,
        )
    )


    rows = []


    for (
        index,
        name,
    ) in enumerate(
        design[
            "names"
        ]
    ):
        coefficient = float(
            beta[
                index
            ]
        )


        standard_error = float(
            se[
                index
            ]
        )


        if standard_error > 0:
            t_value = (
                coefficient
                /
                standard_error
            )


            p_value = float(
                2
                *
                stats.t.sf(
                    abs(
                        t_value
                    ),
                    df,
                )
            )

        else:
            t_value = None
            p_value = None


        ci_low = (
            coefficient
            -
            critical
            *
            standard_error
        )


        ci_high = (
            coefficient
            +
            critical
            *
            standard_error
        )


        rows.append({
            "Term":
                name,

            "B":
                coefficient,

            "SE":
                standard_error,

            "t":
                t_value,

            "p":
                p_value,

            "CI Lower":
                ci_low,

            "CI Upper":
                ci_high,
        })


    return rows


# ==========================================================
# ADJUSTED MEANS
# ==========================================================

def adjusted_means(
    working,
    factor_variable,
    covariates,
    categories,
    design,
    full_fit,
    confidence_level,
):
    covariate_means = {
        covariate:
            float(
                working[
                    covariate
                ].mean()
            )
        for covariate
        in covariates
    }


    beta = (
        full_fit[
            "beta"
        ]
    )


    covariance_beta = (
        full_fit[
            "covariance_beta"
        ]
    )


    df = (
        full_fit[
            "df_residual"
        ]
    )


    alpha_ci = (
        1
        -
        confidence_level
    )


    critical = float(
        stats.t.ppf(
            1
            -
            alpha_ci
            /
            2,
            df,
        )
    )


    rows = []


    for category in categories:

        x0 = [
            1.0
        ]


        for dummy_category in categories[
            1:
        ]:
            x0.append(
                1.0
                if category
                ==
                dummy_category
                else 0.0
            )


        for covariate in covariates:
            x0.append(
                covariate_means[
                    covariate
                ]
            )


        x0 = np.asarray(
            x0,
            dtype=float,
        )


        estimate = float(
            x0
            @
            beta
        )


        variance = float(
            x0
            @
            covariance_beta
            @
            x0.T
        )


        standard_error = math.sqrt(
            max(
                variance,
                0,
            )
        )


        rows.append({
            factor_variable:
                category,

            "Adjusted Mean":
                estimate,

            "SE":
                standard_error,

            "CI Lower":
                (
                    estimate
                    -
                    critical
                    *
                    standard_error
                ),

            "CI Upper":
                (
                    estimate
                    +
                    critical
                    *
                    standard_error
                ),

            "N":
                int(
                    (
                        working[
                            factor_variable
                        ]
                        ==
                        category
                    ).sum()
                ),
        })


    return (
        rows,
        covariate_means,
    )


# ==========================================================
# ASSUMPTION CHECKS
# ==========================================================
def assumption_checks(
    working,
    dependent_variable,
    factor_variable,
    covariates,
    categories,
    design,
    full_fit,
    alpha,
):
    rows = []

    residuals = np.asarray(
        full_fit[
            "residuals"
        ],
        dtype=float,
    )

    residuals = residuals[
        np.isfinite(
            residuals
        )
    ]

    # ======================================================
    # 1. RESIDUAL NORMALITY
    # ======================================================

    if len(
        residuals
    ) >= 3:

        normality_sample = (
            residuals.copy()
        )

        # Shapiro-Wilk becomes expensive / overly sensitive
        # on very large samples. Limit diagnostic sample.
        if len(
            normality_sample
        ) > 5000:

            rng = (
                np.random.default_rng(
                    42
                )
            )

            normality_sample = (
                rng.choice(
                    normality_sample,
                    size=5000,
                    replace=False,
                )
            )

        try:

            shapiro_result = (
                stats.shapiro(
                    normality_sample
                )
            )

            shapiro_statistic = float(
                shapiro_result.statistic
            )

            shapiro_p_value = float(
                shapiro_result.pvalue
            )

            normality_met = (
                shapiro_p_value
                >=
                alpha
            )

            rows.append({
                "Assumption":
                    "Residual normality",

                "Test":
                    "Shapiro-Wilk",

                "Statistic":
                    shapiro_statistic,

                "p":
                    shapiro_p_value,

                "Status":
                    (
                        "Met"
                        if normality_met
                        else
                        "Review"
                    ),

                "Interpretation":
                    (
                        "Residual normality was not "
                        "statistically rejected."
                        if normality_met
                        else
                        "Residuals show evidence of "
                        "departure from normality. "
                        "For large samples, also consider "
                        "the magnitude and practical importance "
                        "of the departure."
                    ),
            })

        except Exception as exc:

            rows.append({
                "Assumption":
                    "Residual normality",

                "Test":
                    "Shapiro-Wilk",

                "Statistic":
                    None,

                "p":
                    None,

                "Status":
                    "Unavailable",

                "Interpretation":
                    (
                        "Residual normality could not "
                        "be evaluated: "
                        f"{str(exc)}"
                    ),
            })

    else:

        rows.append({
            "Assumption":
                "Residual normality",

            "Test":
                "Shapiro-Wilk",

            "Statistic":
                None,

            "p":
                None,

            "Status":
                "Unavailable",

            "Interpretation":
                (
                    "Too few finite residuals were "
                    "available for the Shapiro-Wilk test."
                ),
        })

    # ======================================================
    # 2. HOMOGENEITY OF VARIANCE
    # ======================================================

    groups = []

    valid_group_names = []

    for category in categories:

        values = (
            working.loc[
                working[
                    factor_variable
                ]
                ==
                category,
                dependent_variable,
            ]
            .to_numpy(
                dtype=float
            )
        )

        values = values[
            np.isfinite(
                values
            )
        ]

        if len(
            values
        ) >= 2:

            groups.append(
                values
            )

            valid_group_names.append(
                category
            )

    if len(
        groups
    ) >= 2:

        try:

            levene_result = (
                stats.levene(
                    *groups,
                    center="median",
                )
            )

            levene_statistic = float(
                levene_result.statistic
            )

            levene_p_value = float(
                levene_result.pvalue
            )

            variance_met = (
                levene_p_value
                >=
                alpha
            )

            rows.append({
                "Assumption":
                    "Homogeneity of variance",

                "Test":
                    "Levene",

                "Statistic":
                    levene_statistic,

                "p":
                    levene_p_value,

                "Status":
                    (
                        "Met"
                        if variance_met
                        else
                        "Review"
                    ),

                "Interpretation":
                    (
                        "Group variances are reasonably "
                        "consistent."
                        if variance_met
                        else
                        "There is evidence that group "
                        "variances differ. Interpret the "
                        "standard ANCOVA with caution."
                    ),
            })

        except Exception as exc:

            rows.append({
                "Assumption":
                    "Homogeneity of variance",

                "Test":
                    "Levene",

                "Statistic":
                    None,

                "p":
                    None,

                "Status":
                    "Unavailable",

                "Interpretation":
                    (
                        "Levene's test could not "
                        "be calculated: "
                        f"{str(exc)}"
                    ),
            })

    else:

        rows.append({
            "Assumption":
                "Homogeneity of variance",

            "Test":
                "Levene",

            "Statistic":
                None,

            "p":
                None,

            "Status":
                "Unavailable",

            "Interpretation":
                (
                    "At least two factor groups with "
                    "two or more observations are required."
                ),
        })

    # ======================================================
    # 3. HOMOGENEITY OF REGRESSION SLOPES
    #
    # Standard ANCOVA assumes that the relationship between
    # each covariate and outcome is similar across groups.
    #
    # Compare:
    #
    #   Standard model:
    #       Y ~ Factor + Covariates
    #
    # against:
    #
    #   Interaction model:
    #       Y ~ Factor + Covariates
    #           + Factor×Covariates
    #
    # ======================================================

    try:

        X_full = np.asarray(
            design[
                "X"
            ],
            dtype=float,
        )

        interaction_parts = [
            X_full
        ]

        factor_dummies = (
            design.get(
                "dummy_arrays",
                []
            )
        )

        for dummy in factor_dummies:

            dummy = np.asarray(
                dummy,
                dtype=float,
            )

            for covariate in covariates:

                covariate_values = (
                    working[
                        covariate
                    ]
                    .to_numpy(
                        dtype=float
                    )
                )

                interaction_term = (
                    dummy
                    *
                    covariate_values
                )

                interaction_parts.append(
                    interaction_term[
                        :,
                        None
                    ]
                )

        if len(
            interaction_parts
        ) > 1:

            X_interaction = (
                np.column_stack(
                    interaction_parts
                )
            )

            y = (
                working[
                    dependent_variable
                ]
                .to_numpy(
                    dtype=float
                )
            )

            interaction_fit = (
                fit_ols(
                    X_interaction,
                    y,
                )
            )

            df_interaction = (
                interaction_fit[
                    "rank"
                ]
                -
                full_fit[
                    "rank"
                ]
            )

            if df_interaction > 0:

                ss_interaction = max(
                    0.0,
                    (
                        full_fit[
                            "sse"
                        ]
                        -
                        interaction_fit[
                            "sse"
                        ]
                    ),
                )

                ms_interaction = (
                    ss_interaction
                    /
                    df_interaction
                )

                interaction_mse = (
                    interaction_fit[
                        "mse"
                    ]
                )

                if (
                    interaction_mse
                    >
                    0
                ):

                    interaction_f = (
                        ms_interaction
                        /
                        interaction_mse
                    )

                    interaction_p = float(
                        stats.f.sf(
                            interaction_f,
                            df_interaction,
                            interaction_fit[
                                "df_residual"
                            ],
                        )
                    )

                    slopes_met = (
                        interaction_p
                        >=
                        alpha
                    )

                    rows.append({
                        "Assumption":
                            (
                                "Homogeneity of "
                                "regression slopes"
                            ),

                        "Test":
                            (
                                "Factor × Covariate "
                                "interaction"
                            ),

                        "Statistic":
                            float(
                                interaction_f
                            ),

                        "p":
                            interaction_p,

                        "Status":
                            (
                                "Met"
                                if slopes_met
                                else
                                "Review"
                            ),

                        "Interpretation":
                            (
                                "No statistically significant "
                                "factor-by-covariate interaction "
                                "was detected. The common-slope "
                                "assumption is reasonably supported."
                                if slopes_met
                                else
                                "A statistically significant "
                                "factor-by-covariate interaction "
                                "was detected. Covariate slopes may "
                                "differ between groups, so the "
                                "standard ANCOVA should be "
                                "interpreted cautiously."
                            ),
                    })

                else:

                    rows.append({
                        "Assumption":
                            (
                                "Homogeneity of "
                                "regression slopes"
                            ),

                        "Test":
                            (
                                "Factor × Covariate "
                                "interaction"
                            ),

                        "Statistic":
                            None,

                        "p":
                            None,

                        "Status":
                            "Unavailable",

                        "Interpretation":
                            (
                                "The interaction model had "
                                "zero residual variance, so the "
                                "slope-homogeneity test could not "
                                "be evaluated normally."
                            ),
                    })

            else:

                rows.append({
                    "Assumption":
                        (
                            "Homogeneity of "
                            "regression slopes"
                        ),

                    "Test":
                        (
                            "Factor × Covariate "
                            "interaction"
                        ),

                    "Statistic":
                        None,

                    "p":
                        None,

                    "Status":
                        "Unavailable",

                    "Interpretation":
                        (
                            "The interaction terms did not "
                            "add estimable model degrees "
                            "of freedom."
                        ),
                })

        else:

            rows.append({
                "Assumption":
                    (
                        "Homogeneity of "
                        "regression slopes"
                    ),

                "Test":
                    (
                        "Factor × Covariate "
                        "interaction"
                    ),

                "Statistic":
                    None,

                "p":
                    None,

                "Status":
                    "Unavailable",

                "Interpretation":
                    (
                        "No estimable factor-by-covariate "
                        "interaction terms were available."
                    ),
            })

    except Exception as exc:

        rows.append({
            "Assumption":
                (
                    "Homogeneity of "
                    "regression slopes"
                ),

            "Test":
                (
                    "Factor × Covariate "
                    "interaction"
                ),

            "Statistic":
                None,

            "p":
                None,

            "Status":
                "Unavailable",

            "Interpretation":
                (
                    "The slope-homogeneity diagnostic "
                    "could not be calculated: "
                    f"{str(exc)}"
                ),
        })

    # ======================================================
    # 4. LINEARITY OF COVARIATES
    # ======================================================

    for covariate in covariates:

        try:

            covariate_values = (
                working[
                    covariate
                ]
                .to_numpy(
                    dtype=float
                )
            )

            dependent_values = (
                working[
                    dependent_variable
                ]
                .to_numpy(
                    dtype=float
                )
            )

            valid = (
                np.isfinite(
                    covariate_values
                )
                &
                np.isfinite(
                    dependent_values
                )
            )

            x = (
                covariate_values[
                    valid
                ]
            )

            y = (
                dependent_values[
                    valid
                ]
            )

            if (
                len(
                    x
                )
                >=
                3
                and
                np.std(
                    x
                )
                >
                0
                and
                np.std(
                    y
                )
                >
                0
            ):

                correlation_result = (
                    stats.pearsonr(
                        x,
                        y,
                    )
                )

                correlation = float(
                    correlation_result.statistic
                )

                p_value = float(
                    correlation_result.pvalue
                )

                rows.append({
                    "Assumption":
                        (
                            f"Covariate linearity: "
                            f"{covariate}"
                        ),

                    "Test":
                        (
                            "Pearson correlation "
                            "diagnostic"
                        ),

                    "Statistic":
                        correlation,

                    "p":
                        p_value,

                    "Status":
                        "Review",

                    "Interpretation":
                        (
                            f"The linear association between "
                            f"{covariate} and "
                            f"{dependent_variable} was "
                            f"r = {correlation:.3f}. "
                            f"This is a descriptive diagnostic; "
                            f"linearity should ideally also be "
                            f"evaluated visually in the "
                            f"Visualization module."
                        ),
                })

        except Exception as exc:

            rows.append({
                "Assumption":
                    (
                        f"Covariate linearity: "
                        f"{covariate}"
                    ),

                "Test":
                    "Diagnostic",

                "Statistic":
                    None,

                "p":
                    None,

                "Status":
                    "Unavailable",

                "Interpretation":
                    (
                        f"Linearity diagnostic could not "
                        f"be calculated for {covariate}: "
                        f"{str(exc)}"
                    ),
            })

    # ======================================================
    # 5. INDEPENDENCE NOTICE
    # ======================================================

    rows.append({
        "Assumption":
            "Independence of observations",

        "Test":
            "Study design",

        "Statistic":
            None,

        "p":
            None,

        "Status":
            "User review",

        "Interpretation":
            (
                "Independence depends primarily on the "
                "study design and data-collection process. "
                "It cannot be confirmed from the dataset "
                "values alone."
            ),
    })

    return rows

# ==========================================================
# MODEL SUMMARY
# ==========================================================

def model_summary(
    working,
    dependent_variable,
    full_fit,
    design,
):
    y = (
        working[
            dependent_variable
        ]
        .to_numpy(
            dtype=float
        )
    )


    total_ss = float(
        np.sum(
            (
                y
                -
                np.mean(
                    y
                )
            )
            **
            2
        )
    )


    if total_ss > 0:
        r_squared = (
            1
            -
            (
                full_fit[
                    "sse"
                ]
                /
                total_ss
            )
        )

    else:
        r_squared = None


    n = len(
        y
    )


    p = (
        full_fit[
            "rank"
        ]
    )


    if (
        r_squared
        is not None
        and
        n
        >
        p
    ):
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
                n
                -
                1
            )
            /
            (
                n
                -
                p
            )
        )

    else:
        adjusted_r_squared = None


    return [{
        "N":
            int(
                n
            ),

        "Parameters":
            int(
                p
            ),

        "R²":
            r_squared,

        "Adjusted R²":
            adjusted_r_squared,

        "Residual df":
            full_fit[
                "df_residual"
            ],

        "Residual MSE":
            full_fit[
                "mse"
            ],
    }]


# ==========================================================
# MAIN ANCOVA
# ==========================================================

def run_ancova(
    dataframe,
    dependent_variable,
    factor_variable,
    covariates,
    alpha=0.05,
    confidence_level=0.95,
):
    (
        working,
        categories,
    ) = prepare_data(
        dataframe=(
            dataframe
        ),

        dependent_variable=(
            dependent_variable
        ),

        factor_variable=(
            factor_variable
        ),

        covariates=(
            covariates
        ),
    )


    design = (
        build_design_matrix(
            dataframe=(
                working
            ),

            factor_variable=(
                factor_variable
            ),

            covariates=(
                covariates
            ),

            categories=(
                categories
            ),
        )
    )


    y = (
        working[
            dependent_variable
        ]
        .to_numpy(
            dtype=float
        )
    )


    full_fit = (
        fit_ols(
            design[
                "X"
            ],
            y,
        )
    )


    (
        ancova_rows,
        factor_test,
        factor_eta,
    ) = build_ancova_table(
        working=(
            working
        ),

        dependent_variable=(
            dependent_variable
        ),

        factor_variable=(
            factor_variable
        ),

        covariates=(
            covariates
        ),

        categories=(
            categories
        ),

        design=(
            design
        ),

        full_fit=(
            full_fit
        ),
    )


    coefficients = (
        coefficient_table(
            design=(
                design
            ),

            full_fit=(
                full_fit
            ),

            confidence_level=(
                confidence_level
            ),
        )
    )


    (
        adjusted_mean_rows,
        covariate_means,
    ) = adjusted_means(
        working=(
            working
        ),

        factor_variable=(
            factor_variable
        ),

        covariates=(
            covariates
        ),

        categories=(
            categories
        ),

        design=(
            design
        ),

        full_fit=(
            full_fit
        ),

        confidence_level=(
            confidence_level
        ),
    )


    assumptions = (
        assumption_checks(
            working=(
                working
            ),

            dependent_variable=(
                dependent_variable
            ),

            factor_variable=(
                factor_variable
            ),

            covariates=(
                covariates
            ),

            categories=(
                categories
            ),

            design=(
                design
            ),

            full_fit=(
                full_fit
            ),

            alpha=(
                alpha
            ),
        )
    )


    summary = (
        model_summary(
            working=(
                working
            ),

            dependent_variable=(
                dependent_variable
            ),

            full_fit=(
                full_fit
            ),

            design=(
                design
            ),
        )
    )


    significant = (
        factor_test[
            "p"
        ]
        is not None
        and
        factor_test[
            "p"
        ]
        <
        alpha
    )


    eta_label = (
        effect_size_label(
            factor_eta
        )
    )


    covariate_text = (
        ", ".join(
            covariates
        )
    )


    if significant:

        interpretation = (
            f"After statistically adjusting for "
            f"{covariate_text}, there was a statistically "
            f"significant effect of {factor_variable} on "
            f"{dependent_variable}, "
            f"F({factor_test['df']}, "
            f"{full_fit['df_residual']}) = "
            f"{factor_test['f']:.3f}, "
            f"{format_p(factor_test['p'])}. "
            f"The partial eta squared was "
            f"{factor_eta:.3f}, representing a "
            f"{eta_label.lower()} adjusted effect."
        )

    else:

        interpretation = (
            f"After statistically adjusting for "
            f"{covariate_text}, there was no statistically "
            f"significant effect of {factor_variable} on "
            f"{dependent_variable}, "
            f"F({factor_test['df']}, "
            f"{full_fit['df_residual']}) = "
            f"{factor_test['f']:.3f}, "
            f"{format_p(factor_test['p'])}. "
            f"The partial eta squared was "
            f"{factor_eta:.3f}, representing a "
            f"{eta_label.lower()} adjusted effect."
        )


    apa = (
        f"An analysis of covariance (ANCOVA) was conducted "
        f"to examine differences in {dependent_variable} "
        f"across levels of {factor_variable} while controlling "
        f"for {covariate_text}. "
        f"The adjusted effect of {factor_variable} was "
        f"{'statistically significant' if significant else 'not statistically significant'}, "
        f"F({factor_test['df']}, "
        f"{full_fit['df_residual']}) = "
        f"{factor_test['f']:.2f}, "
        f"{format_p(factor_test['p'])}, "
        f"partial η² = {factor_eta:.3f}."
    )


    return json_safe({
        "analysis_name":
            "Analysis of Covariance",

        "title":
            "ANCOVA",

        "configuration": {
            "dependent_variable":
                dependent_variable,

            "factor_variable":
                factor_variable,

            "covariates":
                covariates,

            "alpha":
                alpha,

            "confidence_level":
                confidence_level,

            "reference_group":
                categories[
                    0
                ],

            "covariate_means":
                covariate_means,
        },

        "factor_result": {
            "factor":
                factor_variable,

            "F":
                factor_test[
                    "f"
                ],

            "df_effect":
                factor_test[
                    "df"
                ],

            "df_error":
                full_fit[
                    "df_residual"
                ],

            "p":
                factor_test[
                    "p"
                ],

            "partial_eta_squared":
                factor_eta,

            "effect_size":
                eta_label,

            "significant":
                significant,
        },

        "tables": [
            {
                "title":
                    "ANCOVA Model Summary",

                "columns": [
                    "N",
                    "Parameters",
                    "R²",
                    "Adjusted R²",
                    "Residual df",
                    "Residual MSE",
                ],

                "rows":
                    summary,
            },

            {
                "title":
                    "ANCOVA Table",

                "columns": [
                    "Effect",
                    "SS",
                    "df",
                    "MS",
                    "F",
                    "p",
                    "Partial Eta²",
                    "Effect Size",
                ],

                "rows":
                    ancova_rows,
            },

            {
                "title":
                    "Parameter Estimates",

                "columns": [
                    "Term",
                    "B",
                    "SE",
                    "t",
                    "p",
                    "CI Lower",
                    "CI Upper",
                ],

                "rows":
                    coefficients,
            },

            {
                "title":
                    "Adjusted Means",

                "columns": [
                    factor_variable,
                    "Adjusted Mean",
                    "SE",
                    "CI Lower",
                    "CI Upper",
                    "N",
                ],

                "rows":
                    adjusted_mean_rows,
            },

            {
                "title":
                    "ANCOVA Assumption Checks",

                "columns": [
                    "Assumption",
                    "Test",
                    "Statistic",
                    "p",
                    "Status",
                    "Interpretation",
                ],

                "rows":
                    assumptions,
            },
        ],

        "assumptions":
            assumptions,

        "interpretation":
            interpretation,

        "apa":
            apa,

        "metadata": {
            "complete_cases":
                int(
                    len(
                        working
                    )
                ),

            "factor_levels":
                categories,

            "reference_group":
                categories[
                    0
                ],
        },
    })
