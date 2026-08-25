from pymongo import MongoClient

from app.config import settings


client = MongoClient(settings.mongo_uri)

database = client[settings.mongo_database]

datasets_collection = database["datasets"]


# Create indexes
datasets_collection.create_index(
    [("user_id", 1)],
    name="user_id_index",
)

datasets_collection.create_index(
    [("user_id", 1), ("created_at", -1)],
    name="user_created_at_index",
)


def check_database_connection() -> bool:
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
