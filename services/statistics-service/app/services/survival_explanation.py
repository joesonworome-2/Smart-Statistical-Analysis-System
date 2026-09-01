def build_survival_explanation(
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

    logrank = (
        result.get(
            "logrank_result"
        )
    )

    duration = (
        configuration.get(
            "duration_variable",
            "duration",
        )
    )

    event_variable = (
        configuration.get(
            "event_variable",
            "event",
        )
    )

    event_value = (
        configuration.get(
            "event_value",
            "1",
        )
    )

    group = (
        configuration.get(
            "group_variable"
        )
    )

    sections = [
        {
            "title":
                "1. Analysis performed",

            "paragraphs": [
                (
                    f"SSAS performed Kaplan-Meier "
                    f"survival analysis using {duration} "
                    f"as the time-to-event variable."
                ),
                (
                    f"An observation was treated as "
                    f"having experienced the event when "
                    f"{event_variable} equalled "
                    f"{event_value}."
                ),
            ],
        },

        {
            "title":
                "2. What survival analysis measures",

            "paragraphs": [
                (
                    "Survival analysis estimates the "
                    "probability that the event of interest "
                    "has not yet occurred by each observed "
                    "time point."
                ),
                (
                    "The method is specifically designed "
                    "to accommodate censored observations."
                ),
            ],
        },

        {
            "title":
                "3. Censoring",

            "paragraphs": [
                (
                    f"The analysis contained "
                    f"{summary.get('events')} observed "
                    f"events and "
                    f"{summary.get('censored')} censored "
                    f"observations."
                ),
                (
                    "A censored observation contributes "
                    "follow-up information until its "
                    "last observed duration even though "
                    "the event was not observed."
                ),
            ],
        },

        {
            "title":
                "4. Kaplan-Meier estimate",

            "paragraphs": [
                (
                    "The Kaplan-Meier estimator updates "
                    "the estimated survival probability "
                    "whenever one or more events occur."
                ),
                (
                    "The Kaplan-Meier Estimates table "
                    "reports the number at risk, observed "
                    "events, censored observations, "
                    "survival probability, standard error "
                    "and confidence interval."
                ),
            ],
        },

        {
            "title":
                "5. Median survival",

            "paragraphs": [
                (
                    (
                        f"The overall estimated median "
                        f"survival time was "
                        f"{summary.get('median_survival')}."
                    )
                    if summary.get(
                        "median_survival"
                    )
                    is not None
                    else
                    (
                        "The median survival time was not "
                        "reached during the observed "
                        "follow-up period."
                    )
                ),
                (
                    "Median survival is the time at "
                    "which the estimated survival "
                    "probability falls to 0.50 or below."
                ),
            ],
        },

        {
            "title":
                "6. Restricted mean survival time",

            "paragraphs": [
                (
                    f"The restricted mean survival time "
                    f"over the observed follow-up period "
                    f"was "
                    f"{summary.get('restricted_mean_survival')}."
                ),
                (
                    "This represents the area under the "
                    "estimated survival curve up to the "
                    "maximum analysed follow-up time."
                ),
            ],
        },
    ]

    if group:
        sections.append({
            "title":
                "7. Group comparison",

            "paragraphs": [
                (
                    f"Survival was compared across "
                    f"levels of {group}."
                ),
                (
                    "The log-rank test evaluates whether "
                    "the survival distributions differ "
                    "between groups across the observed "
                    "follow-up period."
                ),
            ],
        })

        if logrank:
            sections.append({
                "title":
                    "8. Log-rank test",

                "paragraphs": [
                    (
                        f"The log-rank statistic was "
                        f"χ² = "
                        f"{logrank.get('chi_square')}, "
                        f"with {logrank.get('df')} "
                        f"degree(s) of freedom and "
                        f"p = {logrank.get('p')}."
                    ),
                ],
            })

    sections.extend([
        {
            "title":
                "9. Independent censoring",

            "paragraphs": [
                (
                    "Kaplan-Meier estimation assumes "
                    "that censoring is non-informative. "
                    "In practical terms, censored "
                    "participants should not systematically "
                    "have different future event risks "
                    "because of the reason they were censored."
                ),
                (
                    "This assumption is primarily evaluated "
                    "from the study design rather than "
                    "from a statistical test."
                ),
            ],
        },

        {
            "title":
                "10. Independence",

            "paragraphs": [
                (
                    "Observations should generally be "
                    "independent. Repeated observations "
                    "from the same subject or clustered "
                    "samples require more specialised "
                    "survival methods."
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
                "12. Important limitation",

            "paragraphs": [
                (
                    "Survival analysis describes the "
                    "observed time-to-event process and "
                    "does not by itself establish causation."
                ),
                (
                    "Results depend on correct event "
                    "coding, meaningful duration values, "
                    "appropriate censoring and the quality "
                    "of the underlying data."
                ),
            ],
        },

        {
            "title":
                "13. Visualization",

            "paragraphs": [
                (
                    "Kaplan-Meier survival curves are not "
                    "displayed inside the Statistical "
                    "Analysis module because SSAS keeps "
                    "graphical output in the Visualization "
                    "module."
                ),
            ],
        },

        {
            "title":
                "14. Conclusion",

            "paragraphs": [
                (
                    "The analysis provides estimated "
                    "survival probabilities, median "
                    "survival where estimable, censoring "
                    "information and, when a grouping "
                    "variable is supplied, statistical "
                    "comparison of survival distributions."
                ),
            ],
        },
    ])

    return {
        "title":
            (
                "Detailed Explanation — "
                "Survival Analysis"
            ),

        "introduction":
            (
                "Survival analysis examines the time "
                "until an event occurs while accounting "
                "for observations for which the event "
                "has not yet been observed."
            ),

        "sections":
            sections,
    }
