import math

import numpy as np
import pandas as pd

from scipy import stats


# ==========================================================
# GENERAL HELPERS
# ==========================================================

def clean_number(value):
    if value is None:
        return None

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(
        value,
        (
            np.floating,
            float,
        ),
    ):
        number = float(value)

        if (
            math.isnan(number)
            or math.isinf(number)
        ):
            return None

        return number

    return value

def significance_decision(
    p_value,
    alpha,
):
    significant = bool(
        p_value < alpha
    )

    return {
        "alpha": float(
            alpha
        ),
        "significant":
            significant,

        "decision": (
            "Reject the null hypothesis"
            if significant
            else (
                "Fail to reject "
                "the null hypothesis"
            )
        ),
    }


def numeric_series(series):
    """
    Convert numeric columns to numbers.

    If the column is a date column, convert dates to
    ordinal day values so interval calculations are possible.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    if numeric.notna().sum() > 0:
        return numeric.dropna()

    dates = pd.to_datetime(
        series,
        errors="coerce",
    )

    dates = dates.dropna()

    if dates.empty:
        return pd.Series(
            dtype=float
        )

    return (
        dates.astype("int64")
        / 86_400_000_000_000
    )


def normality_check(
    values,
    alpha=0.05,
):
    values = pd.Series(
        values
    ).dropna()

    if len(values) < 3:
        return {
            "statistic": None,
            "p_value": None,
            "normal": None,
            "status": (
                "Insufficient observations"
            ),
        }

    sample = values

    if len(sample) > 5000:
        sample = sample.sample(
            5000,
            random_state=42,
        )

    statistic, p_value = (
        stats.shapiro(sample)
    )

    return {
        "statistic": clean_number(
            statistic
        ),
        "p_value": clean_number(
            p_value
        ),
        "normal": bool(
            p_value >= alpha
        ),
        "status": (
            "Assumption met"
            if p_value >= alpha
            else "Assumption not met"
        ),
    }


def significance_decision(
    p_value,
    alpha,
):
    significant = bool(
        p_value < alpha
    )

    return {
        "alpha": float(
            alpha
        ),
        "significant":
            significant,

        "decision": (
            "Reject the null hypothesis"
            if significant
            else (
                "Fail to reject "
                "the null hypothesis"
            )
        ),
    }


def sem(values):
    if len(values) < 2:
        return None

    return clean_number(
        stats.sem(values)
    )


def effect_magnitude(
    value,
):
    if value is None:
        return None

    absolute = abs(value)

    if absolute < 0.2:
        return "Negligible"

    if absolute < 0.5:
        return "Small"

    if absolute < 0.8:
        return "Medium"

    return "Large"


def eta_magnitude(value):
    if value is None:
        return None

    if value < 0.01:
        return "Negligible"

    if value < 0.06:
        return "Small"

    if value < 0.14:
        return "Medium"

    return "Large"


def alternative_phrase(
    alternative,
):
    if alternative == "greater":
        return "greater than"

    if alternative == "less":
        return "less than"

    return "different from"


# ==========================================================
# ONE-SAMPLE T TEST
# ==========================================================

def one_sample_t(
    df,
    variable,
    test_value,
    alternative,
    alpha,
):
    x = numeric_series(
        df[variable]
    )

    if len(x) < 2:
        raise ValueError(
            "At least two valid observations are required."
        )

    statistic, p_value = (
        stats.ttest_1samp(
            x,
            popmean=test_value,
            alternative=alternative,
        )
    )

    mean = x.mean()
    std = x.std(ddof=1)
    standard_error = (
        stats.sem(x)
    )

    mean_difference = (
        mean - test_value
    )

    confidence = (
        1 - alpha
    )

    interval = stats.t.interval(
        confidence,
        df=len(x) - 1,
        loc=mean_difference,
        scale=standard_error,
    )

    cohen_d = (
        mean_difference / std
        if std != 0
        else None
    )

    normality = normality_check(
        x,
        alpha,
    )

    decision = (
        significance_decision(
            p_value,
            alpha,
        )
    )

    if alternative == "two-sided":
        null_text = (
            f"The population mean of "
            f"{variable} is equal to "
            f"{test_value}."
        )

        alternative_text = (
            f"The population mean of "
            f"{variable} is different "
            f"from {test_value}."
        )

    elif alternative == "greater":
        null_text = (
            f"The population mean of "
            f"{variable} is less than "
            f"or equal to {test_value}."
        )

        alternative_text = (
            f"The population mean of "
            f"{variable} is greater "
            f"than {test_value}."
        )

    else:
        null_text = (
            f"The population mean of "
            f"{variable} is greater than "
            f"or equal to {test_value}."
        )

        alternative_text = (
            f"The population mean of "
            f"{variable} is less than "
            f"{test_value}."
        )

    interpretation = (
        f"The one-sample t-test produced "
        f"t({len(x) - 1}) = "
        f"{statistic:.4f}, "
        f"p = {p_value:.5f}. "
        f"At α = {alpha}, SSAS will "
        f"{'reject' if p_value < alpha else 'not reject'} "
        f"the null hypothesis."
    )

    apa = (
        f"A one-sample t-test showed that "
        f"{variable} (M = {mean:.2f}, "
        f"SD = {std:.2f}) "
        f"{'differed significantly' if p_value < alpha else 'did not differ significantly'} "
        f"from {test_value}, "
        f"t({len(x) - 1}) = "
        f"{statistic:.2f}, "
        f"p = {p_value:.3f}."
    )

    return {
        "test_key": "one_sample_t",
        "test_name": "One-Sample t-Test",
        "family": "parametric",
        "hypotheses": {
            "null": null_text,
            "alternative": (
                alternative_text
            ),
        },
        "tables": [
            {
                "title": "Statistics",
                "columns": [
                    "Variable",
                    "n",
                    "Mean",
                    "Std. Deviation",
                    "Std. Error Mean",
                ],
                "rows": [
                    {
                        "Variable": variable,
                        "n": len(x),
                        "Mean": clean_number(
                            mean
                        ),
                        "Std. Deviation": (
                            clean_number(std)
                        ),
                        "Std. Error Mean": (
                            clean_number(
                                standard_error
                            )
                        ),
                    }
                ],
            },
            {
                "title": "One-Sample Test",
                "columns": [
                    "Variable",
                    "Test Value",
                    "Mean Difference",
                    "t",
                    "df",
                    "p-value",
                    "CI Lower",
                    "CI Upper",
                    "Cohen's d",
                    "Effect",
                ],
                "rows": [
                    {
                        "Variable": variable,
                        "Test Value": (
                            test_value
                        ),
                        "Mean Difference": (
                            clean_number(
                                mean_difference
                            )
                        ),
                        "t": clean_number(
                            statistic
                        ),
                        "df": len(x) - 1,
                        "p-value": (
                            clean_number(
                                p_value
                            )
                        ),
                        "CI Lower": (
                            clean_number(
                                interval[0]
                            )
                        ),
                        "CI Upper": (
                            clean_number(
                                interval[1]
                            )
                        ),
                        "Cohen's d": (
                            clean_number(
                                cohen_d
                            )
                        ),
                        "Effect": (
                            effect_magnitude(
                                cohen_d
                            )
                        ),
                    }
                ],
            },
        ],
        "assumptions": [
            {
                "Assumption": "Normality",
                "Check": (
                    "Shapiro-Wilk"
                ),
                "Statistic": (
                    normality[
                        "statistic"
                    ]
                ),
                "p-value": (
                    normality[
                        "p_value"
                    ]
                ),
                "Status": (
                    normality[
                        "status"
                    ]
                ),
            }
        ],
        "decision": decision,
        "interpretation": interpretation,
        "apa": apa,
    }


# ==========================================================
# ONE-SAMPLE WILCOXON
# ==========================================================

def one_sample_wilcoxon(
    df,
    variable,
    test_value,
    alternative,
    alpha,
):
    x = numeric_series(
        df[variable]
    )

    differences = (
        x - test_value
    )

    differences = differences[
        differences != 0
    ]

    if len(differences) < 2:
        raise ValueError(
            "Not enough non-zero differences for the Wilcoxon test."
        )

    statistic, p_value = (
        stats.wilcoxon(
            differences,
            alternative=alternative,
        )
    )

    decision = (
        significance_decision(
            p_value,
            alpha,
        )
    )

    if alternative == "two-sided":
        alt_text = "different from"
    elif alternative == "greater":
        alt_text = "greater than"
    else:
        alt_text = "less than"

    interpretation = (
        f"The one-sample Wilcoxon "
        f"signed-rank test produced "
        f"W = {statistic:.4f}, "
        f"p = {p_value:.5f}. "
        f"The median of {variable} "
        f"is {'statistically significantly ' if p_value < alpha else 'not statistically significantly '}"
        f"{alt_text} {test_value}."
    )

    return {
        "test_key": (
            "one_sample_wilcoxon"
        ),
        "test_name": (
            "One-Sample Wilcoxon "
            "Signed-Rank Test"
        ),
        "family": (
            "nonparametric"
        ),
        "hypotheses": {
            "null": (
                f"The population median "
                f"of {variable} is equal "
                f"to {test_value}."
            ),
            "alternative": (
                f"The population median "
                f"of {variable} is "
                f"{alt_text} "
                f"{test_value}."
            ),
        },
        "tables": [
            {
                "title": "Statistics",
                "columns": [
                    "Variable",
                    "n",
                    "Median",
                    "Test Value",
                ],
                "rows": [
                    {
                        "Variable": variable,
                        "n": len(x),
                        "Median": (
                            clean_number(
                                x.median()
                            )
                        ),
                        "Test Value": (
                            test_value
                        ),
                    }
                ],
            },
            {
                "title": (
                    "Wilcoxon Test"
                ),
                "columns": [
                    "Variable",
                    "W",
                    "p-value",
                    "Decision",
                ],
                "rows": [
                    {
                        "Variable": variable,
                        "W": clean_number(
                            statistic
                        ),
                        "p-value": (
                            clean_number(
                                p_value
                            )
                        ),
                        "Decision": (
                            decision[
                                "decision"
                            ]
                        ),
                    }
                ],
            },
        ],
        "assumptions": [
            {
                "Assumption": (
                    "Paired differences "
                    "are symmetrically "
                    "distributed"
                ),
                "Check": (
                    "Study / distribution "
                    "review"
                ),
                "Statistic": None,
                "p-value": None,
                "Status": (
                    "Review before "
                    "interpretation"
                ),
            }
        ],
        "decision": decision,
        "interpretation": (
            interpretation
        ),
        "apa": (
            f"A Wilcoxon signed-rank "
            f"test indicated "
            f"{'a significant' if p_value < alpha else 'no significant'} "
            f"difference from "
            f"{test_value}, "
            f"W = {statistic:.2f}, "
            f"p = {p_value:.3f}."
        ),
    }


# ==========================================================
# PAIRED T TEST
# ==========================================================

def paired_t(
    df,
    variable1,
    variable2,
    alternative,
    alpha,
):
    paired = pd.DataFrame({
        variable1: numeric_series(
            df[variable1]
        ),
        variable2: numeric_series(
            df[variable2]
        ),
    }).dropna()

    if len(paired) < 2:
        raise ValueError(
            "At least two paired observations are required."
        )

    x = paired[variable1]
    y = paired[variable2]

    statistic, p_value = (
        stats.ttest_rel(
            x,
            y,
            alternative=alternative,
        )
    )

    differences = x - y

    std_difference = (
        differences.std(ddof=1)
    )

    cohen_dz = (
        differences.mean()
        / std_difference
        if std_difference != 0
        else None
    )

    normality = normality_check(
        differences,
        alpha,
    )

    decision = (
        significance_decision(
            p_value,
            alpha,
        )
    )

    return {
        "test_key": "paired_t",
        "test_name": (
            "Paired Samples t-Test"
        ),
        "family": "parametric",
        "hypotheses": {
            "null": (
                f"The population mean "
                f"difference between "
                f"{variable1} and "
                f"{variable2} is zero."
            ),
            "alternative": (
                f"The population mean "
                f"difference between "
                f"{variable1} and "
                f"{variable2} is "
                f"{alternative_phrase(alternative)} "
                f"zero."
            ),
        },
        "tables": [
            {
                "title": (
                    "Paired Samples Statistics"
                ),
                "columns": [
                    "Variable",
                    "n",
                    "Mean",
                    "Std. Deviation",
                    "Std. Error Mean",
                ],
                "rows": [
                    {
                        "Variable": variable1,
                        "n": len(x),
                        "Mean": (
                            clean_number(
                                x.mean()
                            )
                        ),
                        "Std. Deviation": (
                            clean_number(
                                x.std(
                                    ddof=1
                                )
                            )
                        ),
                        "Std. Error Mean": (
                            sem(x)
                        ),
                    },
                    {
                        "Variable": variable2,
                        "n": len(y),
                        "Mean": (
                            clean_number(
                                y.mean()
                            )
                        ),
                        "Std. Deviation": (
                            clean_number(
                                y.std(
                                    ddof=1
                                )
                            )
                        ),
                        "Std. Error Mean": (
                            sem(y)
                        ),
                    },
                ],
            },
            {
                "title": (
                    "Paired Samples Test"
                ),
                "columns": [
                    "Pair",
                    "Mean Difference",
                    "t",
                    "df",
                    "p-value",
                    "Cohen's dz",
                    "Effect",
                ],
                "rows": [
                    {
                        "Pair": (
                            f"{variable1} - "
                            f"{variable2}"
                        ),
                        "Mean Difference": (
                            clean_number(
                                differences.mean()
                            )
                        ),
                        "t": (
                            clean_number(
                                statistic
                            )
                        ),
                        "df": len(
                            paired
                        ) - 1,
                        "p-value": (
                            clean_number(
                                p_value
                            )
                        ),
                        "Cohen's dz": (
                            clean_number(
                                cohen_dz
                            )
                        ),
                        "Effect": (
                            effect_magnitude(
                                cohen_dz
                            )
                        ),
                    }
                ],
            },
        ],
        "assumptions": [
            {
                "Assumption": (
                    "Normality of paired "
                    "differences"
                ),
                "Check": (
                    "Shapiro-Wilk"
                ),
                "Statistic": (
                    normality[
                        "statistic"
                    ]
                ),
                "p-value": (
                    normality[
                        "p_value"
                    ]
                ),
                "Status": (
                    normality[
                        "status"
                    ]
                ),
            },
            {
                "Assumption": (
                    "Observations are paired"
                ),
                "Check": (
                    "Study design"
                ),
                "Statistic": None,
                "p-value": None,
                "Status": (
                    "User responsibility"
                ),
            },
        ],
        "decision": decision,
        "interpretation": (
            f"The paired samples t-test "
            f"produced t({len(paired) - 1}) "
            f"= {statistic:.4f}, "
            f"p = {p_value:.5f}."
        ),
        "apa": (
            f"A paired-samples t-test "
            f"{'showed a significant' if p_value < alpha else 'did not show a significant'} "
            f"difference between "
            f"{variable1} and {variable2}, "
            f"t({len(paired) - 1}) = "
            f"{statistic:.2f}, "
            f"p = {p_value:.3f}."
        ),
    }


# ==========================================================
# PAIRED WILCOXON
# ==========================================================

def paired_wilcoxon(
    df,
    variable1,
    variable2,
    alternative,
    alpha,
):
    paired = df[
        [
            variable1,
            variable2,
        ]
    ].copy()

    paired[variable1] = (
        pd.to_numeric(
            paired[variable1],
            errors="coerce",
        )
    )

    paired[variable2] = (
        pd.to_numeric(
            paired[variable2],
            errors="coerce",
        )
    )

    paired = paired.dropna()

    if len(paired) < 2:
        raise ValueError(
            "At least two paired observations are required."
        )

    statistic, p_value = (
        stats.wilcoxon(
            paired[variable1],
            paired[variable2],
            alternative=alternative,
        )
    )

    decision = (
        significance_decision(
            p_value,
            alpha,
        )
    )

    return {
        "test_key": (
            "paired_wilcoxon"
        ),
        "test_name": (
            "Wilcoxon Signed-Rank Test"
        ),
        "family": (
            "nonparametric"
        ),
        "hypotheses": {
            "null": (
                f"There is no median "
                f"difference between "
                f"{variable1} and "
                f"{variable2}."
            ),
            "alternative": (
                f"There is a population "
                f"difference between "
                f"{variable1} and "
                f"{variable2}."
            ),
        },
        "tables": [
            {
                "title": (
                    "Paired Statistics"
                ),
                "columns": [
                    "Variable",
                    "n",
                    "Median",
                ],
                "rows": [
                    {
                        "Variable": variable1,
                        "n": len(paired),
                        "Median": (
                            clean_number(
                                paired[
                                    variable1
                                ].median()
                            )
                        ),
                    },
                    {
                        "Variable": variable2,
                        "n": len(paired),
                        "Median": (
                            clean_number(
                                paired[
                                    variable2
                                ].median()
                            )
                        ),
                    },
                ],
            },
            {
                "title": (
                    "Wilcoxon Test"
                ),
                "columns": [
                    "Pair",
                    "W",
                    "p-value",
                    "Decision",
                ],
                "rows": [
                    {
                        "Pair": (
                            f"{variable1} - "
                            f"{variable2}"
                        ),
                        "W": (
                            clean_number(
                                statistic
                            )
                        ),
                        "p-value": (
                            clean_number(
                                p_value
                            )
                        ),
                        "Decision": (
                            decision[
                                "decision"
                            ]
                        ),
                    }
                ],
            },
        ],
        "assumptions": [
            {
                "Assumption": (
                    "Paired observations"
                ),
                "Check": "Study design",
                "Statistic": None,
                "p-value": None,
                "Status": (
                    "User responsibility"
                ),
            }
        ],
        "decision": decision,
        "interpretation": (
            f"The Wilcoxon signed-rank "
            f"test produced "
            f"W = {statistic:.4f}, "
            f"p = {p_value:.5f}."
        ),
        "apa": (
            f"A Wilcoxon signed-rank "
            f"test "
            f"{'identified a significant' if p_value < alpha else 'did not identify a significant'} "
            f"difference between "
            f"{variable1} and "
            f"{variable2}, "
            f"W = {statistic:.2f}, "
            f"p = {p_value:.3f}."
        ),
    }


# ==========================================================
# INDEPENDENT T TEST
# ==========================================================

def independent_t(
    df,
    variable,
    group_variable,
    alternative,
    alpha,
):
    working = df[
        [
            variable,
            group_variable,
        ]
    ].copy()

    working[variable] = (
        pd.to_numeric(
            working[variable],
            errors="coerce",
        )
    )

    working = working.dropna()

    groups = sorted(
        working[
            group_variable
        ].unique().tolist(),
        key=lambda value: str(value),
    )

    if len(groups) != 2:
        raise ValueError(
            "Independent t-test requires exactly two groups."
        )

    group1 = groups[0]
    group2 = groups[1]

    x = working.loc[
        working[
            group_variable
        ] == group1,
        variable,
    ]

    y = working.loc[
        working[
            group_variable
        ] == group2,
        variable,
    ]

    levene_stat, levene_p = (
        stats.levene(
            x,
            y,
        )
    )

    equal_var = bool(
        levene_p >= alpha
    )

    statistic, p_value = (
        stats.ttest_ind(
            x,
            y,
            equal_var=equal_var,
            alternative=alternative,
        )
    )

    pooled_sd = math.sqrt(
        (
            (
                len(x) - 1
            )
            * x.var(ddof=1)
            +
            (
                len(y) - 1
            )
            * y.var(ddof=1)
        )
        /
        (
            len(x)
            + len(y)
            - 2
        )
    )

    cohen_d = (
        (
            x.mean()
            - y.mean()
        )
        / pooled_sd
        if pooled_sd != 0
        else None
    )

    norm1 = normality_check(
        x,
        alpha,
    )

    norm2 = normality_check(
        y,
        alpha,
    )

    decision = (
        significance_decision(
            p_value,
            alpha,
        )
    )

    return {
        "test_key": (
            "independent_t"
        ),
        "test_name": (
            "Independent Samples "
            "t-Test"
        ),
        "family": "parametric",
        "hypotheses": {
            "null": (
                f"The population mean "
                f"of {variable} is equal "
                f"for {group1} and "
                f"{group2}."
            ),
            "alternative": (
                f"The population mean "
                f"of {variable} differs "
                f"between {group1} and "
                f"{group2}."
            ),
        },
        "tables": [
            {
                "title": (
                    "Group Statistics"
                ),
                "columns": [
                    group_variable,
                    "n",
                    "Mean",
                    "Std. Deviation",
                    "Std. Error Mean",
                ],
                "rows": [
                    {
                        group_variable: (
                            str(group1)
                        ),
                        "n": len(x),
                        "Mean": (
                            clean_number(
                                x.mean()
                            )
                        ),
                        "Std. Deviation": (
                            clean_number(
                                x.std(
                                    ddof=1
                                )
                            )
                        ),
                        "Std. Error Mean": (
                            sem(x)
                        ),
                    },
                    {
                        group_variable: (
                            str(group2)
                        ),
                        "n": len(y),
                        "Mean": (
                            clean_number(
                                y.mean()
                            )
                        ),
                        "Std. Deviation": (
                            clean_number(
                                y.std(
                                    ddof=1
                                )
                            )
                        ),
                        "Std. Error Mean": (
                            sem(y)
                        ),
                    },
                ],
            },
            {
                "title": (
                    "Independent Samples Test"
                ),
                "columns": [
                    "Variable",
                    "Method",
                    "t",
                    "p-value",
                    "Cohen's d",
                    "Effect",
                ],
                "rows": [
                    {
                        "Variable": variable,
                        "Method": (
                            "Student t-test"
                            if equal_var
                            else "Welch t-test"
                        ),
                        "t": (
                            clean_number(
                                statistic
                            )
                        ),
                        "p-value": (
                            clean_number(
                                p_value
                            )
                        ),
                        "Cohen's d": (
                            clean_number(
                                cohen_d
                            )
                        ),
                        "Effect": (
                            effect_magnitude(
                                cohen_d
                            )
                        ),
                    }
                ],
            },
        ],
        "assumptions": [
            {
                "Assumption": (
                    f"Normality - "
                    f"{group1}"
                ),
                "Check": (
                    "Shapiro-Wilk"
                ),
                "Statistic": (
                    norm1[
                        "statistic"
                    ]
                ),
                "p-value": (
                    norm1[
                        "p_value"
                    ]
                ),
                "Status": (
                    norm1[
                        "status"
                    ]
                ),
            },
            {
                "Assumption": (
                    f"Normality - "
                    f"{group2}"
                ),
                "Check": (
                    "Shapiro-Wilk"
                ),
                "Statistic": (
                    norm2[
                        "statistic"
                    ]
                ),
                "p-value": (
                    norm2[
                        "p_value"
                    ]
                ),
                "Status": (
                    norm2[
                        "status"
                    ]
                ),
            },
            {
                "Assumption": (
                    "Equality of variances"
                ),
                "Check": (
                    "Levene's Test"
                ),
                "Statistic": (
                    clean_number(
                        levene_stat
                    )
                ),
                "p-value": (
                    clean_number(
                        levene_p
                    )
                ),
                "Status": (
                    "Assumption met"
                    if equal_var
                    else (
                        "Unequal variances; "
                        "Welch correction used"
                    )
                ),
            },
        ],
        "decision": decision,
        "interpretation": (
            f"The independent samples "
            f"t-test comparing {group1} "
            f"and {group2} on {variable} "
            f"produced t = "
            f"{statistic:.4f}, "
            f"p = {p_value:.5f}."
        ),
        "apa": (
            f"An independent-samples "
            f"t-test "
            f"{'showed a significant' if p_value < alpha else 'did not show a significant'} "
            f"difference in {variable} "
            f"between {group1} and "
            f"{group2}, "
            f"t = {statistic:.2f}, "
            f"p = {p_value:.3f}."
        ),
    }


# ==========================================================
# MANN-WHITNEY
# ==========================================================

def mann_whitney(
    df,
    variable,
    group_variable,
    alternative,
    alpha,
):
    working = df[
        [
            variable,
            group_variable,
        ]
    ].copy()

    working[variable] = (
        pd.to_numeric(
            working[variable],
            errors="coerce",
        )
    )

    working = working.dropna()

    groups = sorted(
        working[
            group_variable
        ].unique().tolist(),
        key=lambda value: str(value),
    )

    if len(groups) != 2:
        raise ValueError(
            "Mann-Whitney U test requires exactly two groups."
        )

    group1 = groups[0]
    group2 = groups[1]

    x = working.loc[
        working[
            group_variable
        ] == group1,
        variable,
    ]

    y = working.loc[
        working[
            group_variable
        ] == group2,
        variable,
    ]

    statistic, p_value = (
        stats.mannwhitneyu(
            x,
            y,
            alternative=alternative,
        )
    )

    rank_biserial = (
        1
        - (
            2
            * statistic
            /
            (
                len(x)
                * len(y)
            )
        )
    )

    decision = (
        significance_decision(
            p_value,
            alpha,
        )
    )

    return {
        "test_key": (
            "mann_whitney"
        ),
        "test_name": (
            "Mann-Whitney U Test"
        ),
        "family": (
            "nonparametric"
        ),
        "hypotheses": {
            "null": (
                f"The distributions of "
                f"{variable} are the same "
                f"for {group1} and "
                f"{group2}."
            ),
            "alternative": (
                f"The distributions of "
                f"{variable} differ "
                f"between {group1} and "
                f"{group2}."
            ),
        },
        "tables": [
            {
                "title": (
                    "Group Statistics"
                ),
                "columns": [
                    group_variable,
                    "n",
                    "Median",
                    "Mean Rank",
                ],
                "rows": [
                    {
                        group_variable: (
                            str(group1)
                        ),
                        "n": len(x),
                        "Median": (
                            clean_number(
                                x.median()
                            )
                        ),
                        "Mean Rank": None,
                    },
                    {
                        group_variable: (
                            str(group2)
                        ),
                        "n": len(y),
                        "Median": (
                            clean_number(
                                y.median()
                            )
                        ),
                        "Mean Rank": None,
                    },
                ],
            },
            {
                "title": (
                    "Mann-Whitney Test"
                ),
                "columns": [
                    "Variable",
                    "U",
                    "p-value",
                    "Rank-Biserial",
                    "Effect",
                ],
                "rows": [
                    {
                        "Variable": variable,
                        "U": (
                            clean_number(
                                statistic
                            )
                        ),
                        "p-value": (
                            clean_number(
                                p_value
                            )
                        ),
                        "Rank-Biserial": (
                            clean_number(
                                rank_biserial
                            )
                        ),
                        "Effect": (
                            effect_magnitude(
                                rank_biserial
                            )
                        ),
                    }
                ],
            },
        ],
        "assumptions": [
            {
                "Assumption": (
                    "Independent observations"
                ),
                "Check": (
                    "Study design"
                ),
                "Statistic": None,
                "p-value": None,
                "Status": (
                    "User responsibility"
                ),
            }
        ],
        "decision": decision,
        "interpretation": (
            f"The Mann-Whitney U test "
            f"produced U = "
            f"{statistic:.4f}, "
            f"p = {p_value:.5f}."
        ),
        "apa": (
            f"A Mann-Whitney U test "
            f"{'showed a significant' if p_value < alpha else 'did not show a significant'} "
            f"difference in {variable} "
            f"between {group1} and "
            f"{group2}, "
            f"U = {statistic:.2f}, "
            f"p = {p_value:.3f}."
        ),
    }


# ==========================================================
# ONE-WAY ANOVA
# ==========================================================

def one_way_anova_test(
    df,
    variable,
    group_variable,
    alpha,
):
    working = df[
        [
            variable,
            group_variable,
        ]
    ].copy()

    working[variable] = (
        pd.to_numeric(
            working[variable],
            errors="coerce",
        )
    )

    working = working.dropna()

    group_data = []

    summary_rows = []
    assumption_rows = []

    for (
        group_name,
        group_df,
    ) in working.groupby(
        group_variable
    ):
        values = (
            group_df[variable]
            .dropna()
        )

        if len(values) == 0:
            continue

        group_data.append(
            values
        )

        summary_rows.append({
            group_variable: (
                str(group_name)
            ),
            "n": len(values),
            "Mean": (
                clean_number(
                    values.mean()
                )
            ),
            "Std. Deviation": (
                clean_number(
                    values.std(
                        ddof=1
                    )
                )
                if len(values) > 1
                else None
            ),
        })

        normality = (
            normality_check(
                values,
                alpha,
            )
        )

        assumption_rows.append({
            "Assumption": (
                f"Normality - "
                f"{group_name}"
            ),
            "Check": (
                "Shapiro-Wilk"
            ),
            "Statistic": (
                normality[
                    "statistic"
                ]
            ),
            "p-value": (
                normality[
                    "p_value"
                ]
            ),
            "Status": (
                normality[
                    "status"
                ]
            ),
        })

    if len(group_data) < 2:
        raise ValueError(
            "ANOVA requires at least two groups."
        )

    statistic, p_value = (
        stats.f_oneway(
            *group_data
        )
    )

    levene_stat, levene_p = (
        stats.levene(
            *group_data
        )
    )

    assumption_rows.append({
        "Assumption": (
            "Equality of variances"
        ),
        "Check": (
            "Levene's Test"
        ),
        "Statistic": (
            clean_number(
                levene_stat
            )
        ),
        "p-value": (
            clean_number(
                levene_p
            )
        ),
        "Status": (
            "Assumption met"
            if levene_p >= alpha
            else "Assumption not met"
        ),
    })

    grand_mean = (
        working[variable].mean()
    )

    ss_between = sum(
        len(values)
        * (
            values.mean()
            - grand_mean
        ) ** 2
        for values in group_data
    )

    ss_total = sum(
        (
            working[variable]
            - grand_mean
        ) ** 2
    )

    eta_squared = (
        ss_between / ss_total
        if ss_total != 0
        else None
    )

    df_between = (
        len(group_data) - 1
    )

    df_within = (
        len(working)
        - len(group_data)
    )

    decision = (
        significance_decision(
            p_value,
            alpha,
        )
    )

    return {
        "test_key": "anova",
        "test_name": (
            "One-Way ANOVA"
        ),
        "family": "parametric",
        "hypotheses": {
            "null": (
                f"The mean {variable} "
                f"is equal across all "
                f"{group_variable} groups."
            ),
            "alternative": (
                f"At least one "
                f"{group_variable} group "
                f"has a different mean "
                f"{variable}."
            ),
        },
        "tables": [
            {
                "title": (
                    "Descriptive Statistics"
                ),
                "columns": [
                    group_variable,
                    "n",
                    "Mean",
                    "Std. Deviation",
                ],
                "rows": summary_rows,
            },
            {
                "title": "ANOVA",
                "columns": [
                    "Variable",
                    "F",
                    "df Between",
                    "df Within",
                    "p-value",
                    "Eta Squared",
                    "Effect",
                ],
                "rows": [
                    {
                        "Variable": variable,
                        "F": (
                            clean_number(
                                statistic
                            )
                        ),
                        "df Between": (
                            df_between
                        ),
                        "df Within": (
                            df_within
                        ),
                        "p-value": (
                            clean_number(
                                p_value
                            )
                        ),
                        "Eta Squared": (
                            clean_number(
                                eta_squared
                            )
                        ),
                        "Effect": (
                            eta_magnitude(
                                eta_squared
                            )
                        ),
                    }
                ],
            },
        ],
        "assumptions": (
            assumption_rows
        ),
        "decision": decision,
        "interpretation": (
            f"The one-way ANOVA "
            f"produced F({df_between}, "
            f"{df_within}) = "
            f"{statistic:.4f}, "
            f"p = {p_value:.5f}."
        ),
        "apa": (
            f"A one-way ANOVA "
            f"{'showed a significant' if p_value < alpha else 'did not show a significant'} "
            f"effect of {group_variable} "
            f"on {variable}, "
            f"F({df_between}, "
            f"{df_within}) = "
            f"{statistic:.2f}, "
            f"p = {p_value:.3f}."
        ),
    }


# ==========================================================
# KRUSKAL-WALLIS
# ==========================================================

def kruskal_wallis(
    df,
    variable,
    group_variable,
    alpha,
):
    working = df[
        [
            variable,
            group_variable,
        ]
    ].copy()

    working[variable] = (
        pd.to_numeric(
            working[variable],
            errors="coerce",
        )
    )

    working = working.dropna()

    groups = []
    rows = []

    for (
        name,
        group_df,
    ) in working.groupby(
        group_variable
    ):
        values = (
            group_df[variable]
            .dropna()
        )

        if len(values):
            groups.append(
                values
            )

            rows.append({
                group_variable: str(
                    name
                ),
                "n": len(values),
                "Median": (
                    clean_number(
                        values.median()
                    )
                ),
            })

    if len(groups) < 2:
        raise ValueError(
            "Kruskal-Wallis requires at least two groups."
        )

    statistic, p_value = (
        stats.kruskal(
            *groups
        )
    )

    n = len(working)
    k = len(groups)

    eta_squared = (
        (
            statistic
            - k
            + 1
        )
        /
        (
            n - k
        )
        if n > k
        else None
    )

    decision = (
        significance_decision(
            p_value,
            alpha,
        )
    )

    return {
        "test_key": (
            "kruskal_wallis"
        ),
        "test_name": (
            "Kruskal-Wallis H Test"
        ),
        "family": (
            "nonparametric"
        ),
        "hypotheses": {
            "null": (
                f"The distributions of "
                f"{variable} are the same "
                f"across all "
                f"{group_variable} groups."
            ),
            "alternative": (
                f"At least one "
                f"{group_variable} group "
                f"has a different "
                f"distribution of "
                f"{variable}."
            ),
        },
        "tables": [
            {
                "title": (
                    "Group Statistics"
                ),
                "columns": [
                    group_variable,
                    "n",
                    "Median",
                ],
                "rows": rows,
            },
            {
                "title": (
                    "Kruskal-Wallis Test"
                ),
                "columns": [
                    "Variable",
                    "H",
                    "df",
                    "p-value",
                    "Effect Size",
                    "Magnitude",
                ],
                "rows": [
                    {
                        "Variable": variable,
                        "H": (
                            clean_number(
                                statistic
                            )
                        ),
                        "df": (
                            k - 1
                        ),
                        "p-value": (
                            clean_number(
                                p_value
                            )
                        ),
                        "Effect Size": (
                            clean_number(
                                eta_squared
                            )
                        ),
                        "Magnitude": (
                            eta_magnitude(
                                eta_squared
                            )
                        ),
                    }
                ],
            },
        ],
        "assumptions": [
            {
                "Assumption": (
                    "Independent observations"
                ),
                "Check": (
                    "Study design"
                ),
                "Statistic": None,
                "p-value": None,
                "Status": (
                    "User responsibility"
                ),
            }
        ],
        "decision": decision,
        "interpretation": (
            f"The Kruskal-Wallis test "
            f"produced H({k - 1}) = "
            f"{statistic:.4f}, "
            f"p = {p_value:.5f}."
        ),
        "apa": (
            f"A Kruskal-Wallis test "
            f"{'showed a significant' if p_value < alpha else 'did not show a significant'} "
            f"difference in {variable} "
            f"across {group_variable}, "
            f"H({k - 1}) = "
            f"{statistic:.2f}, "
            f"p = {p_value:.3f}."
        ),
    }


# ==========================================================
# CHI-SQUARE
# ==========================================================

def chi_square(
    df,
    variable1,
    variable2,
    alpha,
):
    table = pd.crosstab(
        df[variable1],
        df[variable2],
    )

    if (
        table.shape[0] < 2
        or table.shape[1] < 2
    ):
        raise ValueError(
            "Chi-square requires at least two categories in each variable."
        )

    statistic, p_value, dof, expected = (
        stats.chi2_contingency(
            table
        )
    )

    n = table.values.sum()

    min_dimension = (
        min(table.shape)
        - 1
    )

    cramers_v = (
        math.sqrt(
            statistic
            /
            (
                n
                * min_dimension
            )
        )
        if (
            n > 0
            and min_dimension > 0
        )
        else None
    )

    expected_array = (
        np.asarray(
            expected
        )
    )

    low_expected = int(
        (
            expected_array < 5
        ).sum()
    )

    total_cells = (
        expected_array.size
    )

    low_percent = (
        (
            low_expected
            / total_cells
        )
        * 100
        if total_cells
        else 0
    )

    observed_rows = []

    for row_name in table.index:
        row = {
            variable1: (
                str(row_name)
            )
        }

        for column_name in table.columns:
            row[str(column_name)] = int(
                table.loc[
                    row_name,
                    column_name,
                ]
            )

        observed_rows.append(
            row
        )

    decision = (
        significance_decision(
            p_value,
            alpha,
        )
    )

    return {
        "test_key": "chi_square",
        "test_name": (
            "Chi-Square Test "
            "of Independence"
        ),
        "family": "categorical",
        "hypotheses": {
            "null": (
                f"{variable1} and "
                f"{variable2} are "
                f"independent."
            ),
            "alternative": (
                f"{variable1} and "
                f"{variable2} are "
                f"associated."
            ),
        },
        "tables": [
            {
                "title": (
                    "Observed Frequencies"
                ),
                "columns": [
                    variable1,
                    *[
                        str(value)
                        for value
                        in table.columns
                    ],
                ],
                "rows": (
                    observed_rows
                ),
            },
            {
                "title": (
                    "Chi-Square Test"
                ),
                "columns": [
                    "Variables",
                    "Chi-Square",
                    "df",
                    "p-value",
                    "Cramer's V",
                    "Effect",
                ],
                "rows": [
                    {
                        "Variables": (
                            f"{variable1} × "
                            f"{variable2}"
                        ),
                        "Chi-Square": (
                            clean_number(
                                statistic
                            )
                        ),
                        "df": int(dof),
                        "p-value": (
                            clean_number(
                                p_value
                            )
                        ),
                        "Cramer's V": (
                            clean_number(
                                cramers_v
                            )
                        ),
                        "Effect": (
                            effect_magnitude(
                                cramers_v
                            )
                        ),
                    }
                ],
            },
        ],
        "assumptions": [
            {
                "Assumption": (
                    "Expected cell counts"
                ),
                "Check": (
                    "Expected frequency ≥ 5"
                ),
                "Statistic": (
                    low_expected
                ),
                "p-value": None,
                "Status": (
                    "Assumption met"
                    if low_percent <= 20
                    else (
                        f"{low_percent:.1f}% "
                        f"of cells below 5"
                    )
                ),
            }
        ],
        "decision": decision,
        "interpretation": (
            f"The chi-square test "
            f"produced χ²({dof}) = "
            f"{statistic:.4f}, "
            f"p = {p_value:.5f}."
        ),
        "apa": (
            f"A chi-square test of "
            f"independence "
            f"{'showed a significant' if p_value < alpha else 'did not show a significant'} "
            f"association between "
            f"{variable1} and "
            f"{variable2}, "
            f"χ²({dof}) = "
            f"{statistic:.2f}, "
            f"p = {p_value:.3f}."
        ),
    }


# ==========================================================
# AUTOMATIC TEST SELECTION
# ==========================================================

def run_hypothesis_test(
    df,
    family,
    metric_variables,
    categorical_variables,
    test_value,
    alternative,
    alpha,
):
    metric_variables = (
        metric_variables or []
    )

    categorical_variables = (
        categorical_variables or []
    )

    # ------------------------------------------------------
    # One metric only
    # ------------------------------------------------------

    if (
        len(metric_variables) == 1
        and
        len(categorical_variables) == 0
    ):
        variable = (
            metric_variables[0]
        )

        if family == "parametric":
            return one_sample_t(
                df,
                variable,
                test_value,
                alternative,
                alpha,
            )

        return one_sample_wilcoxon(
            df,
            variable,
            test_value,
            alternative,
            alpha,
        )

    # ------------------------------------------------------
    # Two metric variables = paired test
    # ------------------------------------------------------

    if (
        len(metric_variables) == 2
        and
        len(categorical_variables) == 0
    ):
        if family == "parametric":
            return paired_t(
                df,
                metric_variables[0],
                metric_variables[1],
                alternative,
                alpha,
            )

        return paired_wilcoxon(
            df,
            metric_variables[0],
            metric_variables[1],
            alternative,
            alpha,
        )

    # ------------------------------------------------------
    # One metric + one grouping variable
    # ------------------------------------------------------

    if (
        len(metric_variables) == 1
        and
        len(categorical_variables) == 1
    ):
        variable = (
            metric_variables[0]
        )

        group_variable = (
            categorical_variables[0]
        )

        valid = df[
            [
                variable,
                group_variable,
            ]
        ].dropna()

        number_of_groups = (
            valid[
                group_variable
            ].nunique()
        )

        if number_of_groups < 2:
            raise ValueError(
                "The grouping variable must contain at least two groups."
            )

        if number_of_groups == 2:
            if family == "parametric":
                return independent_t(
                    df,
                    variable,
                    group_variable,
                    alternative,
                    alpha,
                )

            return mann_whitney(
                df,
                variable,
                group_variable,
                alternative,
                alpha,
            )

        if family == "parametric":
            return one_way_anova_test(
                df,
                variable,
                group_variable,
                alpha,
            )

        return kruskal_wallis(
            df,
            variable,
            group_variable,
            alpha,
        )

    # ------------------------------------------------------
    # Two categorical variables
    # ------------------------------------------------------

    if (
        len(metric_variables) == 0
        and
        len(categorical_variables) == 2
    ):
        return chi_square(
            df,
            categorical_variables[0],
            categorical_variables[1],
            alpha,
        )

    raise ValueError(
        "Unable to determine an appropriate hypothesis test. "
        "Select: one metric variable; two metric variables; "
        "one metric plus one categorical variable; "
        "or two categorical variables."
    )
