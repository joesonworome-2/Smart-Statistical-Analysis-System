import hashlib
import json
import secrets

from app.config import settings
from app.redis import redis_client


def generate_refresh_token() -> str:
    """Generate a secure random refresh token."""

    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """Hash refresh token before storing it in Redis."""

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def store_refresh_token(
    token: str,
    user_id: str,
) -> None:
    """Store refresh-token session in Redis."""

    token_hash = hash_refresh_token(token)

    key = f"refresh_token:{token_hash}"

    data = {
        "user_id": user_id,
    }

    redis_client.setex(
        key,
        settings.refresh_token_expire_days * 24 * 60 * 60,
        json.dumps(data),
    )


def get_refresh_token_user(token: str):
    """Retrieve user associated with refresh token."""

    token_hash = hash_refresh_token(token)

    key = f"refresh_token:{token_hash}"

    data = redis_client.get(key)

    if not data:
        return None

    return json.loads(data)


def delete_refresh_token(token: str) -> None:
    """Delete/revoke refresh token."""

    token_hash = hash_refresh_token(token)

    key = f"refresh_token:{token_hash}"

    redis_client.delete(key)
