from __future__ import annotations

import logging
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import (
    FileResponse,
)

from app.config import settings
from app.database import (
    datasets_collection,
    reports_collection,
)
from app.schemas.report import (
    ReportDetailResponse,
    ReportGenerateResponse,
    ReportListItem,
    ReportListResponse,
)
from app.security.dependencies import (
    get_current_user,
)
from app.services.excel_generator import (
    generate_excel_report,
)
from app.services.notification_client import notify_report_ready
from app.services.pdf_generator import (
    generate_pdf_report,
)
from app.services.report_builder import (
    build_report_data,
    make_json_safe,
)


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


def _user_id(
    current_user: dict,
) -> str:

    return str(
        current_user.get(
            "_id"
        )
        or current_user.get(
            "id"
        )
    )


def _get_owned_dataset(
    dataset_id: str,
    current_user: dict,
):

    if not ObjectId.is_valid(
        dataset_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid dataset ID."
            ),
        )

    dataset = (
        datasets_collection.find_one(
            {
                "_id": ObjectId(
                    dataset_id
                )
            }
        )
    )

    if not dataset:

        raise HTTPException(
            status_code=404,
            detail=(
                "Dataset not found."
            ),
        )

    current_user_id = _user_id(
        current_user
    )

    dataset_user_id = str(
        dataset.get(
            "user_id",
            "",
        )
    )

    if (
        dataset_user_id
        != current_user_id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission "
                "to access this dataset."
            ),
        )

    return (
        dataset,
        current_user_id,
    )


@router.post(
    "/generate/{dataset_id}",
    response_model=(
        ReportGenerateResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
def generate_report(
    dataset_id: str,
    format: str = Query(
        "pdf",
        pattern="^(pdf|xlsx)$",
    ),
    authorization: str | None = Header(
        default=None
    ),
    current_user: dict = Depends(
        get_current_user
    ),
):

    dataset, user_id = (
        _get_owned_dataset(
            dataset_id,
            current_user,
        )
    )

    report_id = str(
        ObjectId()
    )

    created_at = datetime.now(
        timezone.utc
    )

    report_title = (
        "SSAS Statistical "
        "Analysis Report"
    )

    report_data = build_report_data(
        dataset=dataset,
        dataset_id=dataset_id,
        user_id=user_id,
        authorization=authorization,
    )

    extension = format

    file_name = (
        f"ssas_report_"
        f"{dataset_id}_"
        f"{report_id}."
        f"{extension}"
    )

    file_path = str(
        Path(
            settings.report_directory
        )
        / file_name
    )

    try:

        if format == "pdf":

            generate_pdf_report(
                report_data,
                file_path,
            )

        elif format == "xlsx":

            generate_excel_report(
                report_data,
                file_path,
            )

    except Exception as exc:

        logger.exception(
            "Report generation failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Report generation failed."
            ),
        )

    document = {
        "_id": ObjectId(
            report_id
        ),
        "dataset_id": dataset_id,
        "user_id": user_id,
        "title": report_title,
        "format": format,
        "file_name": file_name,
        "file_path": file_path,
        "created_at": created_at,
        "metadata": {
            "analysis_count": (
                report_data[
                    "summary"
                ][
                    "analysis_count"
                ]
            ),
            "visualization_count": (
                report_data[
                    "summary"
                ][
                    "visualization_count"
                ]
            ),
            (
                "smart_interpretation_"
                "available"
            ): (
                report_data[
                    "summary"
                ][
                    (
                        "smart_"
                        "interpretation_"
                        "available"
                    )
                ]
            ),
        },
    }

    reports_collection.insert_one(
        document
    )

    # Notify the user that the report is ready.
    # Notification failure must not cause
    # report generation to fail.
    try:

        notification_result = (
            notify_report_ready(
                report_id=report_id,
                dataset_id=dataset_id,
                file_name=file_name,
                authorization=authorization,
            )
        )

        logger.info(
            "Report-ready notification sent "
            "for report %s: %s",
            report_id,
            notification_result,
        )

    except Exception as exc:

        logger.warning(
            "Report %s was generated "
            "successfully, but notification "
            "delivery failed: %s",
            report_id,
            exc,
        )

    return (
        ReportGenerateResponse(
            report_id=report_id,
            dataset_id=dataset_id,
            title=report_title,
            format=format,
            file_name=file_name,
            created_at=created_at,
            download_endpoint=(
                f"/reports/"
                f"{report_id}"
                f"/download"
            ),
        )
    )


@router.get(
    "",
    response_model=(
        ReportListResponse
    ),
)
def list_reports(
    current_user: dict = Depends(
        get_current_user
    ),
):

    user_id = _user_id(
        current_user
    )

    documents = list(
        reports_collection.find(
            {
                "user_id": user_id
            }
        ).sort(
            "created_at",
            -1,
        )
    )

    reports = []

    for document in documents:

        reports.append(
            ReportListItem(
                report_id=str(
                    document["_id"]
                ),
                dataset_id=str(
                    document.get(
                        "dataset_id",
                        "",
                    )
                ),
                title=document.get(
                    "title",
                    "",
                ),
                format=document.get(
                    "format",
                    "",
                ),
                file_name=document.get(
                    "file_name",
                    "",
                ),
                created_at=document[
                    "created_at"
                ],
            )
        )

    return ReportListResponse(
        count=len(
            reports
        ),
        reports=reports,
    )


@router.get(
    "/{report_id}",
    response_model=(
        ReportDetailResponse
    ),
)
def get_report(
    report_id: str,
    current_user: dict = Depends(
        get_current_user
    ),
):

    if not ObjectId.is_valid(
        report_id
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid report ID."
            ),
        )

    document = (
        reports_collection.find_one(
            {
                "_id": ObjectId(
                    report_id
                )
            }
        )
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    user_id = _user_id(
        current_user
    )

    if str(
        document.get(
            "user_id"
        )
    ) != user_id:

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission "
                "to access this report."
            ),
        )

    return ReportDetailResponse(
        report_id=str(
            document["_id"]
        ),
        dataset_id=str(
            document.get(
                "dataset_id",
                "",
            )
        ),
        user_id=user_id,
        title=document.get(
            "title",
            "",
        ),
        format=document.get(
            "format",
            "",
        ),
        file_name=document.get(
            "file_name",
            "",
        ),
        created_at=document[
            "created_at"
        ],
        metadata=make_json_safe(
            document.get(
                "metadata",
                {},
            )
        ),
    )


@router.get(
    "/{report_id}/download",
)
def download_report(
    report_id: str,
    current_user: dict = Depends(
        get_current_user
    ),
):

    if not ObjectId.is_valid(
        report_id
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid report ID."
            ),
        )

    document = (
        reports_collection.find_one(
            {
                "_id": ObjectId(
                    report_id
                )
            }
        )
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    user_id = _user_id(
        current_user
    )

    if str(
        document.get(
            "user_id"
        )
    ) != user_id:

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission "
                "to download this report."
            ),
        )

    file_path = document.get(
        "file_path"
    )

    if (
        not file_path
        or not Path(
            file_path
        ).exists()
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Generated report file "
                "was not found."
            ),
        )

    report_format = document.get(
        "format"
    )

    if report_format == "pdf":

        media_type = (
            "application/pdf"
        )

    else:

        media_type = (
            "application/vnd."
            "openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )

    return FileResponse(
        path=file_path,
        filename=document[
            "file_name"
        ],
        media_type=media_type,
    )


@router.delete(
    "/{report_id}",
)
def delete_report(
    report_id: str,
    current_user: dict = Depends(
        get_current_user
    ),
):

    if not ObjectId.is_valid(
        report_id
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid report ID."
            ),
        )

    document = (
        reports_collection.find_one(
            {
                "_id": ObjectId(
                    report_id
                )
            }
        )
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    user_id = _user_id(
        current_user
    )

    if str(
        document.get(
            "user_id"
        )
    ) != user_id:

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission "
                "to delete this report."
            ),
        )

    file_path = document.get(
        "file_path"
    )

    if file_path:

        try:

            Path(
                file_path
            ).unlink(
                missing_ok=True
            )

        except Exception:

            logger.warning(
                (
                    "Unable to remove "
                    "report file: %s"
                ),
                file_path,
            )

    reports_collection.delete_one(
        {
            "_id": ObjectId(
                report_id
            )
        }
    )

    return {
        "message": (
            "Report deleted successfully."
        ),
        "report_id": report_id,
    }
