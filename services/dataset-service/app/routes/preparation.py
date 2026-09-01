from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.schemas.preparation import (
    FilterRequest,
    MissingValuesRequest,
    OutlierRequest,
    TransformRequest,
    VariableMetadataUpdate,
)

from app.security.dependencies import (
    get_current_user,
)

from app.services.dataset_preparation import (
    dataset_profile,
    get_owned_dataset,
    missing_value_summary,
    outlier_information,
    prepare_missing_values,
    prepare_outliers,
    read_owned_dataset,
    save_derived_dataset,
    transform_dataset,
    filter_dataset,
    update_variable_metadata,
    variable_metadata,
)


router = APIRouter(
    prefix="/datasets",
    tags=[
        "Data Preparation",
    ],
)


def current_user_id(
    current_user,
):
    user_id = (
        current_user.get(
            "user_id"
        )
        or current_user.get(
            "id"
        )
    )

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=(
                "Authenticated user "
                "ID is missing."
            ),
        )

    return str(user_id)


# ============================================================
# Dataset profile
# ============================================================

@router.get(
    "/{dataset_id}/profile"
)
def profile(
    dataset_id: str,
    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    df, dataset = (
        read_owned_dataset(
            dataset_id,
            user_id,
        )
    )

    return {
        "dataset_id":
            dataset_id,

        "dataset":
            dataset.get(
                "original_filename"
            ),

        "profile":
            dataset_profile(df),

        "variables":
            variable_metadata(
                df,
                dataset,
            ),
    }


# ============================================================
# Variables and metadata
# ============================================================

@router.get(
    "/{dataset_id}/variables"
)
def variables(
    dataset_id: str,
    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    df, dataset = (
        read_owned_dataset(
            dataset_id,
            user_id,
        )
    )

    return {
        "dataset_id":
            dataset_id,

        "variables":
            variable_metadata(
                df,
                dataset,
            ),
    }


@router.patch(
    "/{dataset_id}/variables/{column}"
)
def update_variable(
    dataset_id: str,
    column: str,
    request: VariableMetadataUpdate,
    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    try:
        result = (
            update_variable_metadata(
                dataset_id,
                user_id,
                column,
                request,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "dataset_id":
            dataset_id,

        "column":
            column,

        "metadata":
            result,

        "message":
            "Variable metadata updated.",
    }


# ============================================================
# Missing values
# ============================================================

@router.get(
    "/{dataset_id}/missing-values"
)
def missing_values(
    dataset_id: str,
    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    df, _ = read_owned_dataset(
        dataset_id,
        user_id,
    )

    return {
        "dataset_id":
            dataset_id,

        "total_missing":
            int(
                df.isna()
                .sum()
                .sum()
            ),

        "columns":
            missing_value_summary(
                df
            ),
    }


@router.post(
    "/{dataset_id}/prepare/missing-values"
)
def prepare_missing(
    dataset_id: str,
    request: MissingValuesRequest,
    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    df, dataset = (
        read_owned_dataset(
            dataset_id,
            user_id,
        )
    )

    try:
        prepared, details = (
            prepare_missing_values(
                df,
                request,
            )
        )

        derived = (
            save_derived_dataset(
                prepared,
                dataset,
                user_id,
                "missing_values",
                details,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message":
            (
                "Missing-value "
                "preparation completed. "
                "The original dataset "
                "was preserved."
            ),

        "derived_dataset":
            derived,
    }


# ============================================================
# Outliers
# ============================================================

@router.get(
    "/{dataset_id}/outliers"
)
def detect_outliers(
    dataset_id: str,

    column: str = Query(...),

    method: str = Query(
        default="iqr"
    ),

    threshold: float = Query(
        default=1.5,
        gt=0,
    ),

    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    df, _ = read_owned_dataset(
        dataset_id,
        user_id,
    )

    try:
        result = (
            outlier_information(
                df,
                column,
                method,
                threshold,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "dataset_id":
            dataset_id,

        "outliers":
            result,
    }


@router.post(
    "/{dataset_id}/prepare/outliers"
)
def prepare_outlier_data(
    dataset_id: str,
    request: OutlierRequest,
    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    df, dataset = (
        read_owned_dataset(
            dataset_id,
            user_id,
        )
    )

    try:
        prepared, details = (
            prepare_outliers(
                df,
                request,
            )
        )

        derived = (
            save_derived_dataset(
                prepared,
                dataset,
                user_id,
                "outliers",
                details,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message":
            (
                "Outlier preparation "
                "completed. Original "
                "dataset preserved."
            ),

        "derived_dataset":
            derived,
    }


# ============================================================
# Transformations
# ============================================================

@router.post(
    "/{dataset_id}/prepare/transform"
)
def transform(
    dataset_id: str,
    request: TransformRequest,
    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    df, dataset = (
        read_owned_dataset(
            dataset_id,
            user_id,
        )
    )

    try:
        prepared, details = (
            transform_dataset(
                df,
                request,
            )
        )

        derived = (
            save_derived_dataset(
                prepared,
                dataset,
                user_id,
                "transform",
                details,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message":
            (
                "Transformation completed. "
                "Original dataset preserved."
            ),

        "derived_dataset":
            derived,
    }


# ============================================================
# Filtering
# ============================================================

@router.post(
    "/{dataset_id}/prepare/filter"
)
def filter_rows(
    dataset_id: str,
    request: FilterRequest,
    current_user=Depends(
        get_current_user
    ),
):
    user_id = current_user_id(
        current_user
    )

    df, dataset = (
        read_owned_dataset(
            dataset_id,
            user_id,
        )
    )

    try:
        prepared, details = (
            filter_dataset(
                df,
                request,
            )
        )

        derived = (
            save_derived_dataset(
                prepared,
                dataset,
                user_id,
                "filter",
                details,
            )
        )

    except (
        ValueError,
        TypeError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message":
            (
                "Filter applied. "
                "Original dataset preserved."
            ),

        "derived_dataset":
            derived,
    }
