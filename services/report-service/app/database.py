from pymongo import MongoClient

from app.config import settings


# ============================================================
# MongoDB Client
# ============================================================

client = MongoClient(
    settings.mongo_uri
)


# ============================================================
# SSAS Database
# ============================================================

database = client[
    settings.mongo_database
]


# ============================================================
# Collections
# ============================================================

users_collection = database[
    "users"
]

datasets_collection = database[
    "datasets"
]

analyses_collection = database[
    "analyses"
]

visualizations_collection = database[
    "visualizations"
]

reports_collection = database[
    "reports"
]


# ============================================================
# Database Health Check
# ============================================================

def database_is_available() -> bool:

    try:

        client.admin.command(
            "ping"
        )

        return True

    except Exception:

        return False
from app.config import settings


client = MongoClient(
    settings.mongo_uri
)

database = client[
    settings.mongo_database
]


datasets_collection = database[
    "datasets"
]

analyses_collection = database[
    "analyses"
]

visualizations_collection = database[
    "visualizations"
]

reports_collection = database[
    "reports"
]


def database_is_available() -> bool:

    try:

        client.admin.command(
            "ping"
        )

        return True

    except Exception:

        return False
