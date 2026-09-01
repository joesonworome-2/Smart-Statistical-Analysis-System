import os

from datetime import (
    datetime,
    timezone,
)

from bson import ObjectId

from pymongo import (
    ASCENDING,
    DESCENDING,
    MongoClient,
)

from app.config import settings


_client = None

_database = None

_collection = None


# ==========================================================
# SETTINGS HELPER
# ==========================================================

def setting_value(
    *names,
    default=None,
):
    for name in names:

        if hasattr(
            settings,
            name,
        ):
            value = getattr(
                settings,
                name,
            )

            if value:
                return value

    return default


# ==========================================================
# MONGODB
# ==========================================================

def get_results_collection():
    global _client
    global _database
    global _collection


    if _collection is not None:
        return _collection


    uri = setting_value(
        "mongodb_url",
        "mongo_url",
        "mongodb_uri",
        "mongo_uri",
        default=(
            os.getenv(
                "MONGODB_URL"
            )
            or
            os.getenv(
                "MONGODB_URI"
            )
            or
            "mongodb://mongodb:27017"
        ),
    )


    database_name = setting_value(
        "mongodb_database",
        "mongo_database",
        "database_name",
        "mongo_db",
        default=(
            os.getenv(
                "MONGODB_DATABASE"
            )
            or
            os.getenv(
                "MONGO_DATABASE"
            )
            or
            "ssas"
        ),
    )


    _client = MongoClient(
        uri
    )


    _database = _client[
        database_name
    ]


    _collection = _database[
        "statistical_results"
    ]


    _collection.create_index(
        [
            (
                "user_id",
                ASCENDING,
            ),
            (
                "created_at",
                DESCENDING,
            ),
        ],
        name=(
            "results_user_created"
        ),
    )


    _collection.create_index(
        [
            (
                "dataset_id",
                ASCENDING,
            ),
            (
                "method",
                ASCENDING,
            ),
        ],
        name=(
            "results_dataset_method"
        ),
    )


    return _collection


# ==========================================================
# SERIALIZE
# ==========================================================

def serialize_result(
    document
):
    return {
        "id":
            str(
                document["_id"]
            ),

        "user_id":
            document[
                "user_id"
            ],

        "dataset_id":
            document[
                "dataset_id"
            ],

        "dataset_name":
            document.get(
                "dataset_name"
            ),

        "method":
            document[
                "method"
            ],

        "title":
            document[
                "title"
            ],

        "configuration":
            document.get(
                "configuration",
                {},
            ),

        "tables":
            document.get(
                "tables",
                [],
            ),

        "assumptions":
            document.get(
                "assumptions"
            ),

        "interpretation":
            document.get(
                "interpretation"
            ),

        "apa":
            document.get(
                "apa"
            ),

        "metadata":
            document.get(
                "metadata",
                {},
            ),

        "created_at":
            document[
                "created_at"
            ],

        "updated_at":
            document[
                "updated_at"
            ],
"detailed_explanation":
    document.get(
        "detailed_explanation"
    ),		
    }


# ==========================================================
# CREATE
# ==========================================================

def save_statistical_result(
    user_id,
    payload,
):
    collection = (
        get_results_collection()
    )


    now = datetime.now(
        timezone.utc
    )


    document = {
        "user_id":
            user_id,

        "dataset_id":
            payload.dataset_id,

        "dataset_name":
            payload.dataset_name,

        "method":
            payload.method,

        "title":
            payload.title,

        "configuration":
            payload.configuration,

        "tables":
            payload.tables,

        "assumptions":
            payload.assumptions,

        "interpretation":
            payload.interpretation,

        "apa":
            payload.apa,

        "metadata":
            payload.metadata,

        "created_at":
            now,

        "updated_at":
            now,
    }


    result = collection.insert_one(
        document
    )


    document["_id"] = (
        result.inserted_id
    )


    return serialize_result(
        document
    )


# ==========================================================
# LIST
# ==========================================================

def list_statistical_results(
    user_id,
    dataset_id=None,
    method=None,
):
    collection = (
        get_results_collection()
    )


    query = {
        "user_id":
            user_id
    }


    if dataset_id:
        query[
            "dataset_id"
        ] = dataset_id


    if method:
        query[
            "method"
        ] = method


    cursor = collection.find(
        query
    ).sort(
        "created_at",
        DESCENDING,
    )


    return [
        serialize_result(
            document
        )
        for document
        in cursor
    ]


# ==========================================================
# GET ONE
# ==========================================================

def get_statistical_result(
    user_id,
    result_id,
):
    try:
        object_id = (
            ObjectId(
                result_id
            )
        )

    except Exception:
        return None


    document = (
        get_results_collection()
        .find_one({
            "_id":
                object_id,

            "user_id":
                user_id,
        })
    )


    if not document:
        return None


    return serialize_result(
        document
    )


# ==========================================================
# DELETE
# ==========================================================

def delete_statistical_result(
    user_id,
    result_id,
):
    try:
        object_id = (
            ObjectId(
                result_id
            )
        )

    except Exception:
        return False


    result = (
        get_results_collection()
        .delete_one({
            "_id":
                object_id,

            "user_id":
                user_id,
        })
    )


    return bool(
        result.deleted_count
    )
