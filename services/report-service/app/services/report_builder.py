from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
from typing import Any

import httpx
from bson import ObjectId

from app.config import settings
from app.database import (
    analyses_collection,
    visualizations_collection,
)


def make_json_safe(
    value: Any,
) -> Any:

    if isinstance(
        value,
        ObjectId,
    ):
        return str(
            value
        )

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): make_json_safe(
                item
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            make_json_safe(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return [
            make_json_safe(
                item
            )
            for item in value
        ]

    return value


def _dataset_query(
    dataset_id: str,
) -> dict[str, Any]:

    possible_values: list[
        Any
    ] = [
        dataset_id,
    ]

    if ObjectId.is_valid(
        dataset_id
    ):
        possible_values.append(
            ObjectId(
                dataset_id
            )
        )

    return {
        "dataset_id": {
            "$in": possible_values
        }
    }


def get_analysis_results(
    dataset_id: str,
    user_id: str,
) -> list[dict[str, Any]]:

    query = _dataset_query(
        dataset_id
    )

    query["user_id"] = {
        "$in": [
            user_id,
            (
                ObjectId(user_id)
                if ObjectId.is_valid(
                    user_id
                )
                else user_id
            ),
        ]
    }

    analyses = list(
        analyses_collection.find(
            query
        ).sort(
            "created_at",
            1,
        )
    )

    return make_json_safe(
        analyses
    )


def get_visualization_results(
    dataset_id: str,
    user_id: str,
) -> list[dict[str, Any]]:

    query = _dataset_query(
        dataset_id
    )

    query["user_id"] = {
        "$in": [
            user_id,
            (
                ObjectId(user_id)
                if ObjectId.is_valid(
                    user_id
                )
                else user_id
            ),
        ]
    }

    visualizations = list(
        visualizations_collection.find(
            query
        ).sort(
            "created_at",
            1,
        )
    )

    return make_json_safe(
        visualizations
    )


def get_smart_interpretation(
    dataset_id: str,
    authorization: str | None,
) -> dict[str, Any] | None:

    if not authorization:
        return None

    url = (
        f"{settings.visualization_service_url}"
        f"/visualizations/interpret/"
        f"{dataset_id}"
    )

    try:

        with httpx.Client(
            timeout=20.0
        ) as client:

            response = client.get(
                url,
                headers={
                    "Authorization": (
                        authorization
                    )
                },
                params={
                    "goal": "automatic",
                    "rank": 1,
                },
            )

        if response.status_code != 200:
            return {
                "available": False,
                "status_code": (
                    response.status_code
                ),
                "detail": (
                    response.text
                ),
            }

        result = response.json()

        return {
            "available": True,
            **result,
        }

    except Exception as exc:

        return {
            "available": False,
            "detail": str(
                exc
            ),
        }


def build_report_data(
    dataset: dict[str, Any],
    dataset_id: str,
    user_id: str,
    authorization: str | None,
) -> dict[str, Any]:

    generated_at = datetime.now(
        timezone.utc
    )

    analyses = get_analysis_results(
        dataset_id,
        user_id,
    )

    visualizations = (
        get_visualization_results(
            dataset_id,
            user_id,
        )
    )

    interpretation = (
        get_smart_interpretation(
            dataset_id,
            authorization,
        )
    )

    dataset_safe = make_json_safe(
        dataset
    )

    return {
        "title": (
            "SSAS Statistical "
            "Analysis Report"
        ),
        "generated_at": (
            generated_at.isoformat()
        ),
        "dataset_id": dataset_id,
        "user_id": user_id,
        "dataset": dataset_safe,
        "summary": {
            "analysis_count": len(
                analyses
            ),
            "visualization_count": len(
                visualizations
            ),
            "smart_interpretation_available": (
                bool(
                    interpretation
                    and interpretation.get(
                        "available"
                    )
                )
            ),
        },
        "analyses": analyses,
        "visualizations": (
            visualizations
        ),
        "smart_interpretation": (
            interpretation
        ),
    }
