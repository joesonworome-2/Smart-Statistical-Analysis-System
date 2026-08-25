from fastapi import APIRouter, Depends, HTTPException, status

from app.database import users_collection
from app.models.user import update_timestamp, user_to_response
from app.schemas.user import (
    UserProfileUpdate,
    UserResponse,
)
from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user=Depends(get_current_user),
):
    return user_to_response(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
)
def update_my_profile(
    profile: UserProfileUpdate,
    current_user=Depends(get_current_user),
):

    update_data = {}

    if profile.first_name is not None:
        update_data["first_name"] = profile.first_name

    if profile.last_name is not None:
        update_data["last_name"] = profile.last_name

    if profile.username is not None:

        existing_username = users_collection.find_one(
            {
                "username": profile.username,
                "_id": {
                    "$ne": current_user["_id"]
                },
            }
        )

        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken.",
            )

        update_data["username"] = profile.username

    if not update_data:
        return user_to_response(current_user)

    update_data["updated_at"] = update_timestamp()

    users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_data},
    )

    updated_user = users_collection.find_one(
        {"_id": current_user["_id"]}
    )

    return user_to_response(updated_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: str,
    current_user=Depends(get_current_user),
):

    from bson import ObjectId

    try:
        object_id = ObjectId(user_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID.",
        )

    user = users_collection.find_one(
        {
            "_id": object_id,
            "is_active": True,
        }
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user_to_response(user)
