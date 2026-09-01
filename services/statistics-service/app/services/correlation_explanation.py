def format_value(
    value,
    digits=4,
):
    if value is None:
        return "not available"

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


def format_p(
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


def get_significance_rows(
    result,
):
    tables = (
        result.get(
            "tables",
            []
        )
        or []
    )

    for table in tables:
        if (
            table.get(
                "title"
            )
            ==
            "Correlation Significance"
        ):
            return (
                table.get(
                    "rows",
                    []
                )
                or []
            )

    return []


def strongest_pair(
    result,
):
    rows = (
        get_significance_rows(
            result
        )
    )

    if not rows:
        return None

    return max(
        rows,
        key=lambda row:
            abs(
                row.get(
                    "Coefficient",
                    0
                )
            ),
    )


def build_pair_explanations(
    result,
):
    rows = (
        get_significance_rows(
            result
        )
    )

    paragraphs = []

    for row in rows:
        first = (
            row[
                "Variable 1"
            ]
        )

        second = (
            row[
                "Variable 2"
            ]
        )

        coefficient = (
            row[
                "Coefficient"
            ]
        )

        p_value = (
            row[
                "p-value"
            ]
        )

        strength = (
            row[
                "Strength"
            ]
        )

        direction = (
            row[
                "Direction"
            ]
        )

        sample_size = (
            row[
                "n"
            ]
        )

        significant = (
            row[
                "Significant"
            ]
            ==
            "Yes"
        )

        paragraph = (
            f"{first} and {second}: "
            f"the correlation coefficient is "
            f"{format_value(coefficient)} based on "
            f"{format_value(sample_size)} complete paired "
            f"observations. SSAS classifies this as a "
            f"{strength.lower()} {direction.lower()} "
            f"relationship. "
            f"The statistical test produced "
            f"{format_p(p_value)}. "
        )

        if significant:
            paragraph += (
                "Because the p-value is below the selected "
                "significance level, this relationship is "
                "statistically significant."
            )
        else:
            paragraph += (
                "Because the p-value is not below the "
                "selected significance level, this "
                "relationship is not statistically significant."
            )

        paragraphs.append(
            paragraph
        )

    return paragraphs


def build_correlation_explanation(
    result,
):
    method = (
        result.get(
            "selected_method",
            "correlation"
        )
    )

    recommendation = (
        result.get(
            "recommendation",
            {}
        )
        or {}
    )

    configuration = (
        result.get(
            "configuration",
            {}
        )
        or {}
    )

    variables = (
        configuration.get(
            "variables",
            []
        )
        or []
    )

    alpha = (
        configuration.get(
            "alpha",
            0.05
        )
    )

    strongest = (
        strongest_pair(
            result
        )
    )

    sections = []


    # ======================================================
    # 1. ANALYSIS
    # ======================================================

    sections.append({
        "title":
            "1. What analysis was performed?",

        "paragraphs": [
            (
                f"SSAS performed a "
                f"{method.capitalize()} correlation analysis "
                f"using the selected variables: "
                f"{', '.join(variables)}."
            ),
            (
                "Correlation analysis measures the direction "
                "and strength of association between variables. "
                "It does not by itself demonstrate a causal "
                "relationship."
            ),
        ],
    })


    # ======================================================
    # 2. WHY METHOD
    # ======================================================

    if method == "pearson":
        method_description = (
            "Pearson correlation measures the strength "
            "of a linear relationship between quantitative "
            "variables."
        )

    elif method == "spearman":
        method_description = (
            "Spearman correlation is based on ranks and "
            "measures the strength of a monotonic relationship. "
            "It is generally less sensitive to extreme values "
            "and non-normal distributions than Pearson "
            "correlation."
        )

    else:
        method_description = (
            "Kendall's tau is a rank-based correlation "
            "coefficient. It is useful with smaller samples, "
            "ordinal data, or variables containing many tied "
            "values."
        )

    sections.append({
        "title":
            "2. Why this correlation method was used",

        "paragraphs": [
            method_description,
            (
                "SSAS recommendation: "
                f"{recommendation.get('reason', 'No recommendation explanation available.')}"
            ),
        ],
    })


    # ======================================================
    # 3. COEFFICIENT
    # ======================================================

    sections.append({
        "title":
            "3. Understanding the correlation coefficient",

        "paragraphs": [
            (
                "A correlation coefficient ranges from -1 to +1."
            ),
            (
                "Values close to +1 indicate a strong positive "
                "association: larger values of one variable tend "
                "to occur with larger values of the other."
            ),
            (
                "Values close to -1 indicate a strong negative "
                "association: larger values of one variable tend "
                "to occur with smaller values of the other."
            ),
            (
                "Values near zero indicate little or no "
                "relationship of the type being measured."
            ),
        ],
    })


    # ======================================================
    # 4. PAIR RESULTS
    # ======================================================

    sections.append({
        "title":
            "4. Explanation of the individual relationships",

        "paragraphs":
            build_pair_explanations(
                result
            ),
    })


    # ======================================================
    # 5. STRONGEST
    # ======================================================

    if strongest:
        strongest_paragraphs = [
            (
                f"The strongest relationship in this analysis "
                f"is between {strongest['Variable 1']} and "
                f"{strongest['Variable 2']}."
            ),
            (
                f"The coefficient is "
                f"{format_value(strongest['Coefficient'])}, "
                f"which SSAS classifies as a "
                f"{strongest['Strength'].lower()} "
                f"{strongest['Direction'].lower()} relationship."
            ),
        ]

    else:
        strongest_paragraphs = [
            "No valid correlation pair was available."
        ]

    sections.append({
        "title":
            "5. Strongest relationship",

        "paragraphs":
            strongest_paragraphs,
    })


    # ======================================================
    # 6. P VALUE
    # ======================================================

    sections.append({
        "title":
            "6. Understanding statistical significance",

        "paragraphs": [
            (
                f"The selected significance level is α = {alpha}."
            ),
            (
                "For each relationship, SSAS compares the "
                "p-value with α. When p < α, the relationship "
                "is considered statistically significant."
            ),
            (
                "A statistically significant correlation means "
                "that the observed association would be unlikely "
                "under a model where the population correlation "
                "is zero. It does not tell us that the "
                "relationship is large or practically important."
            ),
            (
                "The p-value is not the probability that the "
                "null hypothesis is true."
            ),
        ],
    })


    # ======================================================
    # 7. SAMPLE SIZE
    # ======================================================

    sections.append({
        "title":
            "7. Role of sample size",

        "paragraphs": [
            (
                "The n column shows the number of complete paired "
                "observations used for each correlation."
            ),
            (
                "Large samples can make even relatively weak "
                "relationships statistically significant. "
                "Therefore the correlation coefficient and its "
                "strength should be interpreted together with "
                "the p-value."
            ),
        ],
    })


    # ======================================================
    # 8. CONFIDENCE INTERVAL
    # ======================================================

    sections.append({
        "title":
            "8. Confidence intervals",

        "paragraphs": [
            (
                "For Pearson correlations, SSAS reports a "
                "confidence interval for the population "
                "correlation using Fisher's z transformation."
            ),
            (
                "The interval indicates a range of plausible "
                "population correlation values. Narrow intervals "
                "indicate greater precision, whereas wide "
                "intervals indicate greater uncertainty."
            ),
            (
                "Rank-based Spearman and Kendall confidence "
                "intervals are not currently returned by this "
                "implementation."
            ),
        ],
    })


    # ======================================================
    # 9. DIAGNOSTICS
    # ======================================================

    sections.append({
        "title":
            "9. Diagnostics and assumptions",

        "paragraphs": [
            (
                "SSAS reports valid sample size, Shapiro-Wilk "
                "results, skewness, outlier counts and outlier "
                "percentages for each selected variable."
            ),
            (
                "These diagnostics help identify situations where "
                "extreme values, heavy skewness or tied values "
                "could influence the choice or interpretation of "
                "the correlation coefficient."
            ),
            (
                "Pearson correlation is particularly sensitive to "
                "extreme observations and measures linear "
                "association. Spearman and Kendall are rank-based "
                "alternatives."
            ),
        ],
    })


    # ======================================================
    # 10. PRACTICAL INTERPRETATION
    # ======================================================

    sections.append({
        "title":
            "10. Practical interpretation",

        "paragraphs": [
            (
                "Statistical significance and practical importance "
                "are different concepts. A statistically significant "
                "correlation can still be too weak to matter in a "
                "real-world setting."
            ),
            (
                "The magnitude of the coefficient, measurement "
                "quality, subject-matter knowledge and the purpose "
                "of the analysis should all be considered when "
                "judging practical importance."
            ),
        ],
    })


    # ======================================================
    # 11. CAUSATION
    # ======================================================

    sections.append({
        "title":
            "11. Correlation does not imply causation",

        "paragraphs": [
            (
                "A correlation shows that variables change together; "
                "it does not establish that one variable causes the "
                "other."
            ),
            (
                "The observed relationship could result from reverse "
                "causation, another unmeasured variable, sampling "
                "effects, measurement error or other factors."
            ),
            (
                "Causal conclusions require an appropriate research "
                "design and additional evidence."
            ),
        ],
    })


    # ======================================================
    # 12. LIMITATIONS
    # ======================================================

    sections.append({
        "title":
            "12. Limitations and cautions",

        "paragraphs": [
            (
                "Correlation can be strongly influenced by data "
                "quality, missing observations and extreme values."
            ),
            (
                "A coefficient close to zero does not necessarily "
                "mean that two variables are unrelated. They may "
                "have a nonlinear relationship that the selected "
                "correlation method does not capture."
            ),
            (
                "Generalising these results beyond this dataset "
                "requires an appropriate sampling method and study "
                "design."
            ),
        ],
    })


    # ======================================================
    # 13. CONCLUSION
    # ======================================================

    if strongest:
        conclusion = [
            (
                f"Overall, the strongest association was between "
                f"{strongest['Variable 1']} and "
                f"{strongest['Variable 2']}."
            ),
            (
                f"The observed coefficient was "
                f"{format_value(strongest['Coefficient'])}, "
                f"representing a "
                f"{strongest['Strength'].lower()} "
                f"{strongest['Direction'].lower()} relationship."
            ),
            (
                f"The corresponding result was "
                f"{format_p(strongest['p-value'])}."
            ),
            (
                "This result should be interpreted as evidence of "
                "association rather than causation."
            ),
        ]

    else:
        conclusion = [
            (
                "No valid correlation relationship was available "
                "for a final statistical conclusion."
            )
        ]

    sections.append({
        "title":
            "13. Final conclusion",

        "paragraphs":
            conclusion,
    })

    return {
        "title":
            (
                "Detailed Explanation — "
                "Correlation Analysis"
            ),

        "introduction":
            (
                "This explanation interprets the correlation "
                "results step by step, including the selected "
                "method, coefficient magnitude, direction, "
                "statistical significance, diagnostics and "
                "practical meaning."
            ),

        "sections":
            sections,
    }
