import math

import numpy as np
import pandas as pd

from sklearn.cluster import (
    AgglomerativeClustering,
    KMeans,
)

from sklearn.metrics import (
    silhouette_score,
)

from sklearn.preprocessing import (
    StandardScaler,
)


# ==========================================================
# JSON SAFE
# ==========================================================

def json_safe(value):
    if value is None:
        return None

    if isinstance(value, (bool, np.bool_)):
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
# PREPARE DATA
# ==========================================================

def prepare_cluster_data(
    dataframe,
    variables,
):
    missing_columns = [
        variable
        for variable in variables
        if variable not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Dataset does not contain: "
            + ", ".join(missing_columns)
        )

    working = dataframe[variables].copy()

    original_rows = len(working)

    for variable in variables:
        original_non_missing = int(
            working[variable].notna().sum()
        )

        converted = pd.to_numeric(
            working[variable],
            errors="coerce",
        )

        converted_non_missing = int(
            converted.notna().sum()
        )

        ratio = (
            converted_non_missing
            / original_non_missing
            if original_non_missing > 0
            else 0
        )

        if ratio < 0.80:
            raise ValueError(
                f"Variable '{variable}' is not "
                "sufficiently numeric for cluster analysis."
            )

        working[variable] = converted

    working = (
        working
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .dropna()
    )

    complete_rows = len(working)

    if complete_rows < 10:
        raise ValueError(
            "Cluster analysis requires at least "
            "10 complete observations. "
            f"Only {complete_rows} remained."
        )

    for variable in variables:
        if working[variable].nunique() < 2:
            raise ValueError(
                f"Variable '{variable}' is constant "
                "and cannot be used for clustering."
            )

    return {
        "data": working,
        "original_rows": int(original_rows),
        "complete_rows": int(complete_rows),
        "excluded_rows": int(
            original_rows - complete_rows
        ),
    }


# ==========================================================
# FIT CLUSTER MODEL
# ==========================================================

def fit_cluster_model(
    values,
    method,
    n_clusters,
):
    if method == "hierarchical":
        model = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage="ward",
        )

        labels = model.fit_predict(values)

        inertia = None

    else:
        model = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
        )

        labels = model.fit_predict(values)

        inertia = float(
            model.inertia_
        )

    return {
        "labels": labels,
        "inertia": inertia,
    }


# ==========================================================
# AUTOMATIC CLUSTER NUMBER
# ==========================================================

def choose_cluster_count(
    values,
    method,
    max_clusters,
):
    n = values.shape[0]

    upper = min(
        max_clusters,
        n - 1,
    )

    if upper < 2:
        raise ValueError(
            "Not enough observations to determine clusters."
        )

    candidates = []

    best_k = None
    best_score = -1.0

    for k in range(2, upper + 1):
        try:
            fitted = fit_cluster_model(
                values=values,
                method=method,
                n_clusters=k,
            )

            labels = fitted["labels"]

            unique_labels = np.unique(labels)

            if len(unique_labels) < 2:
                continue

            score = float(
                silhouette_score(
                    values,
                    labels,
                )
            )

            candidates.append({
                "Clusters": k,
                "Silhouette Score": score,
                "Inertia": fitted["inertia"],
            })

            if score > best_score:
                best_score = score
                best_k = k

        except Exception:
            continue

    if best_k is None:
        raise ValueError(
            "SSAS could not automatically determine "
            "a suitable number of clusters."
        )

    return {
        "best_k": best_k,
        "best_score": best_score,
        "candidates": candidates,
    }


# ==========================================================
# SILHOUETTE ASSESSMENT
# ==========================================================

def silhouette_label(value):
    if value is None:
        return "Unavailable"

    if value >= 0.70:
        return "Strong"

    if value >= 0.50:
        return "Good"

    if value >= 0.25:
        return "Moderate"

    return "Weak"


# ==========================================================
# CLUSTER SIZE TABLE
# ==========================================================

def build_cluster_sizes(labels):
    unique, counts = np.unique(
        labels,
        return_counts=True,
    )

    total = len(labels)

    rows = []

    for label, count in zip(
        unique,
        counts,
    ):
        rows.append({
            "Cluster": int(label + 1),
            "N": int(count),
            "Percentage": float(
                count / total * 100
            ),
        })

    return rows


# ==========================================================
# CENTERS
# ==========================================================

def build_cluster_centers(
    working,
    labels,
    variables,
):
    profiled = working.copy()

    profiled["_cluster"] = (
        labels + 1
    )

    grouped = (
        profiled
        .groupby("_cluster")[variables]
        .mean()
    )

    rows = []

    for cluster_id, values in grouped.iterrows():
        row = {
            "Cluster": int(cluster_id)
        }

        for variable in variables:
            row[variable] = float(
                values[variable]
            )

        rows.append(row)

    return {
        "columns": [
            "Cluster",
            *variables,
        ],
        "rows": rows,
    }


# ==========================================================
# STANDARDIZED CENTERS
# ==========================================================

def build_standardized_centers(
    standardized_values,
    labels,
    variables,
):
    frame = pd.DataFrame(
        standardized_values,
        columns=variables,
    )

    frame["_cluster"] = (
        labels + 1
    )

    grouped = (
        frame
        .groupby("_cluster")[variables]
        .mean()
    )

    rows = []

    for cluster_id, values in grouped.iterrows():
        row = {
            "Cluster": int(cluster_id)
        }

        for variable in variables:
            row[variable] = float(
                values[variable]
            )

        rows.append(row)

    return {
        "columns": [
            "Cluster",
            *variables,
        ],
        "rows": rows,
    }


# ==========================================================
# VARIABLE SEPARATION
# ==========================================================

def build_variable_separation(
    standardized_values,
    labels,
    variables,
):
    frame = pd.DataFrame(
        standardized_values,
        columns=variables,
    )

    frame["_cluster"] = labels

    rows = []

    for variable in variables:
        overall_mean = float(
            frame[variable].mean()
        )

        total_ss = float(
            (
                (
                    frame[variable]
                    - overall_mean
                )
                ** 2
            ).sum()
        )

        between_ss = 0.0

        for _, group in frame.groupby(
            "_cluster"
        ):
            group_mean = float(
                group[variable].mean()
            )

            between_ss += (
                len(group)
                *
                (
                    group_mean
                    - overall_mean
                )
                ** 2
            )

        proportion = (
            between_ss / total_ss
            if total_ss > 0
            else 0.0
        )

        rows.append({
            "Variable": variable,
            "Between-Cluster Variance Proportion":
                proportion,
            "Contribution %":
                proportion * 100,
            "Assessment":
                (
                    "Strong"
                    if proportion >= 0.50
                    else
                    "Moderate"
                    if proportion >= 0.25
                    else
                    "Low"
                ),
        })

    rows.sort(
        key=lambda row:
            row[
                "Between-Cluster Variance Proportion"
            ],
        reverse=True,
    )

    return rows


# ==========================================================
# ASSIGNMENTS PREVIEW
# ==========================================================

def build_assignment_preview(
    working,
    labels,
    variables,
    limit=100,
):
    rows = []

    indexes = working.index.tolist()

    for position in range(
        min(
            len(working),
            limit,
        )
    ):
        row = {
            "Row": int(
                indexes[position]
            ),
            "Cluster": int(
                labels[position] + 1
            ),
        }

        for variable in variables:
            row[variable] = float(
                working.iloc[
                    position
                ][variable]
            )

        rows.append(row)

    return {
        "columns": [
            "Row",
            "Cluster",
            *variables,
        ],
        "rows": rows,
    }


# ==========================================================
# CLUSTER PROFILE INTERPRETATION
# ==========================================================

def build_cluster_profiles(
    standardized_centers,
    variables,
):
    rows = []

    for row in standardized_centers:
        cluster_id = row["Cluster"]

        high = []
        low = []

        for variable in variables:
            value = float(
                row[variable]
            )

            if value >= 0.50:
                high.append(variable)

            elif value <= -0.50:
                low.append(variable)

        high_text = (
            ", ".join(high)
            if high
            else "No strongly above-average variables"
        )

        low_text = (
            ", ".join(low)
            if low
            else "No strongly below-average variables"
        )

        rows.append({
            "Cluster": cluster_id,
            "Above Average": high_text,
            "Below Average": low_text,
        })

    return rows


# ==========================================================
# MAIN ENGINE
# ==========================================================

def run_cluster_analysis(
    dataframe,
    variables,
    method="kmeans",
    n_clusters=None,
    standardize=True,
    max_auto_clusters=8,
):
    prepared = prepare_cluster_data(
        dataframe=dataframe,
        variables=variables,
    )

    working = prepared["data"]

    raw_values = working[
        variables
    ].to_numpy(
        dtype=float
    )

    scaler = StandardScaler()

    standardized_values = (
        scaler.fit_transform(
            raw_values
        )
    )

    values_for_model = (
        standardized_values
        if standardize
        else raw_values
    )

    automatic = (
        n_clusters is None
    )

    auto_result = None

    if automatic:
        auto_result = choose_cluster_count(
            values=values_for_model,
            method=method,
            max_clusters=max_auto_clusters,
        )

        selected_k = int(
            auto_result["best_k"]
        )

    else:
        selected_k = int(
            n_clusters
        )

    if selected_k >= len(working):
        raise ValueError(
            "The number of clusters must be smaller "
            "than the number of observations."
        )

    fitted = fit_cluster_model(
        values=values_for_model,
        method=method,
        n_clusters=selected_k,
    )

    labels = fitted["labels"]

    unique_labels = np.unique(
        labels
    )

    if len(unique_labels) < 2:
        raise ValueError(
            "The clustering algorithm produced "
            "fewer than two clusters."
        )

    silhouette = float(
        silhouette_score(
            values_for_model,
            labels,
        )
    )

    cluster_sizes = build_cluster_sizes(
        labels
    )

    centers = build_cluster_centers(
        working=working,
        labels=labels,
        variables=variables,
    )

    standardized_centers = (
        build_standardized_centers(
            standardized_values=(
                standardized_values
            ),
            labels=labels,
            variables=variables,
        )
    )

    variable_separation = (
        build_variable_separation(
            standardized_values=(
                standardized_values
            ),
            labels=labels,
            variables=variables,
        )
    )

    assignments = (
        build_assignment_preview(
            working=working,
            labels=labels,
            variables=variables,
        )
    )

    profiles = build_cluster_profiles(
        standardized_centers=(
            standardized_centers[
                "rows"
            ]
        ),
        variables=variables,
    )

    method_name = (
        "K-Means Clustering"
        if method == "kmeans"
        else
        "Hierarchical Agglomerative Clustering"
    )

    assessment = silhouette_label(
        silhouette
    )

    strongest_variables = [
        row["Variable"]
        for row in variable_separation[:3]
    ]

    strongest_text = (
        ", ".join(
            strongest_variables
        )
        if strongest_variables
        else
        "none"
    )

    interpretation = (
        f"{method_name} was performed using "
        f"{len(variables)} variables and "
        f"{len(working)} complete observations. "
        f"SSAS identified {selected_k} clusters. "
        f"The overall silhouette score was "
        f"{silhouette:.3f}, indicating a "
        f"{assessment.lower()} degree of cluster "
        f"separation under the current configuration. "
        f"The variables contributing most strongly "
        f"to differences between clusters were "
        f"{strongest_text}. "
        f"Cluster centers should be interpreted "
        f"as descriptive profiles rather than "
        f"causal or predefined population categories."
    )

    apa = (
        f"A {method_name.lower()} was conducted "
        f"using {len(variables)} variables and "
        f"{len(working)} complete observations. "
        f"A {selected_k}-cluster solution was "
        f"obtained with an average silhouette "
        f"coefficient of {silhouette:.3f}."
    )

    tables = []

    if auto_result is not None:
        tables.append({
            "title":
                "Automatic Cluster Selection",

            "columns": [
                "Clusters",
                "Silhouette Score",
                "Inertia",
            ],

            "rows":
                auto_result[
                    "candidates"
                ],
        })

    tables.extend([
        {
            "title":
                "Cluster Summary",

            "columns": [
                "Method",
                "Observations",
                "Variables",
                "Clusters",
                "Silhouette Score",
                "Assessment",
                "Inertia",
            ],

            "rows": [
                {
                    "Method":
                        method_name,

                    "Observations":
                        int(
                            len(
                                working
                            )
                        ),

                    "Variables":
                        len(
                            variables
                        ),

                    "Clusters":
                        selected_k,

                    "Silhouette Score":
                        silhouette,

                    "Assessment":
                        assessment,

                    "Inertia":
                        fitted[
                            "inertia"
                        ],
                }
            ],
        },

        {
            "title":
                "Cluster Sizes",

            "columns": [
                "Cluster",
                "N",
                "Percentage",
            ],

            "rows":
                cluster_sizes,
        },

        {
            "title":
                "Cluster Centers",

            "columns":
                centers[
                    "columns"
                ],

            "rows":
                centers[
                    "rows"
                ],
        },

        {
            "title":
                "Standardized Cluster Profiles",

            "columns":
                standardized_centers[
                    "columns"
                ],

            "rows":
                standardized_centers[
                    "rows"
                ],
        },

        {
            "title":
                "Cluster Profile Interpretation",

            "columns": [
                "Cluster",
                "Above Average",
                "Below Average",
            ],

            "rows":
                profiles,
        },

        {
            "title":
                "Variable Contribution to Cluster Separation",

            "columns": [
                "Variable",
                "Between-Cluster Variance Proportion",
                "Contribution %",
                "Assessment",
            ],

            "rows":
                variable_separation,
        },

        {
            "title":
                "Cluster Assignment Preview",

            "columns":
                assignments[
                    "columns"
                ],

            "rows":
                assignments[
                    "rows"
                ],
        },
    ])

    return json_safe({
        "analysis_name":
            "Cluster Analysis",

        "title":
            method_name,

        "configuration": {
            "variables":
                variables,

            "method":
                method,

            "n_clusters":
                selected_k,

            "automatic_clusters":
                automatic,

            "standardize":
                standardize,

            "max_auto_clusters":
                max_auto_clusters,
        },

        "summary": {
            "n":
                int(
                    len(
                        working
                    )
                ),

            "variables":
                len(
                    variables
                ),

            "clusters":
                selected_k,

            "silhouette_score":
                silhouette,

            "assessment":
                assessment,

            "inertia":
                fitted[
                    "inertia"
                ],

            "excluded_cases":
                prepared[
                    "excluded_rows"
                ],
        },

        "tables":
            tables,

        "interpretation":
            interpretation,

        "apa":
            apa,

        "metadata": {
            "complete_cases":
                prepared[
                    "complete_rows"
                ],

            "excluded_cases":
                prepared[
                    "excluded_rows"
                ],

            "assignment_preview_rows":
                len(
                    assignments[
                        "rows"
                    ]
                ),

            "method":
                method_name,

            "standardized":
                standardize,
        },
    })
