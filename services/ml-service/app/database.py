from pymongo import MongoClient

from app.config import settings


client = MongoClient(
    settings.mongo_uri,
    serverSelectionTimeoutMS=5000,
)

database = client[settings.mongo_database]

users_collection = database["users"]
datasets_collection = database["datasets"]
ml_results_collection = database["ml_results"]


def database_is_available() -> bool:
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
