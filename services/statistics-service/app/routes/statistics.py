from fastapi import APIRouter, Depends, HTTPException

from app.schemas.statistics import (
    AnovaRequest,
    ChiSquareRequest,
    ConfidenceIntervalRequest,
    CorrelationRequest,
    IndependentTTestRequest,
    KruskalWallisRequest,
    MannWhitneyRequest,
    OneSampleTTestRequest,
    PairedTTestRequest,
    ShapiroRequest,
    WilcoxonRequest,
)
from app.security.dependencies import get_current_user
from app.services.dataset_reader import read_dataset
from app.services.statistics_engine import (
    chi_square_test,
    confidence_interval,
    correlation_matrix,
    descriptive_statistics,
    independent_t_test,
    kruskal_wallis_test,
    mann_whitney_test,
    one_sample_t_test,
    one_way_anova,
    paired_t_test,
    shapiro_test,
    wilcoxon_test,
)


router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
)


def ensure_columns(df, columns):
    missing = [
        column
        for column in columns
        if column not in df.columns
    ]

    if missing:
        raise HTTPException(
            status_code=400,
            detail="Unknown columns: " + ", ".join(missing),
        )


@router.get("/tests")
def available_tests():
    return {
        "descriptive": True,
        "correlation": [
            "pearson",
            "spearman",
            "kendall",
        ],
        "hypothesis_tests": [
            "one_sample_t",
            "independent_t",
            "paired_t",
            "chi_square",
            "shapiro",
            "mann_whitney",
            "wilcoxon",
            "kruskal_wallis",
            "one_way_anova",
        ],
        "confidence_interval": True,
    }


@router.get("/descriptive/{dataset_id}")
def descriptive(
    dataset_id: str,
    current_user=Depends(get_current_user),
):
    df, dataset = read_dataset(
        dataset_id,
        current_user["id"],
    )

    return {
        "dataset_id": dataset_id,
        "dataset": dataset.get("original_filename"),
        "row_count": len(df),
        "column_count": len(df.columns),
        "results": descriptive_statistics(df),
    }


@router.post("/correlation/{dataset_id}")
def correlation(
    dataset_id: str,
    request: CorrelationRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    try:
        result = correlation_matrix(
            df,
            columns=request.columns,
            method=request.method,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "dataset_id": dataset_id,
        "method": request.method,
        "correlation_matrix": result,
    }


@router.post("/one-sample-t/{dataset_id}")
def one_sample_t(
    dataset_id: str,
    request: OneSampleTTestRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    ensure_columns(df, [request.column])

    return one_sample_t_test(
        df[request.column],
        request.population_mean,
    )


@router.post("/independent-t/{dataset_id}")
def independent_t(
    dataset_id: str,
    request: IndependentTTestRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    ensure_columns(
        df,
        [
            request.column,
            request.group_column,
        ],
    )

    return independent_t_test(
        df,
        request.column,
        request.group_column,
        request.group1,
        request.group2,
    )


@router.post("/paired-t/{dataset_id}")
def paired_t(
    dataset_id: str,
    request: PairedTTestRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    ensure_columns(
        df,
        [
            request.column1,
            request.column2,
        ],
    )

    return paired_t_test(
        df,
        request.column1,
        request.column2,
    )


@router.post("/chi-square/{dataset_id}")
def chi_square(
    dataset_id: str,
    request: ChiSquareRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    ensure_columns(
        df,
        [
            request.column1,
            request.column2,
        ],
    )

    return chi_square_test(
        df,
        request.column1,
        request.column2,
    )


@router.post("/shapiro/{dataset_id}")
def shapiro(
    dataset_id: str,
    request: ShapiroRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    ensure_columns(df, [request.column])

    return shapiro_test(
        df[request.column]
    )


@router.post("/mann-whitney/{dataset_id}")
def mann_whitney(
    dataset_id: str,
    request: MannWhitneyRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    ensure_columns(
        df,
        [
            request.column,
            request.group_column,
        ],
    )

    return mann_whitney_test(
        df,
        request.column,
        request.group_column,
        request.group1,
        request.group2,
    )


@router.post("/wilcoxon/{dataset_id}")
def wilcoxon(
    dataset_id: str,
    request: WilcoxonRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    ensure_columns(
        df,
        [
            request.column1,
            request.column2,
        ],
    )

    return wilcoxon_test(
        df,
        request.column1,
        request.column2,
    )


@router.post("/kruskal-wallis/{dataset_id}")
def kruskal_wallis(
    dataset_id: str,
    request: KruskalWallisRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    ensure_columns(
        df,
        [
            request.value_column,
            request.group_column,
        ],
    )

    try:
        return kruskal_wallis_test(
            df,
            request.value_column,
            request.group_column,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/anova/{dataset_id}")
def anova(
    dataset_id: str,
    request: AnovaRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    ensure_columns(
        df,
        [
            request.value_column,
            request.group_column,
        ],
    )

    try:
        return one_way_anova(
            df,
            request.value_column,
            request.group_column,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/confidence-interval/{dataset_id}")
def interval(
    dataset_id: str,
    request: ConfidenceIntervalRequest,
    current_user=Depends(get_current_user),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    ensure_columns(df, [request.column])

    try:
        return confidence_interval(
            df[request.column],
            request.confidence,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
