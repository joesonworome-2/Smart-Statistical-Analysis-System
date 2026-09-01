import math

from itertools import combinations

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
# P VALUE
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
# EVENT VALUE MATCHING
# ==========================================================

def convert_event_indicator(
    series,
    event_value,
):
    source = (
        series.copy()
    )

    target_text = (
        str(
            event_value
        )
        .strip()
        .lower()
    )

    source_text = (
        source
        .astype(
            str
        )
        .str
        .strip()
        .str
        .lower()
    )

    text_match = (
        source_text
        ==
        target_text
    )

    # ------------------------------------------------------
    # ALSO TRY NUMERIC MATCHING
    # ------------------------------------------------------

    target_numeric = pd.to_numeric(
        pd.Series(
            [
                event_value
            ]
        ),
        errors="coerce",
    ).iloc[
        0
    ]

    source_numeric = pd.to_numeric(
        source,
        errors="coerce",
    )

    if pd.notna(
        target_numeric
    ):
        numeric_match = (
            source_numeric.notna()
            &
            np.isclose(
                source_numeric,
                float(
                    target_numeric
                ),
            )
        )

        matched = (
            text_match
            |
            numeric_match
        )

    else:
        matched = (
            text_match
        )

    event_count = int(
        matched.sum()
    )

    if event_count == 0:
        unique_values = (
            source
            .dropna()
            .astype(
                str
            )
            .unique()
            .tolist()
        )

        preview = (
            ", ".join(
                unique_values[
                    :10
                ]
            )
        )

        raise ValueError(
            (
                f"Event value '{event_value}' "
                f"was not found in the event variable. "
                f"Available values include: {preview}"
            )
        )

    return (
        matched
        .astype(
            int
        )
    )


# ==========================================================
# PREPARE SURVIVAL DATA
# ==========================================================

def prepare_survival_data(
    dataframe,
    duration_variable,
    event_variable,
    event_value,
    group_variable=None,
):
    required = [
        duration_variable,
        event_variable,
    ]

    if group_variable:
        required.append(
            group_variable
        )

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

    # ------------------------------------------------------
    # DURATION MUST BE NUMERIC
    # ------------------------------------------------------

    original_duration_count = int(
        working[
            duration_variable
        ]
        .notna()
        .sum()
    )

    converted_duration = pd.to_numeric(
        working[
            duration_variable
        ],
        errors="coerce",
    )

    numeric_duration_count = int(
        converted_duration
        .notna()
        .sum()
    )

    if original_duration_count > 0:
        numeric_ratio = (
            numeric_duration_count
            /
            original_duration_count
        )

    else:
        numeric_ratio = 0.0

    if numeric_ratio < 0.80:
        raise ValueError(
            (
                f"Duration variable "
                f"'{duration_variable}' is not "
                f"sufficiently numeric. Survival "
                f"analysis requires elapsed time "
                f"such as days, weeks, months, "
                f"hours or years."
            )
        )

    working[
        duration_variable
    ] = (
        converted_duration
    )

    # ------------------------------------------------------
    # REMOVE MISSING
    # ------------------------------------------------------

    subset = [
        duration_variable,
        event_variable,
    ]

    if group_variable:
        subset.append(
            group_variable
        )

    working[
        event_variable
    ] = (
        working[
            event_variable
        ]
        .replace(
            r"^\s*$",
            np.nan,
            regex=True,
        )
    )

    if group_variable:
        working[
            group_variable
        ] = (
            working[
                group_variable
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
            subset=subset
        )
    )

    if len(
        working
    ) < 10:
        raise ValueError(
            (
                "Survival analysis requires at "
                "least 10 complete observations. "
                f"Only {len(working)} complete "
                "observations remained."
            )
        )

    # ------------------------------------------------------
    # NEGATIVE DURATION NOT ALLOWED
    # ------------------------------------------------------

    negative_count = int(
        (
            working[
                duration_variable
            ]
            <
            0
        ).sum()
    )

    if negative_count > 0:
        raise ValueError(
            (
                f"Duration variable contains "
                f"{negative_count} negative value(s). "
                f"Survival time cannot be negative."
            )
        )

    # ------------------------------------------------------
    # EVENT INDICATOR
    # ------------------------------------------------------

    working[
        "__event__"
    ] = (
        convert_event_indicator(
            working[
                event_variable
            ],
            event_value,
        )
    )

    total_events = int(
        working[
            "__event__"
        ].sum()
    )

    if total_events == 0:
        raise ValueError(
            "No observed events were found."
        )

    # ------------------------------------------------------
    # GROUP VARIABLE
    # ------------------------------------------------------

    categories = None

    if group_variable:
        working[
            group_variable
        ] = (
            working[
                group_variable
            ]
            .astype(
                str
            )
        )

        categories = sorted(
            working[
                group_variable
            ]
            .unique()
            .tolist()
        )

        if len(
            categories
        ) < 2:
            raise ValueError(
                "The grouping variable must "
                "contain at least two groups."
            )

        if len(
            categories
        ) > 20:
            raise ValueError(
                (
                    "The grouping variable contains "
                    "more than 20 categories. Select "
                    "a grouping variable with fewer "
                    "levels."
                )
            )

        for category in categories:
            count = int(
                (
                    working[
                        group_variable
                    ]
                    ==
                    category
                ).sum()
            )

            if count < 2:
                raise ValueError(
                    (
                        f"Group '{category}' contains "
                        f"fewer than two observations."
                    )
                )

    return (
        working,
        categories,
    )


# ==========================================================
# LOG-LOG CONFIDENCE INTERVAL
# ==========================================================

def survival_confidence_interval(
    survival,
    greenwood_sum,
    confidence_level,
):
    survival = float(
        survival
    )

    if survival <= 0:
        return (
            0.0,
            0.0,
        )

    if survival >= 1:
        return (
            1.0,
            1.0,
        )

    if greenwood_sum <= 0:
        return (
            survival,
            survival,
        )

    alpha = (
        1
        -
        confidence_level
    )

    z_value = float(
        stats.norm.ppf(
            1
            -
            alpha
            /
            2
        )
    )

    log_survival = (
        math.log(
            survival
        )
    )

    if abs(
        log_survival
    ) < 1e-12:
        return (
            survival,
            survival,
        )

    se_loglog = (
        math.sqrt(
            greenwood_sum
        )
        /
        abs(
            log_survival
        )
    )

    transformed = (
        math.log(
            -log_survival
        )
    )

    lower = math.exp(
        -math.exp(
            transformed
            +
            z_value
            *
            se_loglog
        )
    )

    upper = math.exp(
        -math.exp(
            transformed
            -
            z_value
            *
            se_loglog
        )
    )

    return (
        max(
            0.0,
            min(
                1.0,
                lower,
            ),
        ),

        max(
            0.0,
            min(
                1.0,
                upper,
            ),
        ),
    )


# ==========================================================
# KAPLAN-MEIER
# ==========================================================

def kaplan_meier(
    durations,
    events,
    confidence_level,
    group_name="Overall",
):
    durations = np.asarray(
        durations,
        dtype=float,
    )

    events = np.asarray(
        events,
        dtype=int,
    )

    order = np.argsort(
        durations
    )

    durations = (
        durations[
            order
        ]
    )

    events = (
        events[
            order
        ]
    )

    unique_times = np.unique(
        durations
    )

    survival = 1.0

    greenwood_sum = 0.0

    rows = []

    median_survival = None

    for time in unique_times:
        at_risk = int(
            np.sum(
                durations
                >=
                time
            )
        )

        event_count = int(
            np.sum(
                (
                    durations
                    ==
                    time
                )
                &
                (
                    events
                    ==
                    1
                )
            )
        )

        censored_count = int(
            np.sum(
                (
                    durations
                    ==
                    time
                )
                &
                (
                    events
                    ==
                    0
                )
            )
        )

        if event_count > 0:
            survival = (
                survival
                *
                (
                    1.0
                    -
                    (
                        event_count
                        /
                        at_risk
                    )
                )
            )

            if (
                at_risk
                >
                event_count
            ):
                greenwood_sum += (
                    event_count
                    /
                    (
                        at_risk
                        *
                        (
                            at_risk
                            -
                            event_count
                        )
                    )
                )

            standard_error = (
                survival
                *
                math.sqrt(
                    max(
                        greenwood_sum,
                        0.0,
                    )
                )
            )

            (
                ci_lower,
                ci_upper,
            ) = survival_confidence_interval(
                survival=(
                    survival
                ),

                greenwood_sum=(
                    greenwood_sum
                ),

                confidence_level=(
                    confidence_level
                ),
            )

            rows.append({
                "Group":
                    group_name,

                "Time":
                    float(
                        time
                    ),

                "At Risk":
                    at_risk,

                "Events":
                    event_count,

                "Censored":
                    censored_count,

                "Survival Probability":
                    survival,

                "SE":
                    standard_error,

                "CI Lower":
                    ci_lower,

                "CI Upper":
                    ci_upper,
            })

            if (
                median_survival
                is None
                and
                survival
                <=
                0.50
            ):
                median_survival = float(
                    time
                )

    final_survival = (
        float(
            survival
        )
    )

    # ------------------------------------------------------
    # RESTRICTED MEAN SURVIVAL TIME
    # ------------------------------------------------------

    previous_time = 0.0

    previous_survival = 1.0

    rmst = 0.0

    for row in rows:
        current_time = float(
            row[
                "Time"
            ]
        )

        rmst += (
            current_time
            -
            previous_time
        ) * previous_survival

        previous_time = (
            current_time
        )

        previous_survival = float(
            row[
                "Survival Probability"
            ]
        )

    maximum_time = float(
        np.max(
            durations
        )
    )

    if maximum_time > previous_time:
        rmst += (
            maximum_time
            -
            previous_time
        ) * previous_survival

    return {
        "rows":
            rows,

        "median_survival":
            median_survival,

        "final_survival":
            final_survival,

        "rmst":
            float(
                rmst
            ),

        "max_followup":
            maximum_time,
    }


# ==========================================================
# LOG-RANK COMPONENTS
# ==========================================================

def logrank_components(
    dataframe,
    duration_variable,
    group_variable,
):
    categories = sorted(
        dataframe[
            group_variable
        ]
        .astype(
            str
        )
        .unique()
        .tolist()
    )

    k = len(
        categories
    )

    event_times = sorted(
        dataframe.loc[
            dataframe[
                "__event__"
            ]
            ==
            1,
            duration_variable,
        ]
        .unique()
        .tolist()
    )

    observed = np.zeros(
        k,
        dtype=float,
    )

    expected = np.zeros(
        k,
        dtype=float,
    )

    covariance = np.zeros(
        (
            k,
            k,
        ),
        dtype=float,
    )

    for time in event_times:
        risk_counts = np.zeros(
            k,
            dtype=float,
        )

        event_counts = np.zeros(
            k,
            dtype=float,
        )

        for index, category in enumerate(
            categories
        ):
            group_data = dataframe[
                dataframe[
                    group_variable
                ]
                .astype(
                    str
                )
                ==
                category
            ]

            risk_counts[
                index
            ] = float(
                (
                    group_data[
                        duration_variable
                    ]
                    >=
                    time
                ).sum()
            )

            event_counts[
                index
            ] = float(
                (
                    (
                        group_data[
                            duration_variable
                        ]
                        ==
                        time
                    )
                    &
                    (
                        group_data[
                            "__event__"
                        ]
                        ==
                        1
                    )
                ).sum()
            )

        n_total = float(
            risk_counts.sum()
        )

        d_total = float(
            event_counts.sum()
        )

        if (
            n_total <= 0
            or
            d_total <= 0
        ):
            continue

        observed += (
            event_counts
        )

        expected += (
            d_total
            *
            risk_counts
            /
            n_total
        )

        if n_total <= 1:
            continue

        common = (
            d_total
            *
            (
                n_total
                -
                d_total
            )
            /
            (
                n_total
                *
                n_total
                *
                (
                    n_total
                    -
                    1
                )
            )
        )

        for i in range(
            k
        ):
            covariance[
                i,
                i
            ] += (
                common
                *
                risk_counts[
                    i
                ]
                *
                (
                    n_total
                    -
                    risk_counts[
                        i
                    ]
                )
            )

            for j in range(
                k
            ):
                if i == j:
                    continue

                covariance[
                    i,
                    j
                ] -= (
                    common
                    *
                    risk_counts[
                        i
                    ]
                    *
                    risk_counts[
                        j
                    ]
                )

    return (
        categories,
        observed,
        expected,
        covariance,
    )


# ==========================================================
# LOG-RANK TEST
# ==========================================================

def logrank_test(
    dataframe,
    duration_variable,
    group_variable,
):
    (
        categories,
        observed,
        expected,
        covariance,
    ) = logrank_components(
        dataframe=(
            dataframe
        ),

        duration_variable=(
            duration_variable
        ),

        group_variable=(
            group_variable
        ),
    )

    k = len(
        categories
    )

    degrees_freedom = (
        k
        -
        1
    )

    difference = (
        observed
        -
        expected
    )

    reduced_difference = (
        difference[
            :degrees_freedom
        ]
    )

    reduced_covariance = (
        covariance[
            :degrees_freedom,
            :degrees_freedom,
        ]
    )

    if (
        degrees_freedom <= 0
        or
        np.allclose(
            reduced_covariance,
            0,
        )
    ):
        chi_square = 0.0
        p_value = 1.0

    else:
        inverse_covariance = (
            np.linalg.pinv(
                reduced_covariance
            )
        )

        chi_square = float(
            reduced_difference.T
            @
            inverse_covariance
            @
            reduced_difference
        )

        p_value = float(
            stats.chi2.sf(
                chi_square,
                degrees_freedom,
            )
        )

    contribution_rows = []

    for index, category in enumerate(
        categories
    ):
        contribution_rows.append({
            "Group":
                category,

            "Observed Events":
                float(
                    observed[
                        index
                    ]
                ),

            "Expected Events":
                float(
                    expected[
                        index
                    ]
                ),

            "O - E":
                float(
                    observed[
                        index
                    ]
                    -
                    expected[
                        index
                    ]
                ),
        })

    return {
        "chi_square":
            chi_square,

        "df":
            degrees_freedom,

        "p":
            p_value,

        "contributions":
            contribution_rows,
    }


# ==========================================================
# PAIRWISE LOG-RANK TESTS
# ==========================================================

def pairwise_logrank_tests(
    dataframe,
    duration_variable,
    group_variable,
    alpha,
):
    categories = sorted(
        dataframe[
            group_variable
        ]
        .astype(
            str
        )
        .unique()
        .tolist()
    )

    pairs = list(
        combinations(
            categories,
            2,
        )
    )

    number_of_tests = len(
        pairs
    )

    rows = []

    for (
        first_group,
        second_group,
    ) in pairs:
        subset = dataframe[
            dataframe[
                group_variable
            ]
            .astype(
                str
            )
            .isin(
                [
                    first_group,
                    second_group,
                ]
            )
        ].copy()

        result = (
            logrank_test(
                dataframe=(
                    subset
                ),

                duration_variable=(
                    duration_variable
                ),

                group_variable=(
                    group_variable
                ),
            )
        )

        raw_p = float(
            result[
                "p"
            ]
        )

        adjusted_p = min(
            1.0,
            raw_p
            *
            number_of_tests,
        )

        rows.append({
            "Group 1":
                first_group,

            "Group 2":
                second_group,

            "Chi-Square":
                result[
                    "chi_square"
                ],

            "df":
                result[
                    "df"
                ],

            "p":
                raw_p,

            "Bonferroni p":
                adjusted_p,

            "Significant":
                bool(
                    adjusted_p
                    <
                    alpha
                ),
        })

    return rows


# ==========================================================
# ASSUMPTION / QUALITY CHECKS
# ==========================================================

def build_assumption_checks(
    working,
    duration_variable,
    event_variable,
    group_variable,
    categories,
):
    rows = []

    # ------------------------------------------------------
    # NON-NEGATIVE DURATION
    # ------------------------------------------------------

    negative_count = int(
        (
            working[
                duration_variable
            ]
            <
            0
        ).sum()
    )

    rows.append({
        "Check":
            "Non-negative survival time",

        "Status":
            (
                "Met"
                if negative_count
                ==
                0
                else
                "Review"
            ),

        "Details":
            (
                "All analysed duration values are non-negative."
                if negative_count
                ==
                0
                else
                (
                    f"{negative_count} negative duration "
                    f"value(s) were detected."
                )
            ),
    })

    # ------------------------------------------------------
    # EVENTS AND CENSORING
    # ------------------------------------------------------

    event_count = int(
        working[
            "__event__"
        ].sum()
    )

    censored_count = (
        len(
            working
        )
        -
        event_count
    )

    rows.append({
        "Check":
            "Observed events",

        "Status":
            (
                "Met"
                if event_count
                >
                0
                else
                "Review"
            ),

        "Details":
            (
                f"{event_count} event(s) and "
                f"{censored_count} censored "
                f"observation(s) were analysed."
            ),
    })

    # ------------------------------------------------------
    # GROUP EVENTS
    # ------------------------------------------------------

    if (
        group_variable
        and
        categories
    ):
        for category in categories:
            subset = working[
                working[
                    group_variable
                ]
                ==
                category
            ]

            group_events = int(
                subset[
                    "__event__"
                ].sum()
            )

            rows.append({
                "Check":
                    (
                        f"Events in group: "
                        f"{category}"
                    ),

                "Status":
                    (
                        "Met"
                        if group_events
                        >
                        0
                        else
                        "Review"
                    ),

                "Details":
                    (
                        f"{len(subset)} observation(s), "
                        f"{group_events} event(s)."
                    ),
            })

    # ------------------------------------------------------
    # INDEPENDENT CENSORING
    # ------------------------------------------------------

    rows.append({
        "Check":
            "Independent / non-informative censoring",

        "Status":
            "User review",

        "Details":
            (
                "Kaplan-Meier analysis assumes that "
                "censored observations have future "
                "survival prospects comparable to "
                "participants still under observation. "
                "This depends on study design and cannot "
                "be verified from the dataset alone."
            ),
    })

    # ------------------------------------------------------
    # INDEPENDENCE
    # ------------------------------------------------------

    rows.append({
        "Check":
            "Independence of observations",

        "Status":
            "User review",

        "Details":
            (
                "Observations should be independent. "
                "Repeated measurements or clustered "
                "observations require specialised survival models."
            ),
    })

    # ------------------------------------------------------
    # LOG-RANK NOTE
    # ------------------------------------------------------

    if group_variable:
        rows.append({
            "Check":
                "Log-rank interpretation",

            "Status":
                "User review",

            "Details":
                (
                    "The log-rank test compares entire "
                    "survival distributions and is most "
                    "straightforward to interpret when "
                    "hazard patterns are reasonably similar "
                    "over time. Crossing survival curves "
                    "should be investigated in the "
                    "Visualization module."
                ),
        })

    return rows


# ==========================================================
# GROUP SUMMARY
# ==========================================================

def build_group_summary(
    working,
    duration_variable,
    group_variable,
    categories,
    confidence_level,
):
    rows = []

    km_rows = []

    if group_variable:
        group_names = (
            categories
        )

    else:
        group_names = [
            "Overall"
        ]

    for group_name in group_names:
        if group_variable:
            subset = working[
                working[
                    group_variable
                ]
                ==
                group_name
            ]

        else:
            subset = (
                working
            )

        durations = (
            subset[
                duration_variable
            ]
            .to_numpy(
                dtype=float
            )
        )

        events = (
            subset[
                "__event__"
            ]
            .to_numpy(
                dtype=int
            )
        )

        km_result = (
            kaplan_meier(
                durations=(
                    durations
                ),

                events=(
                    events
                ),

                confidence_level=(
                    confidence_level
                ),

                group_name=(
                    group_name
                ),
            )
        )

        event_count = int(
            events.sum()
        )

        censored_count = (
            len(
                subset
            )
            -
            event_count
        )

        rows.append({
            "Group":
                group_name,

            "N":
                int(
                    len(
                        subset
                    )
                ),

            "Events":
                event_count,

            "Censored":
                censored_count,

            "Event Rate %":
                (
                    event_count
                    /
                    len(
                        subset
                    )
                    *
                    100
                ),

            "Median Survival":
                km_result[
                    "median_survival"
                ],

            "Final Survival Probability":
                km_result[
                    "final_survival"
                ],

            "Restricted Mean Survival":
                km_result[
                    "rmst"
                ],

            "Maximum Follow-up":
                km_result[
                    "max_followup"
                ],
        })

        km_rows.extend(
            km_result[
                "rows"
            ]
        )

    return (
        rows,
        km_rows,
    )


# ==========================================================
# MAIN SURVIVAL ANALYSIS
# ==========================================================

def run_survival_analysis(
    dataframe,
    duration_variable,
    event_variable,
    event_value,
    group_variable=None,
    alpha=0.05,
    confidence_level=0.95,
):
    (
        working,
        categories,
    ) = prepare_survival_data(
        dataframe=(
            dataframe
        ),

        duration_variable=(
            duration_variable
        ),

        event_variable=(
            event_variable
        ),

        event_value=(
            event_value
        ),

        group_variable=(
            group_variable
        ),
    )

    # ------------------------------------------------------
    # OVERALL KM
    # ------------------------------------------------------

    overall_km = (
        kaplan_meier(
            durations=(
                working[
                    duration_variable
                ]
                .to_numpy(
                    dtype=float
                )
            ),

            events=(
                working[
                    "__event__"
                ]
                .to_numpy(
                    dtype=int
                )
            ),

            confidence_level=(
                confidence_level
            ),

            group_name=(
                "Overall"
            ),
        )
    )

    # ------------------------------------------------------
    # GROUP SUMMARY
    # ------------------------------------------------------

    (
        summary_rows,
        km_rows,
    ) = build_group_summary(
        working=(
            working
        ),

        duration_variable=(
            duration_variable
        ),

        group_variable=(
            group_variable
        ),

        categories=(
            categories
        ),

        confidence_level=(
            confidence_level
        ),
    )

    # ------------------------------------------------------
    # LOG-RANK
    # ------------------------------------------------------

    logrank_result = None

    pairwise_rows = []

    if group_variable:
        logrank_result = (
            logrank_test(
                dataframe=(
                    working
                ),

                duration_variable=(
                    duration_variable
                ),

                group_variable=(
                    group_variable
                ),
            )
        )

        if (
            categories
            and
            len(
                categories
            )
            >
            2
        ):
            pairwise_rows = (
                pairwise_logrank_tests(
                    dataframe=(
                        working
                    ),

                    duration_variable=(
                        duration_variable
                    ),

                    group_variable=(
                        group_variable
                    ),

                    alpha=(
                        alpha
                    ),
                )
            )

    # ------------------------------------------------------
    # ASSUMPTIONS
    # ------------------------------------------------------

    assumptions = (
        build_assumption_checks(
            working=(
                working
            ),

            duration_variable=(
                duration_variable
            ),

            event_variable=(
                event_variable
            ),

            group_variable=(
                group_variable
            ),

            categories=(
                categories
            ),
        )
    )

    # ------------------------------------------------------
    # INTERPRETATION
    # ------------------------------------------------------

    n = int(
        len(
            working
        )
    )

    events = int(
        working[
            "__event__"
        ].sum()
    )

    censored = (
        n
        -
        events
    )

    overall_median = (
        overall_km[
            "median_survival"
        ]
    )

    if overall_median is None:
        median_text = (
            "The overall median survival time "
            "was not reached during the observed "
            "follow-up period."
        )

    else:
        median_text = (
            f"The estimated overall median "
            f"survival time was "
            f"{overall_median:.3f}."
        )

    interpretation_parts = [
        (
            f"Survival analysis included {n} "
            f"complete observations, with "
            f"{events} observed event(s) and "
            f"{censored} censored observation(s)."
        ),
        median_text,
    ]

    if (
        group_variable
        and
        logrank_result
    ):
        significant = (
            logrank_result[
                "p"
            ]
            <
            alpha
        )

        if significant:
            interpretation_parts.append(
                (
                    f"The log-rank test indicated "
                    f"that survival distributions "
                    f"differed significantly across "
                    f"levels of {group_variable}, "
                    f"χ²({logrank_result['df']}) = "
                    f"{logrank_result['chi_square']:.3f}, "
                    f"{format_p(logrank_result['p'])}."
                )
            )

        else:
            interpretation_parts.append(
                (
                    f"The log-rank test did not "
                    f"provide statistically significant "
                    f"evidence of different survival "
                    f"distributions across levels of "
                    f"{group_variable}, "
                    f"χ²({logrank_result['df']}) = "
                    f"{logrank_result['chi_square']:.3f}, "
                    f"{format_p(logrank_result['p'])}."
                )
            )

    interpretation_parts.append(
        (
            "Censoring and independence assumptions "
            "should be evaluated using knowledge of "
            "the data-collection process."
        )
    )

    interpretation = (
        " ".join(
            interpretation_parts
        )
    )

    # ------------------------------------------------------
    # APA
    # ------------------------------------------------------

    if (
        group_variable
        and
        logrank_result
    ):
        apa = (
            f"A Kaplan-Meier survival analysis was "
            f"conducted using {duration_variable} as "
            f"the duration measure and "
            f"{event_variable} = {event_value} as the "
            f"event definition. Survival distributions "
            f"across {group_variable} were compared "
            f"using the log-rank test, "
            f"χ²({logrank_result['df']}) = "
            f"{logrank_result['chi_square']:.2f}, "
            f"{format_p(logrank_result['p'])}."
        )

    else:
        apa = (
            f"A Kaplan-Meier survival analysis was "
            f"conducted using {duration_variable} as "
            f"the duration measure and "
            f"{event_variable} = {event_value} as the "
            f"event definition. The analysis included "
            f"{n} observations, including {events} "
            f"observed events and {censored} censored "
            f"observations."
        )

    # ------------------------------------------------------
    # TABLES
    # ------------------------------------------------------

    tables = [
        {
            "title":
                "Survival Summary",

            "columns": [
                "Group",
                "N",
                "Events",
                "Censored",
                "Event Rate %",
                "Median Survival",
                "Final Survival Probability",
                "Restricted Mean Survival",
                "Maximum Follow-up",
            ],

            "rows":
                summary_rows,
        },

        {
            "title":
                "Kaplan-Meier Estimates",

            "columns": [
                "Group",
                "Time",
                "At Risk",
                "Events",
                "Censored",
                "Survival Probability",
                "SE",
                "CI Lower",
                "CI Upper",
            ],

            "rows":
                km_rows,
        },
    ]

    if (
        group_variable
        and
        logrank_result
    ):
        tables.append({
            "title":
                "Log-Rank Test",

            "columns": [
                "Grouping Variable",
                "Chi-Square",
                "df",
                "p",
                "Significant",
            ],

            "rows": [
                {
                    "Grouping Variable":
                        group_variable,

                    "Chi-Square":
                        logrank_result[
                            "chi_square"
                        ],

                    "df":
                        logrank_result[
                            "df"
                        ],

                    "p":
                        logrank_result[
                            "p"
                        ],

                    "Significant":
                        bool(
                            logrank_result[
                                "p"
                            ]
                            <
                            alpha
                        ),
                }
            ],
        })

        tables.append({
            "title":
                "Observed and Expected Events",

            "columns": [
                "Group",
                "Observed Events",
                "Expected Events",
                "O - E",
            ],

            "rows":
                logrank_result[
                    "contributions"
                ],
        })

    if pairwise_rows:
        tables.append({
            "title":
                "Pairwise Log-Rank Comparisons",

            "columns": [
                "Group 1",
                "Group 2",
                "Chi-Square",
                "df",
                "p",
                "Bonferroni p",
                "Significant",
            ],

            "rows":
                pairwise_rows,
        })

    tables.append({
        "title":
            "Survival Analysis Checks",

        "columns": [
            "Check",
            "Status",
            "Details",
        ],

        "rows":
            assumptions,
    })

    return json_safe({
        "analysis_name":
            "Survival Analysis",

        "title":
            "Kaplan-Meier Survival Analysis",

        "configuration": {
            "duration_variable":
                duration_variable,

            "event_variable":
                event_variable,

            "event_value":
                event_value,

            "group_variable":
                group_variable,

            "alpha":
                alpha,

            "confidence_level":
                confidence_level,
        },

        "summary": {
            "n":
                n,

            "events":
                events,

            "censored":
                censored,

            "median_survival":
                overall_median,

            "final_survival_probability":
                overall_km[
                    "final_survival"
                ],

            "restricted_mean_survival":
                overall_km[
                    "rmst"
                ],

            "max_followup":
                overall_km[
                    "max_followup"
                ],
        },

        "logrank_result":
            logrank_result,

        "tables":
            tables,

        "assumptions":
            assumptions,

        "interpretation":
            interpretation,

        "apa":
            apa,

        "metadata": {
            "complete_cases":
                n,

            "group_levels":
                categories,

            "method":
                "Kaplan-Meier",

            "group_comparison":
                (
                    "Log-rank"
                    if group_variable
                    else None
                ),
        },
    })
