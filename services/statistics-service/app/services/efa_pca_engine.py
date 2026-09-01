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
# FORMAT P VALUE
# ==========================================================

def format_p(
    p_value,
):
    if p_value is None:
        return "p unavailable"

    if p_value < 0.001:
        return "p < .001"

    return (
        f"p = {p_value:.3f}"
    )


# ==========================================================
# PREPARE DATA
# ==========================================================

def prepare_data(
    dataframe,
    variables,
):
    missing_columns = [
        variable
        for variable
        in variables
        if variable
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
            variables
        ]
        .copy()
    )


    for variable in variables:

        original_non_missing = int(
            working[
                variable
            ]
            .notna()
            .sum()
        )


        converted = pd.to_numeric(
            working[
                variable
            ],
            errors="coerce",
        )


        converted_non_missing = int(
            converted
            .notna()
            .sum()
        )


        if original_non_missing > 0:

            ratio = (
                converted_non_missing
                /
                original_non_missing
            )

        else:

            ratio = 0.0


        if ratio < 0.80:

            raise ValueError(
                (
                    f"Variable '{variable}' is not "
                    f"sufficiently numeric for EFA/PCA."
                )
            )


        working[
            variable
        ] = converted


    working = (
        working
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .dropna()
    )


    n = len(
        working
    )


    p = len(
        variables
    )


    if n < 20:

        raise ValueError(
            (
                "EFA/PCA requires at least "
                "20 complete observations. "
                f"Only {n} remained."
            )
        )


    if n <= p:

        raise ValueError(
            (
                "The number of complete observations "
                "must exceed the number of selected variables."
            )
        )


    for variable in variables:

        if (
            working[
                variable
            ]
            .nunique()
            <
            2
        ):
            raise ValueError(
                (
                    f"Variable '{variable}' is constant "
                    f"and cannot be included."
                )
            )


    return working


# ==========================================================
# STANDARDIZE DATA
# ==========================================================

def standardize_data(
    working,
):
    means = (
        working
        .mean()
    )


    stds = (
        working
        .std(
            ddof=1
        )
    )


    if (
        stds
        <=
        0
    ).any():

        bad_columns = (
            stds[
                stds
                <=
                0
            ]
            .index
            .tolist()
        )


        raise ValueError(
            (
                "Zero-variance variables cannot "
                "be analysed: "
                +
                ", ".join(
                    bad_columns
                )
            )
        )


    standardized = (
        (
            working
            -
            means
        )
        /
        stds
    )


    return (
        standardized,
        means,
        stds,
    )


# ==========================================================
# CORRELATION MATRIX
# ==========================================================

def correlation_matrix(
    standardized,
):
    matrix = np.corrcoef(
        standardized
        .to_numpy(
            dtype=float
        ),
        rowvar=False,
    )


    if not np.all(
        np.isfinite(
            matrix
        )
    ):

        raise ValueError(
            "The correlation matrix contains "
            "invalid values."
        )


    return matrix


# ==========================================================
# KMO
# ==========================================================

def calculate_kmo(
    correlation,
):
    try:

        inverse = (
            np.linalg.pinv(
                correlation
            )
        )


        diagonal = np.sqrt(
            np.outer(
                np.diag(
                    inverse
                ),
                np.diag(
                    inverse
                ),
            )
        )


        partial = (
            -inverse
            /
            diagonal
        )


        np.fill_diagonal(
            partial,
            0.0,
        )


        corr = (
            correlation
            .copy()
        )


        np.fill_diagonal(
            corr,
            0.0,
        )


        corr_sq = (
            corr
            **
            2
        )


        partial_sq = (
            partial
            **
            2
        )


        numerator = float(
            np.sum(
                corr_sq
            )
        )


        denominator = (
            numerator
            +
            float(
                np.sum(
                    partial_sq
                )
            )
        )


        if denominator <= 0:

            overall_kmo = None

        else:

            overall_kmo = (
                numerator
                /
                denominator
            )


        variable_kmo = []


        for index in range(
            correlation.shape[
                0
            ]
        ):

            variable_corr = float(
                np.sum(
                    corr_sq[
                        index,
                        :
                    ]
                )
            )


            variable_partial = float(
                np.sum(
                    partial_sq[
                        index,
                        :
                    ]
                )
            )


            variable_total = (
                variable_corr
                +
                variable_partial
            )


            if variable_total <= 0:

                item_kmo = None

            else:

                item_kmo = (
                    variable_corr
                    /
                    variable_total
                )


            variable_kmo.append(
                item_kmo
            )


        return (
            overall_kmo,
            variable_kmo,
        )


    except Exception:

        return (
            None,
            [
                None
            ]
            *
            correlation.shape[
                0
            ],
        )


# ==========================================================
# KMO INTERPRETATION
# ==========================================================

def kmo_label(
    value,
):
    if value is None:
        return "Unavailable"

    if value >= 0.90:
        return "Excellent"

    if value >= 0.80:
        return "Very good"

    if value >= 0.70:
        return "Good"

    if value >= 0.60:
        return "Acceptable"

    if value >= 0.50:
        return "Poor"

    return "Unacceptable"


# ==========================================================
# BARTLETT SPHERICITY TEST
# ==========================================================

def bartlett_test(
    correlation,
    n,
):
    p = (
        correlation.shape[
            0
        ]
    )


    determinant = float(
        np.linalg.det(
            correlation
        )
    )


    if determinant <= 0:

        determinant = (
            np.finfo(
                float
            )
            .tiny
        )


    chi_square = (
        -(
            n
            -
            1
            -
            (
                2
                *
                p
                +
                5
            )
            /
            6
        )
        *
        math.log(
            determinant
        )
    )


    df = int(
        p
        *
        (
            p
            -
            1
        )
        /
        2
    )


    p_value = float(
        stats.chi2.sf(
            chi_square,
            df,
        )
    )


    return {
        "chi_square":
            float(
                chi_square
            ),

        "df":
            df,

        "p":
            p_value,
    }


# ==========================================================
# EIGEN DECOMPOSITION
# ==========================================================

def sorted_eigen(
    matrix,
):
    eigenvalues, eigenvectors = (
        np.linalg.eigh(
            matrix
        )
    )


    order = np.argsort(
        eigenvalues
    )[
        ::-1
    ]


    eigenvalues = (
        eigenvalues[
            order
        ]
    )


    eigenvectors = (
        eigenvectors[
            :,
            order
        ]
    )


    return (
        eigenvalues,
        eigenvectors,
    )


# ==========================================================
# VARIMAX ROTATION
# ==========================================================

def varimax(
    loadings,
    gamma=1.0,
    q=100,
    tol=1e-6,
):
    loadings = np.asarray(
        loadings,
        dtype=float,
    )


    rows, columns = (
        loadings.shape
    )


    if columns <= 1:

        return (
            loadings,
            np.eye(
                columns
            ),
        )


    rotation = np.eye(
        columns
    )


    previous = 0.0


    for _ in range(
        q
    ):

        rotated = (
            loadings
            @
            rotation
        )


        u, singular_values, vh = (
            np.linalg.svd(
                loadings.T
                @
                (
                    rotated
                    **
                    3
                    -
                    (
                        gamma
                        /
                        rows
                    )
                    *
                    rotated
                    @
                    np.diag(
                        np.sum(
                            rotated
                            **
                            2,
                            axis=0,
                        )
                    )
                )
            )
        )


        rotation = (
            u
            @
            vh
        )


        current = float(
            np.sum(
                singular_values
            )
        )


        if (
            previous != 0
            and
            current
            /
            previous
            <
            1
            +
            tol
        ):

            break


        previous = (
            current
        )


    return (
        loadings
        @
        rotation,

        rotation,
    )


# ==========================================================
# PCA
# ==========================================================

def run_pca(
    correlation,
    n_components,
):
    eigenvalues, eigenvectors = (
        sorted_eigen(
            correlation
        )
    )


    selected_values = (
        eigenvalues[
            :n_components
        ]
    )


    selected_vectors = (
        eigenvectors[
            :,
            :n_components
        ]
    )


    selected_values = np.maximum(
        selected_values,
        0.0,
    )


    loadings = (
        selected_vectors
        *
        np.sqrt(
            selected_values
        )
    )


    communalities = np.sum(
        loadings
        **
        2,
        axis=1,
    )


    return {
        "eigenvalues":
            eigenvalues,

        "loadings":
            loadings,

        "communalities":
            communalities,
    }


# ==========================================================
# INITIAL COMMUNALITIES FOR EFA
# ==========================================================

def initial_communality(
    correlation,
):
    inverse = np.linalg.pinv(
        correlation
    )


    diagonal = np.diag(
        inverse
    )


    communalities = (
        1.0
        -
        (
            1.0
            /
            diagonal
        )
    )


    communalities = np.clip(
        communalities,
        0.01,
        0.99,
    )


    return communalities


# ==========================================================
# PRINCIPAL AXIS FACTORING
# ==========================================================

def run_efa(
    correlation,
    n_factors,
    max_iter=100,
    tolerance=1e-5,
):
    communalities = (
        initial_communality(
            correlation
        )
    )


    loadings = None

    reduced_eigenvalues = None


    for _ in range(
        max_iter
    ):

        reduced = (
            correlation
            .copy()
        )


        np.fill_diagonal(
            reduced,
            communalities,
        )


        eigenvalues, eigenvectors = (
            sorted_eigen(
                reduced
            )
        )


        selected_values = np.maximum(
            eigenvalues[
                :n_factors
            ],
            0.0,
        )


        selected_vectors = (
            eigenvectors[
                :,
                :n_factors
            ]
        )


        loadings = (
            selected_vectors
            *
            np.sqrt(
                selected_values
            )
        )


        new_communalities = np.sum(
            loadings
            **
            2,
            axis=1,
        )


        new_communalities = np.clip(
            new_communalities,
            0.0,
            1.0,
        )


        difference = float(
            np.max(
                np.abs(
                    new_communalities
                    -
                    communalities
                )
            )
        )


        communalities = (
            new_communalities
        )


        reduced_eigenvalues = (
            eigenvalues
        )


        if difference < tolerance:

            break


    return {
        "eigenvalues":
            reduced_eigenvalues,

        "loadings":
            loadings,

        "communalities":
            communalities,
    }


# ==========================================================
# AUTO NUMBER OF FACTORS
# ==========================================================

def determine_factor_count(
    correlation_eigenvalues,
    number_variables,
):
    count = int(
        np.sum(
            correlation_eigenvalues
            >
            1.0
        )
    )


    if count < 1:

        count = 1


    return min(
        count,
        number_variables,
    )


# ==========================================================
# VARIANCE TABLE
# ==========================================================

def variance_table(
    eigenvalues,
    total_variables,
):
    rows = []

    cumulative = 0.0


    total = float(
        total_variables
    )


    for (
        index,
        eigenvalue,
    ) in enumerate(
        eigenvalues
    ):

        eigenvalue = float(
            eigenvalue
        )


        variance_percent = (
            max(
                eigenvalue,
                0.0,
            )
            /
            total
            *
            100
        )


        cumulative += (
            variance_percent
        )


        rows.append({
            "Component":
                int(
                    index
                    +
                    1
                ),

            "Eigenvalue":
                eigenvalue,

            "Variance %":
                variance_percent,

            "Cumulative %":
                cumulative,

            "Retain (Kaiser > 1)":
                bool(
                    eigenvalue
                    >
                    1
                ),
        })


    return rows


# ==========================================================
# LOADINGS TABLE
# ==========================================================

def loadings_table(
    variables,
    loadings,
    prefix,
):
    columns = [
        "Variable"
    ]


    columns.extend(
        [
            (
                f"{prefix} "
                f"{index + 1}"
            )
            for index
            in range(
                loadings.shape[
                    1
                ]
            )
        ]
    )


    rows = []


    for row_index, variable in enumerate(
        variables
    ):

        row = {
            "Variable":
                variable
        }


        for factor_index in range(
            loadings.shape[
                1
            ]
        ):

            row[
                (
                    f"{prefix} "
                    f"{factor_index + 1}"
                )
            ] = float(
                loadings[
                    row_index,
                    factor_index
                ]
            )


        rows.append(
            row
        )


    return (
        columns,
        rows,
    )


# ==========================================================
# COMMUNALITY TABLE
# ==========================================================

def communality_table(
    variables,
    communalities,
):
    rows = []


    for (
        variable,
        communality,
    ) in zip(
        variables,
        communalities,
    ):

        communality = float(
            communality
        )


        rows.append({
            "Variable":
                variable,

            "Communality":
                communality,

            "Uniqueness":
                (
                    1.0
                    -
                    communality
                ),

            "Status":
                (
                    "Good"
                    if communality
                    >=
                    0.50
                    else
                    (
                        "Review"
                        if communality
                        >=
                        0.30
                        else
                        "Low"
                    )
                ),
        })


    return rows


# ==========================================================
# KMO VARIABLE TABLE
# ==========================================================

def kmo_variable_table(
    variables,
    item_kmo,
):
    rows = []


    for (
        variable,
        value,
    ) in zip(
        variables,
        item_kmo,
    ):

        rows.append({
            "Variable":
                variable,

            "KMO":
                value,

            "Assessment":
                kmo_label(
                    value
                ),
        })


    return rows


# ==========================================================
# FACTOR INTERPRETATION
# ==========================================================

def factor_interpretation(
    variables,
    loadings,
    threshold,
    prefix,
):
    rows = []


    for factor_index in range(
        loadings.shape[
            1
        ]
    ):

        members = []


        for variable_index, variable in enumerate(
            variables
        ):

            loading = float(
                loadings[
                    variable_index,
                    factor_index
                ]
            )


            if abs(
                loading
            ) >= threshold:

                members.append(
                    (
                        variable,
                        loading,
                    )
                )


        members.sort(
            key=lambda item:
                abs(
                    item[
                        1
                    ]
                ),
            reverse=True,
        )


        if members:

            variable_text = (
                ", ".join(
                    [
                        (
                            f"{variable} "
                            f"({loading:.3f})"
                        )
                        for variable, loading
                        in members
                    ]
                )
            )

        else:

            variable_text = (
                "No loadings reached "
                f"|{threshold:.2f}|."
            )


        rows.append({
            prefix:
                int(
                    factor_index
                    +
                    1
                ),

            "Variables with Strong Loadings":
                variable_text,
        })


    return rows


# ==========================================================
# MAIN ENGINE
# ==========================================================

def run_efa_pca(
    dataframe,
    variables,
    method="pca",
    n_factors=None,
    rotation="varimax",
    alpha=0.05,
    loading_threshold=0.40,
):
    working = prepare_data(
        dataframe=(
            dataframe
        ),

        variables=(
            variables
        ),
    )


    standardized, means, stds = (
        standardize_data(
            working
        )
    )


    correlation = (
        correlation_matrix(
            standardized
        )
    )


    n = int(
        len(
            working
        )
    )


    p = int(
        len(
            variables
        )
    )


    # ======================================================
    # INITIAL EIGENVALUES
    # ======================================================

    correlation_eigenvalues, _ = (
        sorted_eigen(
            correlation
        )
    )


    automatic_count = (
        determine_factor_count(
            correlation_eigenvalues=(
                correlation_eigenvalues
            ),

            number_variables=(
                p
            ),
        )
    )


    selected_count = (
        int(
            n_factors
        )
        if n_factors
        is not None
        else
        automatic_count
    )


    selected_count = max(
        1,
        min(
            selected_count,
            p,
        ),
    )


    # ======================================================
    # KMO
    # ======================================================

    (
        overall_kmo,
        item_kmo,
    ) = calculate_kmo(
        correlation
    )


    # ======================================================
    # BARTLETT
    # ======================================================

    bartlett = (
        bartlett_test(
            correlation=(
                correlation
            ),

            n=(
                n
            ),
        )
    )


    # ======================================================
    # METHOD
    # ======================================================

    if method == "efa":

        analysis_result = (
            run_efa(
                correlation=(
                    correlation
                ),

                n_factors=(
                    selected_count
                ),
            )
        )


        method_name = (
            "Exploratory Factor Analysis"
        )


        prefix = (
            "Factor"
        )

    else:

        analysis_result = (
            run_pca(
                correlation=(
                    correlation
                ),

                n_components=(
                    selected_count
                ),
            )
        )


        method_name = (
            "Principal Component Analysis"
        )


        prefix = (
            "Component"
        )


    unrotated_loadings = (
        analysis_result[
            "loadings"
        ]
    )


    communalities = (
        analysis_result[
            "communalities"
        ]
    )


    # ======================================================
    # ROTATION
    # ======================================================

    if (
        rotation
        ==
        "varimax"
        and
        selected_count
        >
        1
    ):

        rotated_loadings, _ = (
            varimax(
                unrotated_loadings
            )
        )


        rotation_used = (
            "Varimax"
        )

    else:

        rotated_loadings = (
            unrotated_loadings
        )


        rotation_used = (
            "None"
        )


    # ======================================================
    # TABLES
    # ======================================================

    (
        loading_columns,
        loading_rows,
    ) = loadings_table(
        variables=(
            variables
        ),

        loadings=(
            unrotated_loadings
        ),

        prefix=(
            prefix
        ),
    )


    (
        rotated_columns,
        rotated_rows,
    ) = loadings_table(
        variables=(
            variables
        ),

        loadings=(
            rotated_loadings
        ),

        prefix=(
            prefix
        ),
    )


    factor_summary_rows = (
        factor_interpretation(
            variables=(
                variables
            ),

            loadings=(
                rotated_loadings
            ),

            threshold=(
                loading_threshold
            ),

            prefix=(
                prefix
            ),
        )
    )


    # ======================================================
    # SUITABILITY
    # ======================================================

    kmo_status = (
        (
            overall_kmo
            is not None
        )
        and
        (
            overall_kmo
            >=
            0.60
        )
    )


    bartlett_status = (
        bartlett[
            "p"
        ]
        <
        alpha
    )


    suitability = (
        kmo_status
        and
        bartlett_status
    )


    # ======================================================
    # INTERPRETATION
    # ======================================================

    if overall_kmo is None:

        kmo_text = (
            "The overall KMO statistic "
            "could not be estimated."
        )

    else:

        kmo_text = (
            f"The overall KMO measure was "
            f"{overall_kmo:.3f}, classified as "
            f"{kmo_label(overall_kmo).lower()}."
        )


    bartlett_text = (
        f"Bartlett's test of sphericity was "
        f"χ²({bartlett['df']}) = "
        f"{bartlett['chi_square']:.3f}, "
        f"{format_p(bartlett['p'])}."
    )


    if suitability:

        suitability_text = (
            "Together, these diagnostics support "
            "the use of dimension-reduction/factor "
            "analysis for the selected variables."
        )

    else:

        suitability_text = (
            "At least one suitability diagnostic "
            "suggests that the selected variables "
            "should be reviewed before interpreting "
            "the extracted structure."
        )


    interpretation = (
        f"{method_name} was performed on "
        f"{p} variables using {n} complete observations. "
        f"{kmo_text} "
        f"{bartlett_text} "
        f"{suitability_text} "
        f"SSAS retained {selected_count} "
        f"{prefix.lower()}(s) "
        f"{'automatically using the Kaiser criterion' if n_factors is None else 'using the requested manual setting'}. "
        f"{rotation_used} rotation was applied."
    )


    # ======================================================
    # APA
    # ======================================================

    apa = (
        f"A {method_name.lower()} was conducted "
        f"on {p} variables using {n} complete cases. "
        f"The Kaiser-Meyer-Olkin measure was "
        f"{overall_kmo:.3f}"
        if overall_kmo
        is not None
        else
        f"A {method_name.lower()} was conducted "
        f"on {p} variables using {n} complete cases. "
        f"The KMO measure was unavailable"
    )


    apa += (
        f", and Bartlett's test of sphericity "
        f"was significant, "
        f"χ²({bartlett['df']}) = "
        f"{bartlett['chi_square']:.2f}, "
        f"{format_p(bartlett['p'])}. "
        f"{selected_count} "
        f"{prefix.lower()}(s) were retained "
        f"with {rotation_used.lower()} rotation."
    )


    tables = [
        {
            "title":
                "Factorability / Data Suitability",

            "columns": [
                "Measure",
                "Statistic",
                "df",
                "p",
                "Assessment",
            ],

            "rows": [
                {
                    "Measure":
                        "Kaiser-Meyer-Olkin",

                    "Statistic":
                        overall_kmo,

                    "df":
                        None,

                    "p":
                        None,

                    "Assessment":
                        kmo_label(
                            overall_kmo
                        ),
                },

                {
                    "Measure":
                        "Bartlett's Test of Sphericity",

                    "Statistic":
                        bartlett[
                            "chi_square"
                        ],

                    "df":
                        bartlett[
                            "df"
                        ],

                    "p":
                        bartlett[
                            "p"
                        ],

                    "Assessment":
                        (
                            "Suitable"
                            if bartlett_status
                            else
                            "Review"
                        ),
                },
            ],
        },

        {
            "title":
                "KMO by Variable",

            "columns": [
                "Variable",
                "KMO",
                "Assessment",
            ],

            "rows":
                kmo_variable_table(
                    variables=(
                        variables
                    ),

                    item_kmo=(
                        item_kmo
                    ),
                ),
        },

        {
            "title":
                "Eigenvalues and Variance Explained",

            "columns": [
                "Component",
                "Eigenvalue",
                "Variance %",
                "Cumulative %",
                "Retain (Kaiser > 1)",
            ],

            "rows":
                variance_table(
                    eigenvalues=(
                        correlation_eigenvalues
                    ),

                    total_variables=(
                        p
                    ),
                ),
        },

        {
            "title":
                "Communalities",

            "columns": [
                "Variable",
                "Communality",
                "Uniqueness",
                "Status",
            ],

            "rows":
                communality_table(
                    variables=(
                        variables
                    ),

                    communalities=(
                        communalities
                    ),
                ),
        },

        {
            "title":
                "Unrotated Loadings",

            "columns":
                loading_columns,

            "rows":
                loading_rows,
        },
    ]


    if (
        rotation_used
        !=
        "None"
    ):

        tables.append({
            "title":
                "Rotated Loadings",

            "columns":
                rotated_columns,

            "rows":
                rotated_rows,
        })


    tables.append({
        "title":
            (
                f"{prefix} Interpretation"
            ),

        "columns": [
            prefix,
            "Variables with Strong Loadings",
        ],

        "rows":
            factor_summary_rows,
    })


    return json_safe({
        "analysis_name":
            method_name,

        "title":
            "EFA / PCA",

        "configuration": {
            "method":
                method,

            "variables":
                variables,

            "n_factors":
                selected_count,

            "automatic_factor_count":
                automatic_count,

            "rotation":
                rotation_used,

            "alpha":
                alpha,

            "loading_threshold":
                loading_threshold,
        },

        "summary": {
            "n":
                n,

            "variables":
                p,

            "kmo":
                overall_kmo,

            "kmo_assessment":
                kmo_label(
                    overall_kmo
                ),

            "bartlett_chi_square":
                bartlett[
                    "chi_square"
                ],

            "bartlett_df":
                bartlett[
                    "df"
                ],

            "bartlett_p":
                bartlett[
                    "p"
                ],

            "retained":
                selected_count,

            "rotation":
                rotation_used,

            "suitable":
                suitability,
        },

        "tables":
            tables,

        "interpretation":
            interpretation,

        "apa":
            apa,

        "metadata": {
            "complete_cases":
                n,

            "number_variables":
                p,

            "method":
                method_name,

            "rotation":
                rotation_used,

            "automatic_factor_count":
                automatic_count,

            "means":
                means.to_dict(),

            "standard_deviations":
                stds.to_dict(),
        },
    })
