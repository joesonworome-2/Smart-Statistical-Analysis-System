from __future__ import annotations

from math import isfinite
from typing import Any


# ============================================================
# Small helpers
# ============================================================


def _norm(value: Any) -> str:
    text = str(value or "").lower()
    text = (
        text
        .replace("²", "2")
        .replace("β", "beta")
        .replace("α", "alpha")
        .replace("%", "percent")
    )
    return "".join(
        character
        for character in text
        if character.isalnum()
    )


def _human(value: Any) -> str:
    return (
        str(value or "")
        .replace("_", " ")
        .replace("-", " ")
        .strip()
        .title()
    )


def _num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None

    try:
        if value is None:
            return None

        if isinstance(value, str):
            cleaned = (
                value.strip()
                .replace(",", "")
                .replace("%", "")
            )

            if cleaned in {
                "",
                "-",
                "--",
                "—",
                "nan",
                "None",
            }:
                return None

            value = cleaned

        number = float(value)

        if not isfinite(number):
            return None

        return number

    except Exception:
        return None


def _fmt(value: Any) -> str:
    number = _num(value)

    if number is None:
        if value is None:
            return "not available"
        return str(value)

    if abs(number) >= 1000:
        return f"{number:,.3f}".rstrip("0").rstrip(".")

    if number != 0 and abs(number) < 0.001:
        return f"{number:.4e}"

    return f"{number:.4f}".rstrip("0").rstrip(".")


def _row_value(
    row: Any,
    column: Any,
    column_index: int,
) -> Any:
    if isinstance(row, dict):
        if column in row:
            return row.get(column)

        normalized = {
            _norm(key): value
            for key, value in row.items()
        }

        wanted = _norm(column)

        if wanted in normalized:
            return normalized[wanted]

        aliases = {
            "pvalue": ["p", "pvalue", "sig", "significance"],
            "r2": ["r2", "rsquared"],
            "adjustedr2": ["adjustedr2", "adjustedrsquared", "adjr2"],
            "stderror": ["stderror", "standarderror", "stderr", "se"],
            "stddeviation": ["stddeviation", "standarddeviation", "stddev", "sd"],
            "standardizedbeta": ["standardizedbeta", "beta", "stdbeta"],
            "cilower": ["cilower", "lowerci", "lower", "lowerbound"],
            "ciupper": ["ciupper", "upperci", "upper", "upperbound"],
            "meansquare": ["meansquare", "ms"],
            "sumofsquares": ["sumofsquares", "ss"],
        }

        for candidate in aliases.get(wanted, []):
            if candidate in normalized:
                return normalized[candidate]

        return None

    if isinstance(row, (list, tuple)):
        if column_index < len(row):
            return row[column_index]

    return None


def _as_dict_rows(
    table: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]]]:
    columns = table.get("columns") or []
    rows = table.get("rows") or []

    if not columns and rows and isinstance(rows[0], dict):
        columns = list(rows[0].keys())

    columns = [str(column) for column in columns]
    output: list[dict[str, Any]] = []

    for row in rows:
        output.append(
            {
                column: _row_value(row, column, index)
                for index, column in enumerate(columns)
            }
        )

    return columns, output


def _find_column(
    columns: list[str],
    candidates: tuple[str, ...],
) -> str | None:
    wanted = {_norm(item) for item in candidates}

    for column in columns:
        if _norm(column) in wanted:
            return column

    return None


def _row_lookup(
    row: dict[str, Any],
    candidates: tuple[str, ...],
) -> Any:
    normalized = {
        _norm(key): value
        for key, value in row.items()
    }

    for candidate in candidates:
        key = _norm(candidate)
        if key in normalized:
            return normalized[key]

    return None


def _analysis_raw(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    metadata = analysis.get("metadata")

    if isinstance(metadata, dict):
        raw = metadata.get("raw_result")
        if isinstance(raw, dict):
            return raw

    raw = analysis.get("results")
    if isinstance(raw, dict):
        return raw

    return {}


def _configuration(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    raw = _analysis_raw(analysis)

    raw_config = raw.get("configuration")
    if isinstance(raw_config, dict) and raw_config:
        return raw_config

    config = analysis.get("configuration")
    if isinstance(config, dict):
        return config

    return {}


def _config_value(
    config: dict[str, Any],
    candidates: tuple[str, ...],
    default: Any = None,
) -> Any:
    normalized = {
        _norm(key): value
        for key, value in config.items()
    }

    for candidate in candidates:
        key = _norm(candidate)
        if key in normalized:
            return normalized[key]

    return default


def _alpha(
    analysis: dict[str, Any],
) -> float:
    config = _configuration(analysis)
    value = _config_value(
        config,
        ("alpha", "significance_level", "significance"),
        0.05,
    )
    return _num(value) or 0.05


def _dependent_variable(
    analysis: dict[str, Any],
) -> str:
    config = _configuration(analysis)
    value = _config_value(
        config,
        (
            "dependent_variable",
            "dependent",
            "outcome",
            "target",
            "response_variable",
            "response",
            "y",
        ),
    )

    if isinstance(value, list):
        return ", ".join(str(item) for item in value)

    return str(value or "the outcome variable")


def _predictors(
    analysis: dict[str, Any],
) -> str:
    config = _configuration(analysis)
    value = _config_value(
        config,
        (
            "predictors",
            "independent_variables",
            "independent_variable",
            "covariates",
            "x",
        ),
    )

    if isinstance(value, list):
        return ", ".join(str(item) for item in value)

    return str(value or "the predictor variable(s)")


def _append_unique(
    sections: list[dict[str, str]],
    seen: set[str],
    title: str,
    text: str,
) -> None:
    cleaned = " ".join(str(text or "").split())

    if not cleaned:
        return

    signature = _norm(title + " " + cleaned)

    if signature in seen:
        return

    seen.add(signature)
    sections.append(
        {
            "title": title,
            "text": cleaned,
        }
    )


# ============================================================
# Descriptive statistics
# ============================================================


_DESCRIPTIVE_ALIASES = {
    "n": {"n", "count", "numberofvalues", "validn", "observations"},
    "mean": {"mean", "average", "arithmeticmean"},
    "median": {"median"},
    "mode": {"mode"},
    "std": {"std", "sd", "stddev", "stddeviation", "standarddeviation"},
    "variance": {"variance", "var"},
    "min": {"min", "minimum"},
    "max": {"max", "maximum"},
    "range": {"range"},
    "q1": {"q1", "firstquartile", "quartile1", "25thpercentile", "p25"},
    "q3": {"q3", "thirdquartile", "quartile3", "75thpercentile", "p75"},
    "iqr": {"iqr", "interquartilerange"},
    "skewness": {"skewness", "skew"},
    "kurtosis": {"kurtosis", "kurt"},
    "missing": {"missing", "missingvalues", "nmissing"},
}


def _canonical_descriptive_stat(value: Any) -> str | None:
    normalized = _norm(value)

    for canonical, aliases in _DESCRIPTIVE_ALIASES.items():
        if normalized in aliases:
            return canonical

    return None


def _descriptive_variables(
    table: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    columns, rows = _as_dict_rows(table)

    if not columns or not rows:
        return {}

    first = columns[0]
    first_norm = _norm(first)

    result: dict[str, dict[str, Any]] = {}

    # Layout A:
    # Statistic | Quantity | TotalPrice | ...
    if first_norm in {
        "statistic",
        "measure",
        "summary",
    }:
        for variable in columns[1:]:
            metrics: dict[str, Any] = {}

            for row in rows:
                stat = _canonical_descriptive_stat(
                    row.get(first)
                )

                if stat:
                    metrics[stat] = row.get(variable)

            if metrics:
                result[str(variable)] = metrics

        return result

    # Layout B:
    # Variable | N | Mean | Median | SD | ...
    metric_columns = {
        column: _canonical_descriptive_stat(column)
        for column in columns[1:]
    }

    if any(metric_columns.values()):
        for row_index, row in enumerate(rows, 1):
            variable = str(
                row.get(first)
                or f"Variable {row_index}"
            )

            metrics: dict[str, Any] = {}

            for column, stat in metric_columns.items():
                if stat:
                    metrics[stat] = row.get(column)

            if metrics:
                result[variable] = metrics

    return result


def _interpret_descriptive_table(
    table: dict[str, Any],
) -> list[dict[str, str]]:
    variables = _descriptive_variables(table)
    sections: list[dict[str, str]] = []

    for variable, metrics in variables.items():
        sentences: list[str] = []

        n = _num(metrics.get("n"))
        mean = _num(metrics.get("mean"))
        median = _num(metrics.get("median"))
        std = _num(metrics.get("std"))
        variance = _num(metrics.get("variance"))
        minimum = _num(metrics.get("min"))
        maximum = _num(metrics.get("max"))
        range_value = _num(metrics.get("range"))
        q1 = _num(metrics.get("q1"))
        q3 = _num(metrics.get("q3"))
        iqr = _num(metrics.get("iqr"))
        skewness = _num(metrics.get("skewness"))
        kurtosis = _num(metrics.get("kurtosis"))
        missing = _num(metrics.get("missing"))
        mode = metrics.get("mode")

        if n is not None:
            sentences.append(
                f"Number of values (N): {int(n):,} valid observations of {variable} were used. "
                "N tells you how much observed information contributes to the descriptive summary; "
                "it is not itself a measure of center or spread."
            )

        if mean is not None:
            sentences.append(
                f"Mean: the mean is the arithmetic average of {variable} across the valid cases. "
                f"For this dataset the average {variable} is {_fmt(mean)}. "
                "It uses every observation, so unusually high or low values can pull it away from the typical case."
            )

        if median is not None:
            comparison = ""

            if mean is not None:
                difference = abs(mean - median)
                reference = abs(std) if std not in (None, 0) else max(abs(mean), 1.0)

                if difference <= 0.1 * reference:
                    comparison = (
                        " The mean and median are close relative to the observed spread, so the two measures of center "
                        "give a similar picture of the typical value."
                    )
                else:
                    direction = "above" if mean > median else "below"
                    comparison = (
                        f" The mean lies {direction} the median, which indicates that the center depends on which summary is used "
                        "and may reflect asymmetry or influential extreme values."
                    )

            sentences.append(
                f"Median: the median is the middle value of {variable} after the observations are ordered. "
                f"A median of {_fmt(median)} means approximately half of the observed values are at or below this point and half are at or above it."
                f"{comparison}"
            )

        if mode not in (None, "", "—"):
            sentences.append(
                f"Mode: the mode identifies the most frequently occurring observed value or category of {variable}. "
                f"Here the most common value/category is {_fmt(mode)}. This is especially useful for categorical or discrete variables."
            )

        if std is not None:
            relative = ""

            if mean not in (None, 0):
                percent = abs(std / mean) * 100
                relative = (
                    f" Relative to the absolute mean, the standard deviation is about {percent:.1f}% of the mean, "
                    "which provides scale-aware context for the amount of variation."
                )

            sentences.append(
                f"Standard deviation: standard deviation describes how far {variable} values typically spread around their mean. "
                f"A standard deviation of {_fmt(std)} means observations commonly differ from the mean by roughly {_fmt(std)} {variable} units, "
                "although it is not a hard boundary around individual observations."
                f"{relative}"
            )

        if variance is not None:
            sentences.append(
                f"Variance: variance measures dispersion using squared deviations from the mean. "
                f"For {variable} the variance is {_fmt(variance)} in squared units. "
                "It is mathematically useful, while the standard deviation is usually easier to interpret because it returns to the original measurement units."
            )

        if minimum is not None:
            sentences.append(
                f"Minimum: {_fmt(minimum)} is the smallest observed {variable} value in the analyzed data. "
                "It marks the lower observed endpoint rather than an expected lower limit for the wider population."
            )

        if maximum is not None:
            sentences.append(
                f"Maximum: {_fmt(maximum)} is the largest observed {variable} value in the analyzed data. "
                "It marks the upper observed endpoint and should be considered together with the minimum and spread statistics."
            )

        if range_value is None and minimum is not None and maximum is not None:
            range_value = maximum - minimum

        if range_value is not None:
            sentences.append(
                f"Range: the range measures the full observed span from the smallest to the largest {variable} value. "
                f"The observed span is {_fmt(range_value)} units. Because it depends only on the two extreme observations, "
                "it is more sensitive to extremes than the interquartile range."
            )

        if q1 is not None:
            sentences.append(
                f"First quartile (Q1): Q1 = {_fmt(q1)} means about 25% of the observed {variable} values are at or below this point."
            )

        if q3 is not None:
            sentences.append(
                f"Third quartile (Q3): Q3 = {_fmt(q3)} means about 75% of the observed {variable} values are at or below this point, "
                "so about 25% are above it."
            )

        if iqr is None and q1 is not None and q3 is not None:
            iqr = q3 - q1

        if iqr is not None:
            sentences.append(
                f"Interquartile range (IQR): the IQR is the width of the middle 50% of the {variable} observations. "
                f"An IQR of {_fmt(iqr)} describes the spread of the central half of the data and is less affected by extreme observations than the full range."
            )

        if skewness is not None:
            if skewness > 0:
                direction = "a longer or heavier right tail"
            elif skewness < 0:
                direction = "a longer or heavier left tail"
            else:
                direction = "approximately no directional skew"

            sentences.append(
                f"Skewness: skewness describes asymmetry in the distribution of {variable}. "
                f"The value {_fmt(skewness)} indicates {direction}. "
                "The magnitude should be interpreted together with the histogram, box plot, sample size and presence of outliers rather than by a single cutoff alone."
            )

        if kurtosis is not None:
            sentences.append(
                f"Kurtosis: kurtosis describes the concentration of observations in the center and tails of the {variable} distribution. "
                f"The reported value is {_fmt(kurtosis)}. Its numerical reference point depends on whether the software reports ordinary or excess kurtosis, "
                "so the value should be interpreted together with distribution plots and the definition used by the analysis procedure."
            )

        if missing is not None:
            sentences.append(
                f"Missing values: {int(missing):,} {variable} observations were missing. Missing data can reduce the effective sample size and, "
                "when not random, can affect how representative the summary is."
            )

        if sentences:
            sections.append(
                {
                    "title": f"Meaning of descriptive statistics for {variable}",
                    "text": "\n".join(
                        f"{index}. {sentence}"
                        for index, sentence in enumerate(sentences, 1)
                    ),
                }
            )

    return sections


def _interpret_frequency_table(
    table: dict[str, Any],
) -> list[dict[str, str]]:
    columns, rows = _as_dict_rows(table)

    if not rows:
        return []

    frequency_column = _find_column(
        columns,
        ("frequency", "count", "n"),
    )
    percentage_column = _find_column(
        columns,
        ("percentage", "percent", "proportion"),
    )

    title_norm = _norm(
        table.get("title")
        or ""
    )

    # A plain N column in a model-summary table is sample size,
    # not a category-frequency distribution. Only treat a table
    # as frequencies when its title/columns actually indicate a
    # categorical count/percentage table.
    looks_like_frequency = (
        "frequency" in title_norm
        or "frequencies" in title_norm
        or "distribution" in title_norm
        or "categorycount" in title_norm
        or percentage_column is not None
        or (
            frequency_column is not None
            and _norm(frequency_column) in {"frequency", "count"}
        )
    )

    if not looks_like_frequency:
        return []

    if not frequency_column and not percentage_column:
        return []

    category_column = next(
        (
            column
            for column in columns
            if column not in {frequency_column, percentage_column}
        ),
        columns[0] if columns else None,
    )

    if not category_column:
        return []

    top_row = None
    top_count = None

    for row in rows:
        count = _num(row.get(frequency_column)) if frequency_column else None

        if count is not None and (top_count is None or count > top_count):
            top_count = count
            top_row = row

    if top_row is None:
        return [
            {
                "title": f"Meaning of {table.get('title') or 'frequency results'}",
                "text": (
                    "Frequency counts show how often each category occurs, while percentages express each category as a share of the valid observations. "
                    "Use the largest count or percentage to identify the most common category and compare the remaining categories to understand the distribution."
                ),
            }
        ]

    category = top_row.get(category_column)
    percent = _num(top_row.get(percentage_column)) if percentage_column else None

    extra = ""
    if percent is not None:
        if percent <= 1:
            percent *= 100
        extra = f", representing about {percent:.1f}% of the valid cases"

    return [
        {
            "title": f"Meaning of {table.get('title') or 'frequency results'}",
            "text": (
                "Frequency describes how many observations fall in each category, and percentage shows the same distribution relative to the total valid sample. "
                f"In this dataset, {category} is the most frequently observed category with {int(top_count):,} case(s){extra}. "
                "This identifies the modal category but does not, by itself, imply that the category is statistically different from the others."
            ),
        }
    ]


# ============================================================
# Regression / ANOVA / coefficient interpretation
# ============================================================


def _interpret_model_summary(
    analysis: dict[str, Any],
    table: dict[str, Any],
) -> list[dict[str, str]]:
    columns, rows = _as_dict_rows(table)

    if not rows:
        return []

    row = rows[0]
    outcome = _dependent_variable(analysis)
    predictors = _predictors(analysis)

    n = _num(_row_lookup(row, ("n", "sample_size", "observations")))
    r2 = _num(_row_lookup(row, ("r2", "r_squared", "rsquared")))
    adjusted = _num(_row_lookup(row, ("adjusted_r2", "adjusted_r_squared", "adjr2")))
    rmse = _num(_row_lookup(row, ("rmse", "root_mean_squared_error")))
    predictor_count = _num(_row_lookup(row, ("predictors", "predictor_count", "k")))

    sentences: list[str] = []

    if n is not None:
        sentences.append(
            f"Sample size: the model was estimated from {int(n):,} complete observation(s). The sample size determines how much information is available to estimate the regression relationship."
        )

    if predictor_count is not None:
        sentences.append(
            f"Predictor count: {int(predictor_count)} predictor(s) were entered to explain or predict {outcome}: {predictors}."
        )

    if r2 is not None:
        percent = r2 * 100
        sentences.append(
            f"R-squared (R2): R2 measures the proportion of observed variation in {outcome} that is explained by the predictor set. "
            f"Here the model explains about {percent:.2f}% of the variation in {outcome}; the remaining variation is not explained by this linear model."
        )

    if adjusted is not None:
        if adjusted < 0:
            meaning = (
                "The adjusted value is below zero, meaning that after accounting for model complexity the fitted model does not improve on a simple mean-only benchmark for these data."
            )
        elif r2 is not None and adjusted < r2:
            meaning = (
                "It is slightly lower than R2 because it penalizes adding predictors that do not contribute enough explanatory information."
            )
        else:
            meaning = (
                "It adjusts the explained-variance estimate for the number of predictors and the available sample size."
            )

        sentences.append(
            f"Adjusted R-squared: adjusted R2 is {_fmt(adjusted)}. {meaning}"
        )

    if rmse is not None:
        sentences.append(
            f"RMSE: root mean squared error summarizes the typical size of the model's prediction errors in the units of {outcome}. "
            f"An RMSE of {_fmt(rmse)} means predictions typically miss the observed {outcome} values by roughly {_fmt(rmse)} units, with larger errors receiving extra weight."
        )

    if not sentences:
        return []

    return [
        {
            "title": "Meaning of the model summary",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


def _interpret_anova_like(
    analysis: dict[str, Any],
    table: dict[str, Any],
) -> list[dict[str, str]]:
    columns, rows = _as_dict_rows(table)

    if not rows:
        return []

    source_column = _find_column(columns, ("source", "effect", "term"))
    f_column = _find_column(columns, ("f", "f_statistic", "fvalue"))
    p_column = _find_column(columns, ("p_value", "pvalue", "p", "sig"))
    ss_column = _find_column(columns, ("sum_of_squares", "ss"))
    ms_column = _find_column(columns, ("mean_square", "ms"))
    df_column = _find_column(columns, ("df", "degrees_of_freedom"))

    if not f_column and not p_column:
        return []

    alpha = _alpha(analysis)
    outcome = _dependent_variable(analysis)
    title = str(table.get("title") or "ANOVA")
    title_norm = _norm(title)

    target_row = None

    if source_column:
        preferred_terms = (
            "regression",
            "model",
            "between",
            "group",
            "treatment",
        )

        for preferred in preferred_terms:
            target_row = next(
                (
                    row
                    for row in rows
                    if preferred in _norm(row.get(source_column))
                ),
                None,
            )
            if target_row:
                break

    if target_row is None:
        target_row = next(
            (
                row
                for row in rows
                if _num(row.get(f_column)) is not None
                or _num(row.get(p_column)) is not None
            ),
            rows[0],
        )

    f_value = _num(target_row.get(f_column)) if f_column else None
    p_value = _num(target_row.get(p_column)) if p_column else None
    source = target_row.get(source_column) if source_column else "the tested effect"

    if "ancova" in title_norm:
        purpose = (
            f"ANCOVA tests whether adjusted mean differences in {outcome} remain after controlling for the covariate(s)."
        )
    elif "anova" in title_norm or "regression" in _norm(source):
        purpose = (
            f"The F test compares systematic variation explained by {source} with unexplained or within-group variation in {outcome}."
        )
    else:
        purpose = (
            f"The F statistic compares variation attributed to {source} with residual variation in {outcome}."
        )

    sentences = [purpose]

    if f_value is not None:
        sentences.append(
            f"F statistic: F = {_fmt(f_value)} is a ratio of explained/effect variation to residual variation. Larger values indicate that the tested effect is large relative to unexplained variation, but statistical significance is decided using its p-value and degrees of freedom."
        )

    if p_value is not None:
        if p_value < alpha:
            conclusion = (
                f"Because p = {_fmt(p_value)} is below alpha = {_fmt(alpha)}, the result is statistically significant. "
                f"The data provide evidence against the null hypothesis for {source}."
            )
        else:
            conclusion = (
                f"Because p = {_fmt(p_value)} is not below alpha = {_fmt(alpha)}, the result is not statistically significant. "
                f"The data do not provide sufficient evidence to reject the null hypothesis for {source}."
            )

        sentences.append(
            "P-value: the p-value measures how compatible the observed F result is with the null hypothesis under the model assumptions. "
            + conclusion
        )

    if df_column:
        df_value = target_row.get(df_column)
        if df_value not in (None, "", "—"):
            sentences.append(
                f"Degrees of freedom: the reported df ({_fmt(df_value)}) describe the amount of independent information used to reference the F distribution. They are part of the test definition rather than an effect-size measure."
            )

    if ss_column:
        sentences.append(
            "Sum of squares: sums of squares partition total variability into components attributable to the model/effect and to residual variation. They explain where variation comes from, while the F test determines whether the effect component is large relative to residual noise."
        )

    if ms_column:
        sentences.append(
            "Mean square: a mean square is a sum of squares divided by its degrees of freedom. The relevant mean squares form the numerator and denominator of the F statistic."
        )

    return [
        {
            "title": f"Meaning of {title}",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


def _interpret_coefficients(
    analysis: dict[str, Any],
    table: dict[str, Any],
) -> list[dict[str, str]]:
    columns, rows = _as_dict_rows(table)

    if not rows:
        return []

    predictor_column = _find_column(columns, ("predictor", "term", "variable", "coefficient"))
    b_column = _find_column(columns, ("b", "coefficient", "estimate", "unstandardized_b"))
    se_column = _find_column(columns, ("std_error", "standard_error", "se"))
    beta_column = _find_column(columns, ("standardized_beta", "beta", "std_beta"))
    t_column = _find_column(columns, ("t", "t_statistic", "z", "z_statistic"))
    p_column = _find_column(columns, ("p_value", "pvalue", "p", "sig"))
    lower_column = _find_column(columns, ("ci_lower", "lower_ci", "lower"))
    upper_column = _find_column(columns, ("ci_upper", "upper_ci", "upper"))

    if not predictor_column or not b_column:
        return []

    outcome = _dependent_variable(analysis)
    alpha = _alpha(analysis)
    sentences: list[str] = []

    for row in rows:
        predictor = str(row.get(predictor_column) or "Predictor")
        b = _num(row.get(b_column))
        se = _num(row.get(se_column)) if se_column else None
        beta = _num(row.get(beta_column)) if beta_column else None
        test_stat = _num(row.get(t_column)) if t_column else None
        p_value = _num(row.get(p_column)) if p_column else None
        lower = _num(row.get(lower_column)) if lower_column else None
        upper = _num(row.get(upper_column)) if upper_column else None

        if b is None:
            continue

        if _norm(predictor) in {"intercept", "constant", "const"}:
            text = (
                f"Intercept: the intercept {_fmt(b)} is the model's predicted {outcome} when every numeric predictor equals zero and all coded predictors are at their reference level. "
                "Its practical meaning depends on whether zero/reference values are meaningful in the study context."
            )
        else:
            direction = "increase" if b > 0 else "decrease" if b < 0 else "no linear change"
            text = (
                f"{predictor}: the unstandardized coefficient B = {_fmt(b)} means that, holding the other predictors constant, a one-unit increase in {predictor} is associated with an expected {abs(b):.4g}-unit {direction} in {outcome}. "
                "This coefficient describes conditional association/prediction; it does not by itself establish causation."
            )

        if se is not None:
            text += (
                f" The standard error ({_fmt(se)}) describes the sampling uncertainty of this coefficient; smaller standard errors indicate a more precise estimate relative to its scale."
            )

        if beta is not None and _norm(predictor) not in {"intercept", "constant", "const"}:
            text += (
                f" The standardized beta ({_fmt(beta)}) expresses the association in standard-deviation units, allowing the relative strength of predictors measured on different scales to be compared within the same model."
            )

        if test_stat is not None:
            text += (
                f" The test statistic ({_fmt(test_stat)}) expresses how many standard errors the estimated coefficient lies from the null value of zero."
            )

        if p_value is not None:
            if p_value < alpha:
                text += (
                    f" With p = {_fmt(p_value)} < alpha = {_fmt(alpha)}, this coefficient is statistically significant after accounting for the other predictors in the model."
                )
            else:
                text += (
                    f" With p = {_fmt(p_value)} >= alpha = {_fmt(alpha)}, this coefficient is not statistically significant after accounting for the other predictors."
                )

        if lower is not None and upper is not None:
            contains_zero = lower <= 0 <= upper
            text += (
                f" The confidence interval [{_fmt(lower)}, {_fmt(upper)}] gives a range of coefficient values compatible with the data and model at the stated confidence level."
            )
            if contains_zero:
                text += " Because the interval contains zero, a zero linear effect remains compatible with the interval."
            else:
                text += " Because the interval excludes zero, the interval supports a non-zero coefficient at the corresponding confidence level."

        sentences.append(text)

    if not sentences:
        return []

    return [
        {
            "title": "Meaning of the regression coefficients",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


def _interpret_multicollinearity(
    table: dict[str, Any],
) -> list[dict[str, str]]:
    columns, rows = _as_dict_rows(table)

    if not rows:
        return []

    predictor_column = _find_column(columns, ("predictor", "variable", "term"))
    vif_column = _find_column(columns, ("vif", "variance_inflation_factor"))
    tolerance_column = _find_column(columns, ("tolerance",))

    if not vif_column and not tolerance_column:
        return []

    sentences = [
        "Multicollinearity describes how strongly predictors overlap with one another. Strong overlap can inflate coefficient standard errors and make individual predictor effects unstable even when the overall model is useful."
    ]

    for row in rows:
        predictor = str(row.get(predictor_column) or "Predictor") if predictor_column else "Predictor"
        vif = _num(row.get(vif_column)) if vif_column else None
        tolerance = _num(row.get(tolerance_column)) if tolerance_column else None

        if vif is not None:
            if vif < 2:
                meaning = "shows very little inflation from overlap with the other predictors"
            elif vif < 5:
                meaning = "shows some overlap, but not a strong conventional warning"
            elif vif < 10:
                meaning = "indicates potentially important multicollinearity that deserves review"
            else:
                meaning = "indicates severe multicollinearity under common diagnostic conventions"

            sentences.append(
                f"{predictor}: VIF = {_fmt(vif)} {meaning}. VIF quantifies how much the variance of this coefficient is inflated because the predictor can be explained by the other predictors."
            )

        if tolerance is not None:
            sentences.append(
                f"{predictor}: tolerance = {_fmt(tolerance)} is the proportion of variance in this predictor not explained by the other predictors; values closer to zero indicate more redundancy."
            )

    return [
        {
            "title": "Meaning of multicollinearity diagnostics",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


def _interpret_diagnostics(
    analysis: dict[str, Any],
    table: dict[str, Any],
) -> list[dict[str, str]]:
    columns, rows = _as_dict_rows(table)

    diagnostic_column = _find_column(columns, ("diagnostic", "test", "check"))
    statistic_column = _find_column(columns, ("statistic", "value", "test_statistic"))
    p_column = _find_column(columns, ("p_value", "pvalue", "p"))

    if not diagnostic_column:
        return []

    alpha = _alpha(analysis)
    sentences: list[str] = []

    for row in rows:
        name = str(row.get(diagnostic_column) or "Diagnostic")
        name_norm = _norm(name)
        statistic = _num(row.get(statistic_column)) if statistic_column else None
        p_value = _num(row.get(p_column)) if p_column else None

        if "normal" in name_norm:
            text = (
                "Residual normality evaluates whether the model residuals follow the distributional shape assumed for standard regression inference."
            )
            if p_value is not None:
                if p_value < alpha:
                    text += (
                        f" Here p = {_fmt(p_value)} is below alpha = {_fmt(alpha)}, providing evidence that residual normality may not hold exactly. "
                        "Residual plots and sample size should be reviewed because formal normality tests can be very sensitive in large samples."
                    )
                else:
                    text += (
                        f" Here p = {_fmt(p_value)} is not below alpha = {_fmt(alpha)}, so the test does not provide strong evidence against residual normality."
                    )

        elif "durbinwatson" in name_norm:
            text = (
                "Durbin-Watson assesses first-order autocorrelation in regression residuals. A value near 2 indicates little linear serial autocorrelation; values below 2 suggest positive autocorrelation and values above 2 suggest negative autocorrelation."
            )
            if statistic is not None:
                text += f" The observed value is {_fmt(statistic)}."

        elif "breuschpagan" in name_norm or "heterosced" in name_norm:
            text = (
                "The Breusch-Pagan test evaluates homoscedasticity: whether residual variance is approximately constant across fitted values or predictors."
            )
            if p_value is not None:
                if p_value < alpha:
                    text += (
                        f" With p = {_fmt(p_value)} < alpha = {_fmt(alpha)}, there is evidence of non-constant residual variance (heteroscedasticity)."
                    )
                else:
                    text += (
                        f" With p = {_fmt(p_value)} >= alpha = {_fmt(alpha)}, the test does not show a strong heteroscedasticity warning."
                    )

        elif "standardizedresidual" in name_norm or "extremeresidual" in name_norm:
            text = (
                "Extreme standardized residuals identify observations whose prediction errors are unusually large relative to the residual standard deviation and may deserve case-level review."
            )
            if statistic is not None:
                text += f" The reported count/statistic is {_fmt(statistic)}."

        else:
            text = (
                f"{name} is a model-assumption or quality diagnostic. Its role is to check whether the fitted model behaves consistently with the assumptions required for valid interpretation."
            )
            if statistic is not None:
                text += f" The reported statistic is {_fmt(statistic)}."
            if p_value is not None:
                text += (
                    f" The p-value ({_fmt(p_value)}) should be compared with alpha = {_fmt(alpha)} using the null hypothesis defined by that diagnostic."
                )

        sentences.append(text)

    if not sentences:
        return []

    sentences.append(
        "Diagnostic tests should be interpreted together with residual plots, study design and subject-matter context. Passing one test does not guarantee that every model assumption is satisfied."
    )

    return [
        {
            "title": "Meaning of regression diagnostics",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


# ============================================================
# General inferential tests
# ============================================================


def _interpret_t_test(
    analysis: dict[str, Any],
    table: dict[str, Any],
) -> list[dict[str, str]]:
    title = str(table.get("title") or "")
    title_norm = _norm(title)
    columns, rows = _as_dict_rows(table)

    analysis_title_norm = _norm(
        analysis.get("title")
        or analysis.get("method")
        or analysis.get("analysis_type")
        or ""
    )

    # Coefficient tables also contain a t column, but that t value
    # is a coefficient test inside regression, not a standalone
    # t-test analysis. Restrict this interpreter to actual t tests.
    if (
        "ttest" not in title_norm
        and "ttest" not in analysis_title_norm
    ):
        return []

    if not rows:
        return []

    alpha = _alpha(analysis)
    sentences = [
        "The t test evaluates a mean difference relative to the amount of sampling uncertainty. The t statistic is the estimated difference measured in standard-error units."
    ]

    for row in rows[:8]:
        t_value = _num(_row_lookup(row, ("t", "t_statistic", "tvalue")))
        p_value = _num(_row_lookup(row, ("p_value", "pvalue", "p", "sig")))
        df = _num(_row_lookup(row, ("df", "degrees_of_freedom")))
        difference = _num(_row_lookup(row, ("mean_difference", "difference", "mean_diff")))
        lower = _num(_row_lookup(row, ("ci_lower", "lower_ci", "lower")))
        upper = _num(_row_lookup(row, ("ci_upper", "upper_ci", "upper")))
        effect = _num(_row_lookup(row, ("cohens_d", "cohen_d", "effect_size", "d")))

        if difference is not None:
            sentences.append(
                f"Mean difference: {_fmt(difference)} is the estimated difference targeted by this test. Its sign shows direction, while its practical importance depends on the units and study context."
            )

        if t_value is not None:
            sentences.append(
                f"t statistic: t = {_fmt(t_value)} indicates how many standard errors the estimated difference lies from the null value."
            )

        if df is not None:
            sentences.append(
                f"Degrees of freedom: df = {_fmt(df)} determine the reference t distribution and reflect the amount of independent information available for the test."
            )

        if p_value is not None:
            if p_value < alpha:
                conclusion = "The null hypothesis is rejected at the selected alpha level."
            else:
                conclusion = "There is not sufficient evidence to reject the null hypothesis at the selected alpha level."

            sentences.append(
                f"P-value: p = {_fmt(p_value)} is compared with alpha = {_fmt(alpha)}. {conclusion}"
            )

        if lower is not None and upper is not None:
            text = (
                f"Confidence interval: [{_fmt(lower)}, {_fmt(upper)}] represents a range of mean-difference values compatible with the data at the stated confidence level."
            )
            if lower <= 0 <= upper:
                text += " Because zero is inside the interval, no difference remains compatible with the interval."
            else:
                text += " Because zero is outside the interval, the interval supports a non-zero difference at the corresponding confidence level."
            sentences.append(text)

        if effect is not None:
            sentences.append(
                f"Effect size: the reported standardized effect ({_fmt(effect)}) describes the magnitude of the difference in standard-deviation units, which helps separate practical magnitude from statistical significance."
            )

        break

    return [
        {
            "title": f"Meaning of {title or 'the t test'}",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


def _interpret_chi_square(
    analysis: dict[str, Any],
    table: dict[str, Any],
) -> list[dict[str, str]]:
    title = str(table.get("title") or "")
    columns, rows = _as_dict_rows(table)
    title_norm = _norm(title)

    has_chi = (
        "chisquare" in title_norm
        or any(
            _norm(column) in {
                "chisquare",
                "chi2",
                "chi2statistic",
            }
            for column in columns
        )
    )

    if not has_chi or not rows:
        return []

    row = rows[0]
    statistic = _num(_row_lookup(row, ("chi_square", "chi2", "statistic", "chisquare")))
    p_value = _num(_row_lookup(row, ("p_value", "pvalue", "p", "sig")))
    df = _num(_row_lookup(row, ("df", "degrees_of_freedom")))
    effect = _num(_row_lookup(row, ("cramers_v", "phi", "effect_size")))
    alpha = _alpha(analysis)

    sentences = [
        "The chi-square test compares observed category counts with the counts expected under the null hypothesis. A larger chi-square statistic means the observed pattern differs more from the null-expected pattern relative to sampling variation."
    ]

    if statistic is not None:
        sentences.append(f"Chi-square statistic: the reported value is {_fmt(statistic)}.")

    if df is not None:
        sentences.append(
            f"Degrees of freedom: df = {_fmt(df)} determine the reference chi-square distribution from the number of independent category comparisons."
        )

    if p_value is not None:
        if p_value < alpha:
            conclusion = "The observed categorical pattern is statistically inconsistent with the null hypothesis at the selected alpha level."
        else:
            conclusion = "The data do not provide sufficient evidence that the observed categorical pattern differs from the null expectation."

        sentences.append(
            f"P-value: p = {_fmt(p_value)} is compared with alpha = {_fmt(alpha)}. {conclusion}"
        )

    if effect is not None:
        sentences.append(
            f"Association/effect size: {_fmt(effect)} summarizes the strength of the categorical association separately from sample-size-driven statistical significance."
        )

    return [
        {
            "title": f"Meaning of {title or 'the chi-square test'}",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


def _interpret_correlation(
    analysis: dict[str, Any],
    table: dict[str, Any],
) -> list[dict[str, str]]:
    title = str(table.get("title") or "")
    title_norm = _norm(title)
    columns, rows = _as_dict_rows(table)

    looks_like_correlation = (
        "correlation" in title_norm
        or any(
            _norm(column) in {
                "r",
                "pearsonr",
                "spearmanrho",
                "rho",
                "correlation",
            }
            for column in columns
        )
    )

    if not looks_like_correlation or not rows:
        return []

    alpha = _alpha(analysis)
    sentences = [
        "A correlation coefficient describes the direction and strength of association between two variables. Positive values mean the variables tend to increase together; negative values mean one tends to decrease as the other increases; values near zero indicate little linear/monotonic association depending on the selected method. Correlation does not establish causation."
    ]

    # Pairwise-row layout
    for row in rows[:12]:
        r_value = _num(_row_lookup(row, ("r", "correlation", "pearson_r", "rho", "spearman_rho")))
        p_value = _num(_row_lookup(row, ("p_value", "pvalue", "p", "sig")))
        var1 = _row_lookup(row, ("variable_1", "variable1", "x", "first_variable"))
        var2 = _row_lookup(row, ("variable_2", "variable2", "y", "second_variable"))

        if r_value is None:
            continue

        magnitude = abs(r_value)
        if magnitude < 0.1:
            strength = "very weak"
        elif magnitude < 0.3:
            strength = "weak"
        elif magnitude < 0.5:
            strength = "moderate"
        elif magnitude < 0.7:
            strength = "moderately strong"
        elif magnitude < 0.9:
            strength = "strong"
        else:
            strength = "very strong"

        direction = "positive" if r_value > 0 else "negative" if r_value < 0 else "near-zero"
        pair = f" between {var1} and {var2}" if var1 and var2 else ""

        text = (
            f"Coefficient{pair}: {_fmt(r_value)} indicates a {strength} {direction} association in this sample."
        )

        if p_value is not None:
            if p_value < alpha:
                text += f" With p = {_fmt(p_value)} < alpha = {_fmt(alpha)}, the association is statistically significant under the test assumptions."
            else:
                text += f" With p = {_fmt(p_value)} >= alpha = {_fmt(alpha)}, the sample does not provide sufficient evidence of a non-zero population association."

        sentences.append(text)
        break

    return [
        {
            "title": f"Meaning of {title or 'the correlation results'}",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


# ============================================================
# Reliability, factor/PCA, cluster, survival, predictive
# ============================================================


def _interpret_reliability(
    table: dict[str, Any],
) -> list[dict[str, str]]:
    title = str(table.get("title") or "")
    columns, rows = _as_dict_rows(table)
    combined = _norm(title + " " + " ".join(columns))

    if not any(token in combined for token in ("cronbach", "reliability", "itemtotal", "alphaifitemdeleted")):
        return []

    sentences = [
        "Reliability analysis evaluates whether a set of items behaves consistently enough to support interpretation as a scale. Internal consistency is about how items work together; it is not evidence that the scale is valid or one-dimensional by itself."
    ]

    alpha_value = None
    for row in rows:
        alpha_value = _num(_row_lookup(row, ("cronbach_alpha", "alpha", "reliability")))
        if alpha_value is not None:
            break

    if alpha_value is not None:
        sentences.append(
            f"Cronbach's alpha: alpha = {_fmt(alpha_value)} summarizes average item consistency on a 0-to-1 style scale, with higher values generally indicating greater internal consistency. "
            "Whether the value is adequate depends on the purpose of the instrument, number of items, item redundancy and research context rather than one universal cutoff."
        )

    if "itemtotal" in combined:
        sentences.append(
            "Item-total correlation shows how strongly each item relates to the score formed from the remaining scale. Very low or negative item-total relationships can indicate that an item does not behave like the rest of the scale and should be reviewed."
        )

    if "alphaifitemdeleted" in combined:
        sentences.append(
            "Alpha if item deleted estimates the scale's internal consistency after removing each item. An increase after deletion can identify an item that weakens consistency, but deletion should also consider content validity and theory."
        )

    return [
        {
            "title": f"Meaning of {title or 'reliability results'}",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


def _interpret_factor_pca(
    analysis: dict[str, Any],
    table: dict[str, Any],
) -> list[dict[str, str]]:
    title = str(table.get("title") or "")
    columns, rows = _as_dict_rows(table)
    combined = _norm(title + " " + " ".join(columns))

    if not any(token in combined for token in ("kmo", "bartlett", "eigen", "varianceexplained", "loading", "communality", "component", "factor")):
        return []

    alpha = _alpha(analysis)
    sentences: list[str] = []

    if "kmo" in combined:
        sentences.append(
            "KMO (Kaiser-Meyer-Olkin) measures whether the correlation pattern is sufficiently compact for factor/component extraction. Values closer to 1 indicate that variables share enough common variance for this type of analysis; low values suggest weak factorability."
        )

    if "bartlett" in combined:
        p_value = None
        for row in rows:
            p_value = _num(_row_lookup(row, ("p_value", "pvalue", "p", "sig")))
            if p_value is not None:
                break

        text = (
            "Bartlett's test evaluates the null hypothesis that the correlation matrix is essentially an identity matrix, which would mean the variables are not sufficiently correlated for factor analysis."
        )
        if p_value is not None:
            if p_value < alpha:
                text += f" With p = {_fmt(p_value)} < alpha = {_fmt(alpha)}, the null is rejected, supporting factorability of the correlation matrix."
            else:
                text += f" With p = {_fmt(p_value)} >= alpha = {_fmt(alpha)}, the test does not provide strong evidence that the matrix is factorable."
        sentences.append(text)

    if "eigen" in combined or "varianceexplained" in combined or "component" in combined:
        sentences.append(
            "Eigenvalues and explained variance describe how much total information each extracted component/factor accounts for. Larger eigenvalues and cumulative explained variance indicate that fewer dimensions summarize more of the original variability."
        )

    if "loading" in combined:
        sentences.append(
            "Factor/component loadings describe how strongly each observed variable is associated with an extracted factor or component. Larger absolute loadings indicate a stronger relationship; the sign gives direction. Interpretation should focus on coherent patterns of variables rather than a single loading in isolation."
        )

    if "communality" in combined:
        sentences.append(
            "Communality is the proportion of an observed variable's variance represented by the retained factors. Higher communalities mean the extracted factor solution reproduces more of that variable's information."
        )

    if not sentences:
        return []

    return [
        {
            "title": f"Meaning of {title or 'factor/PCA results'}",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


def _interpret_cluster(
    table: dict[str, Any],
) -> list[dict[str, str]]:
    title = str(table.get("title") or "")
    columns, _ = _as_dict_rows(table)
    combined = _norm(title + " " + " ".join(columns))

    if not any(token in combined for token in ("cluster", "silhouette", "centroid", "clustersize")):
        return []

    sentences = [
        "Cluster analysis groups observations so that cases within a cluster are more similar to one another than to cases in other clusters, according to the variables and distance/model definition used. Cluster labels are descriptive group identifiers, not pre-existing outcome categories."
    ]

    if "clustersize" in combined or "size" in combined:
        sentences.append(
            "Cluster size shows how many observations were assigned to each cluster. Large differences in size may be genuine features of the data, but very small clusters can also indicate rare patterns or sensitivity to the selected number of clusters."
        )

    if "centroid" in combined or "center" in combined:
        sentences.append(
            "Cluster centers/centroids summarize the typical profile of each cluster on the analyzed variables. Comparing centers helps describe what makes one cluster different from another."
        )

    if "silhouette" in combined:
        sentences.append(
            "Silhouette measures how well each observation fits its assigned cluster relative to neighboring clusters. Values closer to 1 indicate clear separation, values near 0 indicate overlap, and negative values can indicate possible misclassification."
        )

    return [
        {
            "title": f"Meaning of {title or 'cluster results'}",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


def _interpret_survival(
    analysis: dict[str, Any],
    table: dict[str, Any],
) -> list[dict[str, str]]:
    title = str(table.get("title") or "")
    columns, rows = _as_dict_rows(table)
    combined = _norm(title + " " + " ".join(columns))

    if not any(token in combined for token in ("survival", "kaplan", "hazard", "logrank", "cox")):
        return []

    alpha = _alpha(analysis)
    sentences = [
        "Survival analysis studies time until an event while correctly accounting for censored observations whose event time is not fully observed. The event definition and time scale determine the substantive interpretation."
    ]

    if "survivalprobability" in combined or "kaplan" in combined:
        sentences.append(
            "Survival probability is the estimated probability of remaining event-free beyond a given time. A Kaplan-Meier curve shows how this probability changes over time and where events occur."
        )

    if "mediansurvival" in combined:
        sentences.append(
            "Median survival time is the time at which the estimated survival probability falls to 0.50; approximately half the population is estimated to remain event-free beyond that time."
        )

    if "hazardratio" in combined or "cox" in combined:
        sentences.append(
            "A hazard ratio compares instantaneous event rates while accounting for the model's other predictors. A ratio above 1 indicates higher hazard, below 1 indicates lower hazard, and 1 indicates no hazard difference for the compared values."
        )

    if "logrank" in combined:
        p_value = None
        for row in rows:
            p_value = _num(_row_lookup(row, ("p_value", "pvalue", "p")))
            if p_value is not None:
                break
        text = "The log-rank test compares entire survival curves between groups under the null hypothesis that their survival experience is the same."
        if p_value is not None:
            if p_value < alpha:
                text += f" With p = {_fmt(p_value)} < alpha = {_fmt(alpha)}, the survival curves differ statistically."
            else:
                text += f" With p = {_fmt(p_value)} >= alpha = {_fmt(alpha)}, there is not sufficient evidence of a difference between the survival curves."
        sentences.append(text)

    return [
        {
            "title": f"Meaning of {title or 'survival results'}",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


def _interpret_predictive(
    table: dict[str, Any],
) -> list[dict[str, str]]:
    title = str(table.get("title") or "")
    columns, _ = _as_dict_rows(table)
    combined = _norm(title + " " + " ".join(columns))

    strong_tokens = (
        "accuracy",
        "precision",
        "recall",
        "f1",
        "auc",
        "roc",
        "confusionmatrix",
        "mae",
        "meansquarederror",
    )

    title_norm = _norm(title)
    predictive_title = any(
        token in title_norm
        for token in (
            "prediction",
            "predictive",
            "modelperformance",
            "classificationmetrics",
            "evaluationmetrics",
        )
    )

    # RMSE also appears in ordinary regression model summaries.
    # Do not create a second predictive-performance explanation
    # for those tables unless the table itself is clearly a model
    # evaluation/prediction table.
    if (
        not predictive_title
        and not any(
            token in combined
            for token in strong_tokens
        )
    ):
        return []

    sentences: list[str] = []

    if "accuracy" in combined:
        sentences.append("Accuracy is the proportion of all predictions classified correctly. It can be misleading when outcome classes are highly imbalanced, so it should be read with precision, recall and the confusion matrix.")

    if "precision" in combined:
        sentences.append("Precision answers: among cases predicted as positive, what proportion were actually positive? It emphasizes the cost of false-positive predictions.")

    if "recall" in combined or "sensitivity" in combined:
        sentences.append("Recall/sensitivity answers: among truly positive cases, what proportion did the model correctly identify? It emphasizes the cost of missed positive cases (false negatives).")

    if "f1" in combined:
        sentences.append("F1 score is the harmonic mean of precision and recall. It is useful when a balance between false positives and false negatives is important.")

    if "auc" in combined or "roc" in combined:
        sentences.append("ROC-AUC measures how well the model ranks positive cases above negative cases across classification thresholds. Values nearer 1 indicate better ranking discrimination; 0.5 corresponds to chance-level ranking.")

    if "confusionmatrix" in combined:
        sentences.append("The confusion matrix separates correct and incorrect predictions into true positives, true negatives, false positives and false negatives, making the types of classification errors explicit.")

    if "mae" in combined:
        sentences.append("MAE is the average absolute prediction error in the outcome's original units, so it describes the typical size of an error without giving extra weight to very large errors.")

    if "rmse" in combined:
        sentences.append("RMSE is the square root of average squared prediction error. It is in the outcome's original units and penalizes larger errors more heavily than MAE.")

    if not sentences:
        return []

    return [
        {
            "title": f"Meaning of {title or 'predictive model performance'}",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


# ============================================================
# Generic statistic-column interpretation
# ============================================================


def _interpret_generic_inferential(
    analysis: dict[str, Any],
    table: dict[str, Any],
) -> list[dict[str, str]]:
    title = str(table.get("title") or "Results")
    columns, rows = _as_dict_rows(table)

    if not rows:
        return []

    normalized_columns = {_norm(column): column for column in columns}
    alpha = _alpha(analysis)
    sentences: list[str] = []

    if "pvalue" in normalized_columns or "p" in normalized_columns:
        sentences.append(
            f"P-value: the p-value quantifies how compatible the observed test result is with the null hypothesis, assuming the test model is valid. SSAS compares it with alpha = {_fmt(alpha)}; a value below alpha is treated as statistically significant, while a value at or above alpha is not sufficient to reject the null hypothesis."
        )

    if "df" in normalized_columns or "degreesoffreedom" in normalized_columns:
        sentences.append(
            "Degrees of freedom (df): df describe the amount of independent information used to determine the reference sampling distribution for the test. They affect the critical values and p-value but are not a measure of effect magnitude."
        )

    if any(key in normalized_columns for key in ("effectsize", "cohensd", "etasquared", "partialetasquared", "cramersv", "oddsratio")):
        sentences.append(
            "Effect size: effect-size statistics describe the magnitude of an association, difference or model effect. They complement the p-value because statistical significance can be strongly influenced by sample size."
        )

    if any(key in normalized_columns for key in ("cilower", "ciupper", "confidenceinterval", "lowerci", "upperci")):
        sentences.append(
            "Confidence interval: a confidence interval gives a range of parameter values compatible with the sample and model at the selected confidence level. For differences, correlations and regression coefficients, whether the interval includes zero is often important; for ratio measures such as odds/hazard ratios, whether it includes one is important."
        )

    if not sentences:
        return []

    return [
        {
            "title": f"How to read {title}",
            "text": "\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(sentences, 1)
            ),
        }
    ]


# ============================================================
# Public entry point
# ============================================================


def build_contextual_interpretation(
    analysis: dict[str, Any],
    tables: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """
    Create statistical interpretation that explains what each
    reported statistic/test MEANS for the variables and model,
    rather than merely repeating the number already shown in the
    results table.

    The function is deterministic and uses only the saved SSAS
    analysis result; it does not call an external AI service.
    """

    sections: list[dict[str, str]] = []
    seen: set[str] = set()

    analysis_title = str(
        analysis.get("title")
        or analysis.get("method")
        or analysis.get("analysis_type")
        or "Statistical Analysis"
    )

    intro = (
        f"The tables above contain the numerical results for {analysis_title}. "
        "The explanations below focus on what those statistics mean for the analyzed variables, how they should be read, "
        "and what statistical conclusion they support. Values are referenced only when they help interpret the meaning; they are not repeated simply to duplicate the tables."
    )

    _append_unique(
        sections,
        seen,
        "How to interpret this analysis",
        intro,
    )

    for table in tables:
        title = str(table.get("title") or "Results")
        title_norm = _norm(title)
        columns, _ = _as_dict_rows(table)
        column_norms = {_norm(column) for column in columns}

        generated: list[dict[str, str]] = []

        # Descriptive statistics first because they can contain
        # columns such as mean / p-value-like names in unusual data.
        descriptive = _interpret_descriptive_table(table)
        if descriptive:
            generated.extend(descriptive)

        frequency = _interpret_frequency_table(table)
        if frequency:
            generated.extend(frequency)

        if "modelsummary" in title_norm or (
            "r2" in column_norms and "rmse" in column_norms
        ):
            generated.extend(
                _interpret_model_summary(analysis, table)
            )

        if "coefficient" in title_norm:
            generated.extend(
                _interpret_coefficients(analysis, table)
            )

        if "multicollinearity" in title_norm or "vif" in column_norms:
            generated.extend(
                _interpret_multicollinearity(table)
            )

        if "diagnostic" in title_norm:
            generated.extend(
                _interpret_diagnostics(analysis, table)
            )

        if "anova" in title_norm or "ancova" in title_norm:
            generated.extend(
                _interpret_anova_like(analysis, table)
            )

        generated.extend(
            _interpret_t_test(analysis, table)
        )
        generated.extend(
            _interpret_chi_square(analysis, table)
        )
        generated.extend(
            _interpret_correlation(analysis, table)
        )
        generated.extend(
            _interpret_reliability(table)
        )
        generated.extend(
            _interpret_factor_pca(analysis, table)
        )
        generated.extend(
            _interpret_cluster(table)
        )
        generated.extend(
            _interpret_survival(analysis, table)
        )
        generated.extend(
            _interpret_predictive(table)
        )

        # If no specialized interpreter recognized the table,
        # explain common inferential columns instead of leaving
        # the reader with unexplained p-values / CIs / effect sizes.
        if not generated:
            generated.extend(
                _interpret_generic_inferential(analysis, table)
            )

        for section in generated:
            _append_unique(
                sections,
                seen,
                section.get("title", "Interpretation"),
                section.get("text", ""),
            )

    # A method-level explanation helps when the saved result contains
    # few tables or only scalar outputs.
    method_norm = _norm(analysis_title)

    if "regression" in method_norm and not any(
        "model summary" in section["title"].lower()
        for section in sections
    ):
        _append_unique(
            sections,
            seen,
            "Meaning of regression analysis",
            (
                f"Regression models the expected value of {_dependent_variable(analysis)} as a function of {_predictors(analysis)}. "
                "Coefficients describe conditional linear associations, R2 describes explained variation, p-values evaluate evidence against coefficient/model null hypotheses, "
                "confidence intervals describe estimation uncertainty, and diagnostics evaluate whether the fitted model's assumptions are reasonable."
            ),
        )

    return sections
