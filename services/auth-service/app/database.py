from pymongo import MongoClient

from app.config import settings


client = MongoClient(settings.mongo_uri)

database = client[settings.mongo_database]

users_collection = database["users"]


def initialize_database():
    """Create required MongoDB indexes."""

    users_collection.create_index(
        "email",
        unique=True,
        name="unique_email",
    )

    users_collection.create_index(
        "username",
        unique=True,
        name="unique_username",
    )


def check_database_connection() -> bool:
    """Check whether MongoDB is reachable."""

    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
