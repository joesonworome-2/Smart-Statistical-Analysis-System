import math


# ==========================================================
# GENERAL HELPERS
# ==========================================================

def format_value(
    value,
    digits=4,
):
    if value is None:
        return "not available"

    if isinstance(
        value,
        bool,
    ):
        return (
            "Yes"
            if value
            else "No"
        )

    if isinstance(
        value,
        int,
    ):
        return f"{value:,}"

    if isinstance(
        value,
        float,
    ):
        if (
            math.isnan(value)
            or math.isinf(value)
        ):
            return "not available"

        if (
            value != 0
            and
            abs(value) < 0.001
        ):
            return (
                f"{value:.3e}"
            )

        return (
            f"{value:.{digits}f}"
        )

    return str(value)


def format_p_value(
    p_value,
):
    if p_value is None:
        return (
            "not available"
        )

    if p_value < 0.001:
        return "p < 0.001"

    return (
        f"p = {p_value:.4f}"
    )


def find_table(
    result,
    keywords,
):
    tables = (
        result.get(
            "tables",
            []
        )
        or []
    )

    for table in tables:
        title = (
            table.get(
                "title",
                ""
            )
            .lower()
        )

        for keyword in keywords:
            if (
                keyword.lower()
                in title
            ):
                return table

    return None


def get_first_row(
    table,
):
    if not table:
        return {}

    rows = (
        table.get(
            "rows",
            []
        )
        or []
    )

    if not rows:
        return {}

    return rows[0]


def get_value(
    row,
    *keys,
):
    for key in keys:
        if (
            key in row
            and
            row[key]
            is not None
        ):
            return row[key]

    return None


# ==========================================================
# TEST PURPOSE
# ==========================================================

def test_purpose(
    test_key,
):
    purposes = {

        "one_sample_t": (
            "The One-Sample t-Test compares the mean "
            "of one quantitative variable with a "
            "specific reference or hypothesised "
            "population value."
        ),

        "one_sample_wilcoxon": (
            "The One-Sample Wilcoxon Signed-Rank Test "
            "is a nonparametric procedure used to "
            "determine whether the location of a "
            "sample differs from a specified reference "
            "value when a parametric one-sample t-test "
            "is not preferred."
        ),

        "independent_t": (
            "The Independent Samples t-Test compares "
            "the mean of a quantitative outcome "
            "between two independent groups."
        ),

        "paired_t": (
            "The Paired Samples t-Test compares two "
            "related measurements, such as before and "
            "after measurements from the same cases."
        ),

        "mann_whitney": (
            "The Mann-Whitney U Test is a "
            "nonparametric test used to compare the "
            "distributions of a quantitative or "
            "ordinal variable between two independent "
            "groups."
        ),

        "paired_wilcoxon": (
            "The Wilcoxon Signed-Rank Test compares "
            "two related samples using ranked "
            "differences rather than relying on a "
            "normal-distribution assumption."
        ),

        "anova": (
            "One-Way ANOVA tests whether the mean of "
            "a quantitative outcome is equal across "
            "three or more independent groups."
        ),

        "kruskal_wallis": (
            "The Kruskal-Wallis H Test is the "
            "nonparametric alternative to one-way "
            "ANOVA and compares ranked outcomes "
            "across two or more independent groups."
        ),

        "chi_square": (
            "The Chi-Square Test of Independence "
            "examines whether two categorical "
            "variables are statistically associated."
        ),
    }

    return purposes.get(
        test_key,
        (
            "This statistical test evaluates evidence "
            "against a stated null hypothesis."
        ),
    )


# ==========================================================
# WHY SELECTED
# ==========================================================

def why_selected(
    test_key,
):
    reasons = {

        "one_sample_t": (
            "SSAS selected this test because one "
            "metric variable was selected, no grouping "
            "variable was selected, and the user chose "
            "a parametric test."
        ),

        "one_sample_wilcoxon": (
            "SSAS selected this procedure because one "
            "metric variable was selected with no "
            "grouping variable and the nonparametric "
            "test family was requested."
        ),

        "independent_t": (
            "SSAS selected this procedure because one "
            "metric outcome and one grouping variable "
            "with exactly two groups were selected "
            "under the parametric test family."
        ),

        "mann_whitney": (
            "SSAS selected this procedure because one "
            "metric outcome and a two-group categorical "
            "variable were selected under the "
            "nonparametric test family."
        ),

        "anova": (
            "SSAS selected One-Way ANOVA because one "
            "metric outcome and one categorical "
            "grouping variable containing more than "
            "two groups were selected under the "
            "parametric test family."
        ),

        "kruskal_wallis": (
            "SSAS selected the Kruskal-Wallis test "
            "because one metric outcome and a grouping "
            "variable containing multiple groups were "
            "selected under the nonparametric family."
        ),

        "paired_t": (
            "SSAS selected a paired t-test because two "
            "metric variables were selected without a "
            "separate grouping variable and a "
            "parametric paired comparison was requested."
        ),

        "paired_wilcoxon": (
            "SSAS selected the Wilcoxon signed-rank "
            "test because two related metric variables "
            "were selected under the nonparametric "
            "test family."
        ),

        "chi_square": (
            "SSAS selected the Chi-Square Test because "
            "two categorical variables were selected "
            "and the objective is to determine whether "
            "their categories are associated."
        ),
    }

    return reasons.get(
        test_key,
        (
            "The selected test matches the measurement "
            "levels and variable combination supplied "
            "by the user."
        ),
    )


# ==========================================================
# DESCRIPTIVE EXPLANATION
# ==========================================================

def descriptive_explanation(
    result,
):
    tables = (
        result.get(
            "tables",
            []
        )
        or []
    )

    if not tables:
        return []

    descriptive_table = (
        tables[0]
    )

    rows = (
        descriptive_table.get(
            "rows",
            []
        )
        or []
    )

    messages = []

    for row in rows:
        parts = []

        label = (
            row.get(
                "Variable"
            )
            or
            row.get(
                "Pair"
            )
        )

        if label:
            parts.append(
                str(label)
            )

        for key in [
            "n",
            "Mean",
            "Median",
            "Std. Deviation",
            "Std. Error Mean",
            "Test Value",
        ]:
            if (
                key in row
                and
                row[key]
                is not None
            ):
                parts.append(
                    (
                        f"{key} = "
                        f"{format_value(row[key])}"
                    )
                )

        if len(parts) > 1:
            messages.append(
                ", ".join(parts)
                + "."
            )

        else:
            # Group statistics can use the
            # categorical column as the first key.
            values = []

            for key, value in row.items():
                if value is not None:
                    values.append(
                        (
                            f"{key} = "
                            f"{format_value(value)}"
                        )
                    )

            if values:
                messages.append(
                    ", ".join(values)
                    + "."
                )

    if not messages:
        return []

    return [
        (
            "The descriptive statistics provide "
            "context before interpreting the "
            "inferential test."
        ),
        *messages,
    ]


# ==========================================================
# TEST STATISTIC EXPLANATION
# ==========================================================

def statistic_explanation(
    result,
):
    test_key = (
        result.get(
            "test_key",
            ""
        )
    )

    tables = (
        result.get(
            "tables",
            []
        )
        or []
    )

    if not tables:
        return []

    test_table = (
        tables[-1]
    )

    row = get_first_row(
        test_table
    )

    messages = []

    if test_key in {
        "one_sample_t",
        "independent_t",
        "paired_t",
    }:
        statistic = get_value(
            row,
            "t",
        )

        df = get_value(
            row,
            "df",
        )

        if statistic is not None:
            messages.append(
                (
                    "The t-statistic is "
                    f"{format_value(statistic)}. "
                    "A t-statistic expresses the "
                    "observed difference relative to "
                    "the amount of sampling variation "
                    "or standard error. Larger absolute "
                    "t-values generally represent "
                    "stronger evidence against the null "
                    "hypothesis."
                )
            )

        if df is not None:
            messages.append(
                (
                    "The degrees of freedom are "
                    f"{format_value(df)}. Degrees of "
                    "freedom determine the reference "
                    "t-distribution used to calculate "
                    "the p-value."
                )
            )

    elif test_key == "anova":
        statistic = get_value(
            row,
            "F",
        )

        df_between = get_value(
            row,
            "df Between",
        )

        df_within = get_value(
            row,
            "df Within",
        )

        if statistic is not None:
            messages.append(
                (
                    "The F-statistic is "
                    f"{format_value(statistic)}. "
                    "The F-ratio compares variation "
                    "between group means with variation "
                    "within the groups. A larger F-ratio "
                    "indicates that the group means are "
                    "more separated relative to the "
                    "natural variation within groups."
                )
            )

        if (
            df_between is not None
            and
            df_within is not None
        ):
            messages.append(
                (
                    "The test uses "
                    f"{format_value(df_between)} "
                    "between-group degrees of freedom "
                    "and "
                    f"{format_value(df_within)} "
                    "within-group degrees of freedom."
                )
            )

    elif (
        test_key
        ==
        "kruskal_wallis"
    ):
        statistic = get_value(
            row,
            "H",
        )

        df = get_value(
            row,
            "df",
        )

        messages.append(
            (
                "The Kruskal-Wallis H statistic is "
                f"{format_value(statistic)} with "
                f"{format_value(df)} degrees of "
                "freedom. This statistic is calculated "
                "from ranked observations and indicates "
                "how different the group rank "
                "distributions are."
            )
        )

    elif (
        test_key
        ==
        "mann_whitney"
    ):
        statistic = get_value(
            row,
            "U",
        )

        messages.append(
            (
                "The Mann-Whitney U statistic is "
                f"{format_value(statistic)}. The U "
                "statistic is based on the relative "
                "ranks of observations from the two "
                "groups rather than directly comparing "
                "their arithmetic means."
            )
        )

    elif test_key in {
        "paired_wilcoxon",
        "one_sample_wilcoxon",
    }:
        statistic = get_value(
            row,
            "W",
        )

        messages.append(
            (
                "The Wilcoxon W statistic is "
                f"{format_value(statistic)}. It is "
                "derived from the ranks of non-zero "
                "differences and evaluates whether "
                "positive and negative differences are "
                "balanced around the null value."
            )
        )

    elif (
        test_key
        ==
        "chi_square"
    ):
        statistic = get_value(
            row,
            "Chi-Square",
        )

        df = get_value(
            row,
            "df",
        )

        messages.append(
            (
                "The chi-square statistic is "
                f"{format_value(statistic)} with "
                f"{format_value(df)} degrees of "
                "freedom. It measures how different "
                "the observed category frequencies are "
                "from the frequencies expected if the "
                "two categorical variables were "
                "independent."
            )
        )

    return messages


# ==========================================================
# P-VALUE AND DECISION
# ==========================================================

def significance_explanation(
    result,
):
    decision = (
        result.get(
            "decision",
            {}
        )
        or {}
    )

    alpha = (
        decision.get(
            "alpha",
            0.05
        )
    )

    significant = bool(
        decision.get(
            "significant",
            False
        )
    )

    tables = (
        result.get(
            "tables",
            []
        )
        or []
    )

    test_row = {}

    if tables:
        test_row = (
            get_first_row(
                tables[-1]
            )
        )

    p_value = get_value(
        test_row,
        "p-value",
    )

    messages = []

    if p_value is not None:
        messages.append(
            (
                "The p-value is "
                f"{format_p_value(p_value)}. "
                "The p-value represents how compatible "
                "the observed result is with the null "
                "hypothesis under the assumptions of "
                "the statistical model."
            )
        )

    messages.append(
        (
            "The selected significance level is "
            f"α = {format_value(alpha)}. "
            "SSAS compares the p-value with this "
            "threshold."
        )
    )

    if significant:
        messages.append(
            (
                "Because the p-value is smaller than "
                "the significance level, the result is "
                "statistically significant. SSAS "
                "therefore rejects the null hypothesis."
            )
        )

        messages.append(
            (
                "A statistically significant result "
                "means that the observed evidence would "
                "be relatively unusual under the null "
                "hypothesis. It does not automatically "
                "mean that the effect is large or "
                "practically important."
            )
        )

    else:
        messages.append(
            (
                "Because the p-value is not smaller "
                "than the significance level, the "
                "result is not statistically "
                "significant. SSAS therefore fails to "
                "reject the null hypothesis."
            )
        )

        messages.append(
            (
                "Failing to reject the null hypothesis "
                "does not prove that the null "
                "hypothesis is true. It means the data "
                "do not provide sufficiently strong "
                "evidence against it at the chosen "
                "significance level."
            )
        )

    return messages


# ==========================================================
# EFFECT SIZE
# ==========================================================

def effect_size_explanation(
    result,
):
    tables = (
        result.get(
            "tables",
            []
        )
        or []
    )

    if not tables:
        return []

    row = get_first_row(
        tables[-1]
    )

    candidates = [
        (
            "Cohen's d",
            "Cohen's d",
        ),
        (
            "Cohen's dz",
            "Cohen's dz",
        ),
        (
            "Eta Squared",
            "eta squared",
        ),
        (
            "Effect Size",
            "effect size",
        ),
        (
            "Rank-Biserial",
            "rank-biserial correlation",
        ),
        (
            "Cramer's V",
            "Cramer's V",
        ),
    ]

    effect_value = None
    effect_name = None

    for (
        key,
        description,
    ) in candidates:
        if (
            key in row
            and
            row[key]
            is not None
        ):
            effect_value = (
                row[key]
            )

            effect_name = (
                description
            )

            break

    if effect_value is None:
        return [
            (
                "No numerical effect-size estimate "
                "was returned for this test. Statistical "
                "significance should therefore be "
                "interpreted together with the raw "
                "descriptive differences."
            )
        ]

    magnitude = (
        row.get(
            "Effect"
        )
        or
        row.get(
            "Magnitude"
        )
    )

    messages = [
        (
            f"The {effect_name} is "
            f"{format_value(effect_value)}."
        )
    ]

    if magnitude:
        messages.append(
            (
                "SSAS classifies the magnitude as "
                f"{str(magnitude).lower()}. "
                "Effect size describes the magnitude "
                "of the relationship or difference and "
                "is different from statistical "
                "significance."
            )
        )

    messages.append(
        (
            "A very small p-value can occur even when "
            "the effect is small if the sample size is "
            "large, which is why effect size should "
            "always be considered alongside the "
            "p-value."
        )
    )

    return messages


# ==========================================================
# CONFIDENCE INTERVAL
# ==========================================================

def confidence_interval_explanation(
    result,
):
    tables = (
        result.get(
            "tables",
            []
        )
        or []
    )

    if not tables:
        return []

    row = get_first_row(
        tables[-1]
    )

    lower = get_value(
        row,
        "CI Lower",
    )

    upper = get_value(
        row,
        "CI Upper",
    )

    if (
        lower is None
        or upper is None
    ):
        return [
            (
                "A confidence interval is not reported "
                "for this particular result."
            )
        ]

    return [
        (
            "The confidence interval extends from "
            f"{format_value(lower)} to "
            f"{format_value(upper)}."
        ),
        (
            "A confidence interval provides a range of "
            "values that are reasonably compatible "
            "with the estimated population effect "
            "under the statistical model. Narrower "
            "intervals indicate greater precision, "
            "while wider intervals indicate greater "
            "uncertainty."
        ),
    ]


# ==========================================================
# ASSUMPTIONS
# ==========================================================

def assumptions_explanation(
    result,
):
    assumptions = (
        result.get(
            "assumptions",
            []
        )
        or []
    )

    if not assumptions:
        return [
            (
                "No automated assumption checks were "
                "returned for this test."
            )
        ]

    messages = []

    for assumption in assumptions:
        name = (
            assumption.get(
                "Assumption",
                "Assumption"
            )
        )

        check = (
            assumption.get(
                "Check",
                "Not specified"
            )
        )

        statistic = (
            assumption.get(
                "Statistic"
            )
        )

        p_value = (
            assumption.get(
                "p-value"
            )
        )

        status = (
            assumption.get(
                "Status",
                "Review"
            )
        )

        sentence = (
            f"{name}: checked using "
            f"{check}."
        )

        if statistic is not None:
            sentence += (
                " Test statistic = "
                f"{format_value(statistic)}."
            )

        if p_value is not None:
            sentence += (
                " "
                f"{format_p_value(p_value)}."
            )

        sentence += (
            f" Status: {status}."
        )

        messages.append(
            sentence
        )

    messages.append(
        (
            "Assumption checks should not be interpreted "
            "mechanically. The study design, independence "
            "of observations, measurement quality, "
            "sample size, outliers and distributional "
            "shape should also be considered."
        )
    )

    return messages


# ==========================================================
# PRACTICAL MEANING
# ==========================================================

def practical_explanation(
    result,
):
    test_key = (
        result.get(
            "test_key",
            ""
        )
    )

    decision = (
        result.get(
            "decision",
            {}
        )
        or {}
    )

    significant = bool(
        decision.get(
            "significant",
            False
        )
    )

    messages = []

    if test_key == "anova":
        if significant:
            messages.append(
                (
                    "The significant ANOVA result means "
                    "that at least one group mean differs "
                    "from another. ANOVA alone does not "
                    "identify exactly which groups differ."
                )
            )

            messages.append(
                (
                    "A post-hoc multiple-comparison "
                    "procedure such as Tukey's HSD should "
                    "be considered to identify the "
                    "specific group differences."
                )
            )

    elif (
        test_key
        ==
        "kruskal_wallis"
    ):
        if significant:
            messages.append(
                (
                    "The significant Kruskal-Wallis "
                    "result indicates that at least one "
                    "group has a different rank "
                    "distribution. Appropriate pairwise "
                    "post-hoc comparisons are needed to "
                    "identify which groups differ."
                )
            )

    elif (
        test_key
        ==
        "chi_square"
    ):
        if significant:
            messages.append(
                (
                    "The significant chi-square result "
                    "indicates an association between the "
                    "two categorical variables. It does "
                    "not show that one variable causes "
                    "the other."
                )
            )

            messages.append(
                (
                    "Examining observed and expected "
                    "frequencies or standardized "
                    "residuals can help identify which "
                    "category combinations contribute "
                    "most strongly to the association."
                )
            )

    elif test_key in {
        "one_sample_t",
        "one_sample_wilcoxon",
    }:
        messages.append(
            (
                "The practical meaning depends on how "
                "large the observed difference from the "
                "reference value is, not only on whether "
                "the difference is statistically "
                "significant."
            )
        )

    elif test_key in {
        "independent_t",
        "mann_whitney",
    }:
        messages.append(
            (
                "The result should be interpreted "
                "together with the group descriptive "
                "statistics and effect size to determine "
                "whether the observed group difference "
                "is meaningful in practice."
            )
        )

    elif test_key in {
        "paired_t",
        "paired_wilcoxon",
    }:
        messages.append(
            (
                "Because the observations are paired, "
                "the result describes change or "
                "difference within matched cases rather "
                "than differences between unrelated "
                "groups."
            )
        )

    if not messages:
        messages.append(
            (
                "Practical importance should be judged "
                "using the magnitude of the effect, the "
                "measurement scale, domain knowledge and "
                "the consequences of the observed "
                "difference."
            )
        )

    return messages


# ==========================================================
# LIMITATIONS
# ==========================================================

def limitations_explanation(
    result,
):
    return [
        (
            "Statistical significance does not establish "
            "causation. Causal conclusions require an "
            "appropriate research design and control of "
            "alternative explanations."
        ),
        (
            "Results can be influenced by sample size, "
            "missing values, measurement error, extreme "
            "observations and violations of study-design "
            "assumptions."
        ),
        (
            "The analysis applies only to the supplied "
            "dataset and selected variables. Generalising "
            "the result to a wider population requires "
            "appropriate sampling and study design."
        ),
        (
            "The p-value should not be interpreted as "
            "the probability that the null hypothesis "
            "is true or false."
        ),
    ]


# ==========================================================
# FINAL CONCLUSION
# ==========================================================

def conclusion_explanation(
    result,
):
    decision = (
        result.get(
            "decision",
            {}
        )
        or {}
    )

    significant = bool(
        decision.get(
            "significant",
            False
        )
    )

    hypotheses = (
        result.get(
            "hypotheses",
            {}
        )
        or {}
    )

    null_hypothesis = (
        hypotheses.get(
            "null",
            "the null hypothesis"
        )
    )

    alternative = (
        hypotheses.get(
            "alternative",
            "the alternative hypothesis"
        )
    )

    if significant:
        return [
            (
                "Overall, the statistical evidence is "
                "sufficient at the selected significance "
                "level to reject the null hypothesis."
            ),
            (
                "Null hypothesis: "
                f"{null_hypothesis}"
            ),
            (
                "The data therefore provide statistical "
                "support for the alternative statement: "
                f"{alternative}"
            ),
        ]

    return [
        (
            "Overall, the statistical evidence is not "
            "strong enough at the selected significance "
            "level to reject the null hypothesis."
        ),
        (
            "Null hypothesis: "
            f"{null_hypothesis}"
        ),
        (
            "This does not prove the null hypothesis. "
            "It means that the available sample does not "
            "provide sufficient evidence to support the "
            "alternative statement: "
            f"{alternative}"
        ),
    ]


# ==========================================================
# MAIN EXPLANATION BUILDER
# ==========================================================

def build_hypothesis_explanation(
    result,
):
    test_key = (
        result.get(
            "test_key",
            ""
        )
    )

    test_name = (
        result.get(
            "test_name",
            "Hypothesis Test"
        )
    )

    hypotheses = (
        result.get(
            "hypotheses",
            {}
        )
        or {}
    )

    original_interpretation = (
        result.get(
            "interpretation"
        )
    )

    sections = [
        {
            "title":
                "1. What test was performed?",

            "paragraphs": [
                test_purpose(
                    test_key
                ),
            ],
        },

        {
            "title":
                "2. Why SSAS selected this test",

            "paragraphs": [
                why_selected(
                    test_key
                ),
            ],
        },

        {
            "title":
                "3. Hypotheses being tested",

            "paragraphs": [
                (
                    "Null hypothesis (H₀): "
                    f"{hypotheses.get('null', 'Not available')}"
                ),
                (
                    "Alternative hypothesis (H₁): "
                    f"{hypotheses.get('alternative', 'Not available')}"
                ),
                (
                    "The statistical test evaluates "
                    "whether the sample provides enough "
                    "evidence to reject H₀ in favour of "
                    "H₁."
                ),
            ],
        },

        {
            "title":
                "4. Description of the sample",

            "paragraphs":
                descriptive_explanation(
                    result
                ),
        },

        {
            "title":
                "5. Understanding the test statistic",

            "paragraphs":
                statistic_explanation(
                    result
                ),
        },

        {
            "title":
                "6. Understanding the p-value",

            "paragraphs":
                significance_explanation(
                    result
                ),
        },

        {
            "title":
                "7. Effect size and practical magnitude",

            "paragraphs":
                effect_size_explanation(
                    result
                ),
        },

        {
            "title":
                "8. Confidence interval",

            "paragraphs":
                confidence_interval_explanation(
                    result
                ),
        },

        {
            "title":
                "9. Test assumptions",

            "paragraphs":
                assumptions_explanation(
                    result
                ),
        },

        {
            "title":
                "10. Practical interpretation",

            "paragraphs":
                practical_explanation(
                    result
                ),
        },

        {
            "title":
                "11. Limitations and cautions",

            "paragraphs":
                limitations_explanation(
                    result
                ),
        },

        {
            "title":
                "12. Final conclusion",

            "paragraphs":
                conclusion_explanation(
                    result
                ),
        },
    ]

    if original_interpretation:
        sections.insert(
            10,
            {
                "title":
                    "11. Statistical summary",

                "paragraphs": [
                    original_interpretation
                ],
            },
        )

    return {
        "title":
            (
                "Detailed Explanation — "
                f"{test_name}"
            ),

        "introduction": (
            "This explanation interprets the statistical "
            "output step by step. It is intended to help "
            "the user understand both the numerical "
            "result and what can reasonably be concluded "
            "from it."
        ),

        "sections":
            sections,
    }
