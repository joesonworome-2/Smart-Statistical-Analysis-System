from pymongo import MongoClient

from app.config import settings


client = MongoClient(
    settings.mongo_uri
)

database = client[
    settings.mongo_database
]

users_collection = database["users"]
datasets_collection = database["datasets"]
visualizations_collection = database["visualizations"]
analyses_collection = database["analyses"]
