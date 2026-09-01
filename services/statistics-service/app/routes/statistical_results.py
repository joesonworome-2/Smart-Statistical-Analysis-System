from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Query,
    status,
)

from app.schemas.statistical_result import (
    StatisticalResultSaveRequest,
)

from app.services.auth_identity import (
    get_authenticated_user,
)

from app.services.statistical_result_store import (
    delete_statistical_result,
    get_statistical_result,
    list_statistical_results,
    save_statistical_result,
)


router = APIRouter(
    prefix="/statistics/results",
    tags=[
        "Statistical Results"
    ],
)


# ==========================================================
# SAVE
# ==========================================================

@router.post(
    "",
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_result(
    request:
        StatisticalResultSaveRequest,

    authorization:
        str = Header(...),
):
    user = (
        await get_authenticated_user(
            authorization
        )
    )


    saved = (
        save_statistical_result(
            user_id=(
                user[
                    "user_id"
                ]
            ),
            payload=request,
        )
    )


    return saved


# ==========================================================
# LIST
# ==========================================================

@router.get("")
async def get_results(
    authorization:
        str = Header(...),

    dataset_id:
        str | None = Query(
            default=None
        ),

    method:
        str | None = Query(
            default=None
        ),
):
    user = (
        await get_authenticated_user(
            authorization
        )
    )


    results = (
        list_statistical_results(
            user_id=(
                user[
                    "user_id"
                ]
            ),
            dataset_id=(
                dataset_id
            ),
            method=method,
        )
    )


    return {
        "results":
            results,

        "total":
            len(results),
    }


# ==========================================================
# GET ONE
# ==========================================================

@router.get(
    "/{result_id}"
)
async def get_result(
    result_id: str,

    authorization:
        str = Header(...),
):
    user = (
        await get_authenticated_user(
            authorization
        )
    )


    result = (
        get_statistical_result(
            user_id=(
                user[
                    "user_id"
                ]
            ),
            result_id=(
                result_id
            ),
        )
    )


    if not result:

        raise HTTPException(
            status_code=404,
            detail=(
                "Statistical result "
                "not found."
            ),
        )


    return result


# ==========================================================
# DELETE
# ==========================================================

@router.delete(
    "/{result_id}"
)
async def delete_result(
    result_id: str,

    authorization:
        str = Header(...),
):
    user = (
        await get_authenticated_user(
            authorization
        )
    )


    deleted = (
        delete_statistical_result(
            user_id=(
                user[
                    "user_id"
                ]
            ),
            result_id=(
                result_id
            ),
        )
    )


    if not deleted:

        raise HTTPException(
            status_code=404,
            detail=(
                "Statistical result "
                "not found."
            ),
        )


    return {
        "message":
            "Statistical result "
            "deleted successfully.",

        "result_id":
            result_id,
    }
