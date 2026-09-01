def build_ancova_explanation(
    result,
):
    configuration = (
        result.get(
            "configuration",
            {}
        )
    )


    factor_result = (
        result.get(
            "factor_result",
            {}
        )
    )


    dependent = (
        configuration.get(
            "dependent_variable",
            "the dependent variable",
        )
    )


    factor = (
        configuration.get(
            "factor_variable",
            "the factor",
        )
    )


    covariates = (
        configuration.get(
            "covariates",
            []
        )
    )


    covariate_text = (
        ", ".join(
            covariates
        )
        if covariates
        else
        "the selected covariates"
    )


    significant = (
        factor_result.get(
            "significant",
            False,
        )
    )


    return {
        "title":
            (
                "Detailed Explanation — "
                "Analysis of Covariance (ANCOVA)"
            ),

        "introduction":
            (
                "ANCOVA combines analysis of variance "
                "and regression. It compares the mean "
                "outcome between categorical groups "
                "while statistically adjusting for one "
                "or more continuous covariates."
            ),

        "sections": [
            {
                "title":
                    "1. Analysis performed",

                "paragraphs": [
                    (
                        f"SSAS performed an ANCOVA with "
                        f"{dependent} as the dependent variable, "
                        f"{factor} as the categorical factor, "
                        f"and {covariate_text} as covariate(s)."
                    ),
                ],
            },

            {
                "title":
                    "2. Why ANCOVA is used",

                "paragraphs": [
                    (
                        "ANCOVA is appropriate when the user "
                        "wants to compare groups while controlling "
                        "for other quantitative variables that "
                        "may also be associated with the outcome."
                    ),
                    (
                        "The resulting group comparison therefore "
                        "represents an adjusted comparison rather "
                        "than a comparison of raw group means."
                    ),
                ],
            },

            {
                "title":
                    "3. Adjusted factor effect",

                "paragraphs": [
                    (
                        f"The adjusted test of {factor} produced "
                        f"F = {factor_result.get('F')}, "
                        f"p = {factor_result.get('p')}."
                    ),
                    (
                        (
                            f"The adjusted factor effect was "
                            f"statistically significant."
                        )
                        if significant
                        else
                        (
                            f"The adjusted factor effect was "
                            f"not statistically significant."
                        )
                    ),
                ],
            },

            {
                "title":
                    "4. Effect size",

                "paragraphs": [
                    (
                        f"The partial eta squared for {factor} "
                        f"was "
                        f"{factor_result.get('partial_eta_squared')}. "
                        f"SSAS classified this as a "
                        f"{str(factor_result.get('effect_size', '')).lower()} "
                        f"effect."
                    ),
                    (
                        "Partial eta squared estimates the "
                        "proportion of effect-plus-error variance "
                        "associated with the adjusted factor effect."
                    ),
                ],
            },

            {
                "title":
                    "5. Covariates",

                "paragraphs": [
                    (
                        f"The model statistically controls for "
                        f"{covariate_text}."
                    ),
                    (
                        "Each covariate is also tested while "
                        "holding the factor and other covariates "
                        "constant."
                    ),
                ],
            },

            {
                "title":
                    "6. Adjusted means",

                "paragraphs": [
                    (
                        "Adjusted means estimate the expected "
                        "outcome for each factor group when the "
                        "covariates are held at their overall "
                        "sample means."
                    ),
                    (
                        "These adjusted means are more appropriate "
                        "for interpreting ANCOVA group differences "
                        "than the unadjusted raw means."
                    ),
                ],
            },

            {
                "title":
                    "7. Homogeneity of regression slopes",

                "paragraphs": [
                    (
                        "ANCOVA assumes that the relationship "
                        "between each covariate and the dependent "
                        "variable is reasonably similar across "
                        "factor groups."
                    ),
                    (
                        "SSAS evaluates this using factor-by-"
                        "covariate interaction terms. A significant "
                        "interaction suggests that the standard "
                        "ANCOVA model should be interpreted with "
                        "caution."
                    ),
                ],
            },

            {
                "title":
                    "8. Homogeneity of variance",

                "paragraphs": [
                    (
                        "Levene's test is used to evaluate whether "
                        "the variability of the dependent variable "
                        "is reasonably similar across factor groups."
                    ),
                ],
            },

            {
                "title":
                    "9. Residual normality",

                "paragraphs": [
                    (
                        "The Shapiro-Wilk test is used as one "
                        "diagnostic for residual normality."
                    ),
                    (
                        "With large datasets, small departures "
                        "from normality may become statistically "
                        "significant even when the ANCOVA estimates "
                        "remain practically useful."
                    ),
                ],
            },

            {
                "title":
                    "10. Independence",

                "paragraphs": [
                    (
                        "ANCOVA also assumes independent "
                        "observations. Independence normally "
                        "depends on how the data were collected "
                        "and cannot be established solely from "
                        "the numerical dataset."
                    ),
                ],
            },

            {
                "title":
                    "11. Statistical interpretation",

                "paragraphs": [
                    result.get(
                        "interpretation",
                        ""
                    ),
                ],
            },

            {
                "title":
                    "12. Important limitation",

                "paragraphs": [
                    (
                        "Statistical adjustment does not prove "
                        "causation. ANCOVA describes adjusted "
                        "associations and group differences under "
                        "the fitted model."
                    ),
                    (
                        "Results should be interpreted alongside "
                        "study design, measurement quality, "
                        "missing-data patterns and subject-matter "
                        "knowledge."
                    ),
                ],
            },

            {
                "title":
                    "13. Conclusion",

                "paragraphs": [
                    (
                        f"The ANCOVA evaluates whether groups "
                        f"defined by {factor} differ in "
                        f"{dependent} after accounting for "
                        f"{covariate_text}."
                    ),
                ],
            },
        ],
    }
