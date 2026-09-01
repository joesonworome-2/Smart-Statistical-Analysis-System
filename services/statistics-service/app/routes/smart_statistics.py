from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.schemas.smart_statistics import (
    EffectSizeRequest,
    NormalityRequest,
    RecommendationRequest,
)

from app.security.dependencies import (
    get_current_user,
)

from app.services.dataset_reader import (
    read_dataset,
)

from app.services.smart_statistics import (
    calculate_effect_size,
    frequency_table,
    normality_tests,
    recommend_analysis,
    variable_profiles,
)


router = APIRouter(
    prefix="/statistics/smart",
    tags=[
        "Smart Statistics",
    ],
)


# ============================================================
# Variable profiles
# ============================================================

@router.get(
    "/variables/{dataset_id}"
)
def variables(
    dataset_id: str,
    current_user=Depends(
        get_current_user
    ),
):
    df, dataset = read_dataset(
        dataset_id,
        current_user["id"],
    )

    return {
        "dataset_id":
            dataset_id,
        "dataset":
            dataset.get(
                "original_filename"
            ),
        "row_count":
            len(df),
        "column_count":
            len(df.columns),
        "variables":
            variable_profiles(df),
    }


# ============================================================
# Frequency tables
# ============================================================

@router.get(
    "/frequencies/{dataset_id}"
)
def frequencies(
    dataset_id: str,
    column: str = Query(...),
    current_user=Depends(
        get_current_user
    ),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    try:
        return {
            "dataset_id":
                dataset_id,
            **frequency_table(
                df,
                column,
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Normality suite
# ============================================================

@router.post(
    "/normality/{dataset_id}"
)
def normality(
    dataset_id: str,
    request: NormalityRequest,
    current_user=Depends(
        get_current_user
    ),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    if (
        request.column
        not in df.columns
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unknown column: "
                + request.column
            ),
        )

    try:
        result = normality_tests(
            df[request.column],
            methods=request.methods,
            alpha=request.alpha,
        )

        return {
            "dataset_id":
                dataset_id,
            "column":
                request.column,
            **result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Effect size
# ============================================================

@router.post(
    "/effect-size/{dataset_id}"
)
def effect_size(
    dataset_id: str,
    request: EffectSizeRequest,
    current_user=Depends(
        get_current_user
    ),
):
    df, _ = read_dataset(
        dataset_id,
        current_user["id"],
    )

    try:
        result = (
            calculate_effect_size(
                df,
                request,
            )
        )

        return {
            "dataset_id":
                dataset_id,
            "effect_size":
                result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Smart method recommendation
# ============================================================

@router.post(
    "/recommend/{dataset_id}"
)
def recommend(
    dataset_id: str,
    request: RecommendationRequest,
    current_user=Depends(
        get_current_user
    ),
):
    df, dataset = read_dataset(
        dataset_id,
        current_user["id"],
    )

    try:
        result = recommend_analysis(
            df,
            request,
        )

        return {
            "dataset_id":
                dataset_id,
            "dataset":
                dataset.get(
                    "original_filename"
                ),
            "recommendation":
                result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
