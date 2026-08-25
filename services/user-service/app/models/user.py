from datetime import datetime, timezone


def user_to_response(user: dict) -> dict:
    """
    Convert MongoDB user document into API response data.
    """

    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "username": user["username"],
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "role": user.get("role", "user"),
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


def update_timestamp() -> datetime:
    return datetime.now(timezone.utc)
