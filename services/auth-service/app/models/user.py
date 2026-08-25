from datetime import datetime, timezone
from typing import Any


def create_user_document(
    email: str,
    username: str,
    password_hash: str,
    first_name: str,
    last_name: str,
    role: str = "user",
) -> dict[str, Any]:

    now = datetime.now(timezone.utc)

    return {
        "email": email.lower(),
        "username": username,
        "password_hash": password_hash,
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
