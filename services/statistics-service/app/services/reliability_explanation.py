def build_reliability_explanation(
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


    items = (
        configuration.get(
            "variables",
            []
        )
    )


    return {
        "title":
            (
                "Detailed Explanation — "
                "Reliability Analysis"
            ),

        "introduction":
            (
                "Reliability analysis evaluates how "
                "consistently a set of items operates "
                "as a scale. SSAS uses Cronbach's alpha "
                "as the primary internal-consistency "
                "coefficient."
            ),

        "sections": [
            {
                "title":
                    "1. Analysis performed",

                "paragraphs": [
                    (
                        f"SSAS evaluated "
                        f"{summary.get('items')} selected "
                        f"items using "
                        f"{summary.get('n')} complete "
                        f"observations."
                    ),
                    (
                        "The selected items were: "
                        +
                        ", ".join(
                            items
                        )
                        +
                        "."
                    ),
                ],
            },

            {
                "title":
                    "2. Cronbach's alpha",

                "paragraphs": [
                    (
                        f"The estimated Cronbach's alpha "
                        f"was "
                        f"{summary.get('cronbach_alpha')}."
                    ),
                    (
                        f"SSAS classified the observed "
                        f"internal consistency as "
                        f"{summary.get('assessment')}."
                    ),
                    (
                        "Cronbach's alpha measures the "
                        "internal consistency of a set "
                        "of items. Higher values generally "
                        "indicate stronger relationships "
                        "among the items."
                    ),
                ],
            },

            {
                "title":
                    "3. Standardized alpha",

                "paragraphs": [
                    (
                        f"The standardized alpha was "
                        f"{summary.get('standardized_alpha')}."
                    ),
                    (
                        "Standardized alpha is calculated "
                        "from the correlation matrix and can "
                        "be useful when items have different "
                        "variances or measurement scales."
                    ),
                ],
            },

            {
                "title":
                    "4. Average inter-item correlation",

                "paragraphs": [
                    (
                        f"The average inter-item correlation "
                        f"was "
                        f"{summary.get('average_inter_item_correlation')}."
                    ),
                    (
                        "This statistic describes the typical "
                        "relationship between pairs of scale items."
                    ),
                ],
            },

            {
                "title":
                    "5. Corrected item-total correlation",

                "paragraphs": [
                    (
                        "The corrected item-total correlation "
                        "compares each item with the total score "
                        "formed from all of the other items."
                    ),
                    (
                        "Weak values may suggest that an item "
                        "does not behave consistently with the "
                        "remaining scale. Negative values may "
                        "also indicate a reverse-coded item that "
                        "has not been recoded."
                    ),
                ],
            },

            {
                "title":
                    "6. Alpha if item deleted",

                "paragraphs": [
                    (
                        "The Alpha if Item Deleted statistic "
                        "shows what Cronbach's alpha would become "
                        "if a particular item were removed."
                    ),
                    (
                        "An increase does not automatically mean "
                        "the item should be removed. Item content, "
                        "construct coverage and theory should also "
                        "be considered."
                    ),
                ],
            },

            {
                "title":
                    "7. Inter-item correlations",

                "paragraphs": [
                    (
                        "The inter-item correlation matrix "
                        "shows the pairwise relationships among "
                        "the selected scale items."
                    ),
                    (
                        "Negative correlations should be "
                        "investigated because they may indicate "
                        "reverse wording, incorrect coding or "
                        "items measuring a different construct."
                    ),
                ],
            },

            {
                "title":
                    "8. Split-half reliability",

                "paragraphs": [
                    (
                        "SSAS additionally reports an odd-even "
                        "split-half reliability diagnostic."
                    ),
                    (
                        "The Spearman-Brown coefficient adjusts "
                        "the correlation between the two halves "
                        "to estimate reliability for the complete "
                        "scale."
                    ),
                ],
            },

            {
                "title":
                    "9. Missing data",

                "paragraphs": [
                    (
                        f"SSAS used complete-case analysis. "
                        f"{summary.get('excluded_cases')} "
                        f"observation(s) were excluded because "
                        f"one or more selected items were missing "
                        f"or non-numeric."
                    ),
                ],
            },

            {
                "title":
                    "10. Dimensionality",

                "paragraphs": [
                    (
                        "A high Cronbach's alpha does not prove "
                        "that the scale measures only one "
                        "underlying construct."
                    ),
                    (
                        "EFA or PCA should be considered when "
                        "evaluating whether the selected items "
                        "form one dimension or multiple dimensions."
                    ),
                ],
            },

            {
                "title":
                    "11. Number of items",

                "paragraphs": [
                    (
                        "Cronbach's alpha is influenced by the "
                        "number of scale items. A scale containing "
                        "many similar items can obtain a high alpha "
                        "even when the average item relationship "
                        "is only moderate."
                    ),
                ],
            },

            {
                "title":
                    "12. Interpretation",

                "paragraphs": [
                    result.get(
                        "interpretation",
                        "",
                    ),
                ],
            },

            {
                "title":
                    "13. Important limitation",

                "paragraphs": [
                    (
                        "Reliability does not establish validity. "
                        "A scale can measure something consistently "
                        "without necessarily measuring the intended "
                        "construct."
                    ),
                    (
                        "Reliability should therefore be interpreted "
                        "alongside content validity, construct "
                        "validity, dimensionality and the design "
                        "of the instrument."
                    ),
                ],
            },

            {
                "title":
                    "14. Conclusion",

                "paragraphs": [
                    (
                        f"The selected scale obtained a "
                        f"Cronbach's alpha of "
                        f"{summary.get('cronbach_alpha')} "
                        f"and was classified as "
                        f"{summary.get('assessment')}."
                    ),
                ],
            },
        ],
    }
