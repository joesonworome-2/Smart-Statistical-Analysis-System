def build_cluster_explanation(result):
    configuration = result.get(
        "configuration",
        {},
    )

    summary = result.get(
        "summary",
        {},
    )

    method = configuration.get(
        "method",
        "kmeans",
    )

    if method == "hierarchical":
        method_name = (
            "Hierarchical Agglomerative Clustering"
        )

        method_description = (
            "Hierarchical clustering progressively "
            "combines observations into groups using "
            "their similarity. SSAS uses Ward linkage "
            "for this implementation."
        )

    else:
        method_name = (
            "K-Means Clustering"
        )

        method_description = (
            "K-means attempts to divide observations "
            "into clusters so that observations within "
            "the same cluster are similar while clusters "
            "remain different from one another."
        )

    return {
        "title":
            (
                "Detailed Explanation — "
                "Cluster Analysis"
            ),

        "introduction":
            (
                "Cluster analysis is an unsupervised "
                "statistical learning method used to "
                "discover groups of similar observations "
                "without requiring a predefined outcome."
            ),

        "sections": [
            {
                "title":
                    "1. Analysis performed",

                "paragraphs": [
                    (
                        f"SSAS performed {method_name} "
                        f"using {summary.get('n')} complete "
                        f"observations and "
                        f"{summary.get('variables')} variables."
                    ),
                    method_description,
                ],
            },

            {
                "title":
                    "2. Number of clusters",

                "paragraphs": [
                    (
                        f"The final solution contained "
                        f"{summary.get('clusters')} clusters."
                    ),
                    (
                        "When automatic selection is enabled, "
                        "SSAS compares candidate cluster "
                        "solutions and selects the solution "
                        "with the highest silhouette score."
                    ),
                ],
            },

            {
                "title":
                    "3. Standardization",

                "paragraphs": [
                    (
                        f"Standardization was "
                        f"{'enabled' if configuration.get('standardize') else 'disabled'}."
                    ),
                    (
                        "Standardization is normally recommended "
                        "when selected variables use different "
                        "measurement scales because otherwise "
                        "variables with large numerical ranges "
                        "can dominate distance calculations."
                    ),
                ],
            },

            {
                "title":
                    "4. Silhouette score",

                "paragraphs": [
                    (
                        f"The silhouette score was "
                        f"{summary.get('silhouette_score')}."
                    ),
                    (
                        f"SSAS classified the cluster separation "
                        f"as {summary.get('assessment')}."
                    ),
                    (
                        "Silhouette values closer to 1 indicate "
                        "better separation between clusters. "
                        "Values near 0 indicate overlapping "
                        "groups, while negative values may "
                        "indicate poorly assigned observations."
                    ),
                ],
            },

            {
                "title":
                    "5. Cluster sizes",

                "paragraphs": [
                    (
                        "The Cluster Sizes table shows how "
                        "many observations belong to each group "
                        "and the percentage of the analysed "
                        "sample represented by each cluster."
                    ),
                ],
            },

            {
                "title":
                    "6. Cluster centers",

                "paragraphs": [
                    (
                        "Cluster centers describe the average "
                        "value of each selected variable within "
                        "each cluster."
                    ),
                    (
                        "These averages help characterize and "
                        "compare the groups discovered by the "
                        "clustering algorithm."
                    ),
                ],
            },

            {
                "title":
                    "7. Standardized profiles",

                "paragraphs": [
                    (
                        "Standardized cluster profiles report "
                        "cluster means in standard-deviation "
                        "units relative to the overall sample."
                    ),
                    (
                        "Positive values indicate above-average "
                        "levels and negative values indicate "
                        "below-average levels."
                    ),
                ],
            },

            {
                "title":
                    "8. Variable contribution",

                "paragraphs": [
                    (
                        "SSAS reports how strongly each selected "
                        "variable contributes to separation among "
                        "the discovered clusters."
                    ),
                    (
                        "Variables with larger between-cluster "
                        "variance proportions are more useful "
                        "for describing differences among groups."
                    ),
                ],
            },

            {
                "title":
                    "9. Cluster assignments",

                "paragraphs": [
                    (
                        "Each analysed observation receives "
                        "a cluster label. SSAS displays a preview "
                        "of these assignments in Statistical "
                        "Analysis."
                    ),
                ],
            },

            {
                "title":
                    "10. Interpretation",

                "paragraphs": [
                    result.get(
                        "interpretation",
                        "",
                    ),
                ],
            },

            {
                "title":
                    "11. Important limitation",

                "paragraphs": [
                    (
                        "Cluster analysis is exploratory. "
                        "Clusters are generated from the selected "
                        "variables, scaling method, algorithm and "
                        "requested number of groups."
                    ),
                    (
                        "The resulting clusters should therefore "
                        "not automatically be treated as true "
                        "or permanent population categories."
                    ),
                ],
            },

            {
                "title":
                    "12. Validation",

                "paragraphs": [
                    (
                        "A useful cluster solution should ideally "
                        "be evaluated using separation measures, "
                        "domain knowledge and, when possible, "
                        "replication on new observations."
                    ),
                ],
            },

            {
                "title":
                    "13. Visualization",

                "paragraphs": [
                    (
                        "Cluster scatter plots, PCA projections "
                        "and dendrograms are intentionally kept "
                        "outside Statistical Analysis and can "
                        "later be implemented in the SSAS "
                        "Visualization module."
                    ),
                ],
            },
        ],
    }
