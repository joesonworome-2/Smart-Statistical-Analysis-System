from datetime import datetime, timezone


def create_analysis_document(
    dataset_id: str,
    user_id: str,
    analysis_type: str,
    results: dict,
):
    now = datetime.now(timezone.utc)

    return {
        "dataset_id": dataset_id,
        "user_id": user_id,
        "analysis_type": analysis_type,
        "results": results,
        "created_at": now,
        "updated_at": now,
    }
