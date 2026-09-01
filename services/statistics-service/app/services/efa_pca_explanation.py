def build_efa_pca_explanation(
    result,
):
    configuration = (
        result.get(
            "configuration",
            {}
        )
    )

    summary = (
        result.get(
            "summary",
            {}
        )
    )

    method = (
        configuration.get(
            "method",
            "pca",
        )
    )

    retained = (
        configuration.get(
            "n_factors"
        )
    )

    rotation = (
        configuration.get(
            "rotation",
            "None",
        )
    )

    if method == "efa":

        method_name = (
            "Exploratory Factor Analysis"
        )

        structure_name = (
            "factor"
        )

        purpose = (
            "identify underlying latent constructs "
            "that may account for correlations among "
            "the observed variables"
        )

    else:

        method_name = (
            "Principal Component Analysis"
        )

        structure_name = (
            "component"
        )

        purpose = (
            "reduce a larger set of correlated "
            "variables into a smaller number of "
            "components while retaining as much "
            "information as possible"
        )


    return {
        "title":
            (
                "Detailed Explanation — "
                f"{method_name}"
            ),

        "introduction":
            (
                f"{method_name} was used to "
                f"{purpose}."
            ),

        "sections": [
            {
                "title":
                    "1. Analysis performed",

                "paragraphs": [
                    (
                        f"SSAS analysed "
                        f"{summary.get('variables')} selected "
                        f"variables using "
                        f"{summary.get('n')} complete observations."
                    ),
                    (
                        f"The selected method was "
                        f"{method_name}."
                    ),
                ],
            },

            {
                "title":
                    "2. KMO measure",

                "paragraphs": [
                    (
                        f"The overall Kaiser-Meyer-Olkin "
                        f"measure was "
                        f"{summary.get('kmo')}."
                    ),
                    (
                        f"SSAS classified this value as "
                        f"{summary.get('kmo_assessment')}."
                    ),
                    (
                        "KMO evaluates whether correlations "
                        "among variables are sufficiently "
                        "compact for extraction of a smaller "
                        "underlying structure."
                    ),
                ],
            },

            {
                "title":
                    "3. Bartlett's test",

                "paragraphs": [
                    (
                        f"Bartlett's test produced "
                        f"χ² = "
                        f"{summary.get('bartlett_chi_square')}, "
                        f"df = "
                        f"{summary.get('bartlett_df')}, "
                        f"p = "
                        f"{summary.get('bartlett_p')}."
                    ),
                    (
                        "A statistically significant Bartlett "
                        "test indicates that the correlation "
                        "matrix differs from an identity matrix, "
                        "supporting the presence of relationships "
                        "that may be summarised by factors or "
                        "components."
                    ),
                ],
            },

            {
                "title":
                    "4. Number retained",

                "paragraphs": [
                    (
                        f"SSAS retained {retained} "
                        f"{structure_name}(s)."
                    ),
                    (
                        f"The automatically suggested number "
                        f"using the Kaiser eigenvalue-greater-than-"
                        f"one criterion was "
                        f"{configuration.get('automatic_factor_count')}."
                    ),
                ],
            },

            {
                "title":
                    "5. Eigenvalues",

                "paragraphs": [
                    (
                        "Eigenvalues describe how much "
                        "variance is associated with each "
                        "dimension. Larger eigenvalues indicate "
                        "dimensions that account for more "
                        "information in the selected variables."
                    ),
                ],
            },

            {
                "title":
                    "6. Variance explained",

                "paragraphs": [
                    (
                        "The variance-explained table reports "
                        "the percentage of total standardized "
                        "variance represented by each component."
                    ),
                    (
                        "Cumulative variance shows how much "
                        "information is retained as additional "
                        "dimensions are included."
                    ),
                ],
            },

            {
                "title":
                    "7. Communalities",

                "paragraphs": [
                    (
                        "Communality represents the proportion "
                        "of a variable's variance reproduced by "
                        "the retained dimensions."
                    ),
                    (
                        "Very low communalities may indicate "
                        "variables that are poorly represented "
                        "by the extracted structure."
                    ),
                ],
            },

            {
                "title":
                    "8. Loadings",

                "paragraphs": [
                    (
                        "A loading describes the relationship "
                        "between an observed variable and an "
                        f"extracted {structure_name}."
                    ),
                    (
                        "Larger absolute loadings indicate "
                        "stronger relationships. Positive and "
                        "negative signs describe direction."
                    ),
                ],
            },

            {
                "title":
                    "9. Rotation",

                "paragraphs": [
                    (
                        f"The selected rotation was "
                        f"{rotation}."
                    ),
                    (
                        "Varimax is an orthogonal rotation "
                        "that attempts to produce a clearer "
                        "loading pattern by encouraging each "
                        "variable to load strongly on fewer "
                        "dimensions."
                    ),
                ],
            },

            {
                "title":
                    "10. EFA versus PCA",

                "paragraphs": [
                    (
                        "PCA and EFA are related but answer "
                        "different questions."
                    ),
                    (
                        "PCA focuses on data reduction using "
                        "total observed variance. EFA focuses "
                        "on modelling common variance in order "
                        "to investigate possible latent factors."
                    ),
                ],
            },

            {
                "title":
                    "11. Interpretation",

                "paragraphs": [
                    result.get(
                        "interpretation",
                        "",
                    ),
                ],
            },

            {
                "title":
                    "12. Sample size",

                "paragraphs": [
                    (
                        "Factor and component solutions become "
                        "more stable with larger samples. "
                        "KMO, communalities, number of variables "
                        "and strength of correlations should be "
                        "considered alongside the raw number of "
                        "observations."
                    ),
                ],
            },

            {
                "title":
                    "13. Visualization",

                "paragraphs": [
                    (
                        "A scree plot is not displayed inside "
                        "Statistical Analysis because SSAS keeps "
                        "graphs in the Visualization module."
                    ),
                ],
            },

            {
                "title":
                    "14. Important limitation",

                "paragraphs": [
                    (
                        "The retained structure should not be "
                        "interpreted solely from automatic rules. "
                        "Subject-matter knowledge, theory, loading "
                        "patterns and replication should also be "
                        "considered."
                    ),
                ],
            },

            {
                "title":
                    "15. Conclusion",

                "paragraphs": [
                    (
                        f"The analysis extracted "
                        f"{retained} {structure_name}(s) from "
                        f"the selected variables and reports "
                        f"their eigenvalues, communalities, "
                        f"loadings and rotated structure."
                    ),
                ],
            },
        ],
    }
