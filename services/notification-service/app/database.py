from pymongo import ASCENDING, DESCENDING, MongoClient

from app.config import settings


client = MongoClient(
    settings.mongo_uri,
    serverSelectionTimeoutMS=5000,
)

database = client[settings.mongo_database]

users_collection = database["users"]
notifications_collection = database["notifications"]


def database_is_available() -> bool:
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False


def ensure_indexes():
    notifications_collection.create_index(
        [
            ("user_id", ASCENDING),
            ("created_at", DESCENDING),
        ],
        name="user_notifications",
    )

    notifications_collection.create_index(
        [
            ("user_id", ASCENDING),
            ("is_read", ASCENDING),
        ],
        name="user_unread_notifications",
    )
