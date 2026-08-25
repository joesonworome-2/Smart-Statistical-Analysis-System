from pymongo import MongoClient

from app.config import settings


client = MongoClient(settings.mongo_uri)
database = client[settings.mongo_database]

users_collection = database["users"]
datasets_collection = database["datasets"]
analyses_collection = database["analyses"]


def database_is_available() -> bool:
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
