from pymongo import MongoClient

from app.config import settings


client = MongoClient(settings.mongo_uri)

database = client[settings.mongo_database]

users_collection = database["users"]


def check_database_connection() -> bool:
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
