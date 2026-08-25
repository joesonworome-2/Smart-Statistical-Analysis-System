from typing import Optional

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel, Field

from app.database import users_collection
from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/users/admin",
    tags=["Admin User Management"],
)


class RoleUpdateRequest(BaseModel):
    role: str = Field(
        pattern="^(user|admin)$"
    )


class StatusUpdateRequest(BaseModel):
    is_active: bool


def require_admin(
    current_user=Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Administrator access required."
            ),
        )

    return current_user


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "username": user.get("username"),
        "first_name": user.get(
            "first_name",
            "",
        ),
        "last_name": user.get(
            "last_name",
            "",
        ),
        "role": user.get(
            "role",
            "user",
        ),
        "is_active": user.get(
            "is_active",
            True,
        ),
        "auth_provider": user.get(
            "auth_provider",
            "password",
        ),
        "created_at": (
            user.get("created_at").isoformat()
            if user.get("created_at")
            else None
        ),
        "updated_at": (
            user.get("updated_at").isoformat()
            if user.get("updated_at")
            else None
        ),
    }


@router.get("/stats")
def user_statistics(
    admin=Depends(require_admin),
):
    total_users = users_collection.count_documents(
        {}
    )

    active_users = users_collection.count_documents(
        {
            "is_active": True,
        }
    )

    inactive_users = (
        total_users
        - active_users
    )

    admins = users_collection.count_documents(
        {
            "role": "admin",
        }
    )

    normal_users = users_collection.count_documents(
        {
            "role": "user",
        }
    )

    google_users = users_collection.count_documents(
        {
            "auth_provider": "google",
        }
    )

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "admins": admins,
        "normal_users": normal_users,
        "google_users": google_users,
    }


@router.get("/list")
def list_users(
    search: Optional[str] = Query(
        default=None,
        max_length=100,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    admin=Depends(require_admin),
):
    query = {}

    if search:
        expression = {
            "$regex": search,
            "$options": "i",
        }

        query = {
            "$or": [
                {
                    "email": expression,
                },
                {
                    "username": expression,
                },
                {
                    "first_name": expression,
                },
                {
                    "last_name": expression,
                },
            ]
        }

    total = users_collection.count_documents(
        query
    )

    users = list(
        users_collection.find(
            query
        )
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    return {
        "total": total,
        "users": [
            serialize_user(user)
            for user in users
        ],
    }


@router.get("/{user_id}")
def admin_get_user(
    user_id: str,
    admin=Depends(require_admin),
):
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
        }
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return serialize_user(user)


@router.patch("/{user_id}/role")
def update_user_role(
    user_id: str,
    request: RoleUpdateRequest,
    admin=Depends(require_admin),
):
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
        }
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if str(user["_id"]) == str(
        admin["_id"]
    ):
        if request.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "You cannot remove your own "
                    "administrator role."
                ),
            )

    users_collection.update_one(
        {
            "_id": object_id,
        },
        {
            "$set": {
                "role": request.role,
            }
        },
    )

    updated_user = users_collection.find_one(
        {
            "_id": object_id,
        }
    )

    return {
        "message": (
            "User role updated successfully."
        ),
        "user": serialize_user(
            updated_user
        ),
    }


@router.patch("/{user_id}/status")
def update_user_status(
    user_id: str,
    request: StatusUpdateRequest,
    admin=Depends(require_admin),
):
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
        }
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if (
        str(user["_id"])
        == str(admin["_id"])
        and request.is_active is False
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "You cannot deactivate "
                "your own administrator account."
            ),
        )

    users_collection.update_one(
        {
            "_id": object_id,
        },
        {
            "$set": {
                "is_active":
                    request.is_active,
            }
        },
    )

    updated_user = users_collection.find_one(
        {
            "_id": object_id,
        }
    )

    return {
        "message": (
            "User account status "
            "updated successfully."
        ),
        "user": serialize_user(
            updated_user
        ),
    }

