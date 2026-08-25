from datetime import datetime, timezone


def create_dataset_document(
    user_id: str,
    filename: str,
    original_filename: str,
    file_type: str,
    file_size: int,
    row_count: int,
    column_count: int,
    columns: list[str],
):
    now = datetime.now(timezone.utc)

    return {
        "user_id": user_id,
        "filename": filename,
        "original_filename": original_filename,
        "file_type": file_type,
        "file_size": file_size,
        "row_count": row_count,
        "column_count": column_count,
        "columns": columns,
        "status": "uploaded",
        "created_at": now,
        "updated_at": now,
    }
