from pymongo import MongoClient

from app.config import settings


# ============================================================
# MongoDB client / database
# ============================================================

client = MongoClient(
    settings.mongo_uri
)

database = client[
    settings.mongo_database
]


# ============================================================
# Collections used by the report service
# ============================================================

users_collection = database[
    "users"
]

datasets_collection = database[
    "datasets"
]

# Legacy analysis-service results.
analyses_collection = database[
    "analyses"
]

# Results saved by the statistics-service.  This is the
# collection used by the new Analysis UI and is essential for
# generating a report containing the exact calculations the
# user performed.
statistical_results_collection = database[
    "statistical_results"
]

visualizations_collection = database[
    "visualizations"
]

reports_collection = database[
    "reports"
]


# ============================================================
# Database health check
# ============================================================

def database_is_available() -> bool:
    try:
        client.admin.command(
            "ping"
        )
        return True
    except Exception:
        return False
