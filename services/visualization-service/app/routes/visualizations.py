from datetime import datetime, timezone
import json
import logging

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from plotly.utils import PlotlyJSONEncoder

from app.database import (
    datasets_collection,
    visualizations_collection,
)

from app.schemas.visualization import (
    AutoVisualizationResponse,
    VisualizationRecommendationResponse,
    VisualizationRequest,
    VisualizationResponse,
)

from app.security.dependencies import (
    get_current_user,
)

from app.services.chart_engine import (
    SUPPORTED_CHARTS,
    generate_chart,
)

from app.services.dataset_reader import (
    load_dataset,
)

from app.services.recommendation_engine import (
    recommend_visualizations,
)


# ============================================================
# Logging
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/visualizations",
    tags=["Visualizations"],
)


# ============================================================
# Helper: Get owned dataset
# ============================================================

def get_owned_dataset(
    dataset_id: str,
    current_user: dict,
) -> tuple[dict, str]:

    if not ObjectId.is_valid(
        dataset_id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one(
        {
            "_id": ObjectId(
                dataset_id
            )
        }
    )

    if not dataset:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Dataset not found.",
        )

    current_user_id = str(
        current_user.get("_id")
        or current_user.get("id")
    )

    dataset_user_id = str(
        dataset.get(
            "user_id",
            ""
        )
    )

    if (
        current_user_id
        != dataset_user_id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "You do not have permission "
                "to access this dataset."
            ),
        )

    return (
        dataset,
        current_user_id,
    )


# ============================================================
# Helper: Load dataframe
# ============================================================

def get_dataset_dataframe(
    dataset: dict,
):

    filename = dataset.get(
        "filename"
    )

    if not filename:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Dataset file information "
                "is missing."
            ),
        )

    try:
        return load_dataset(
            filename
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Dataset file could not "
                "be found in storage."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        )

    except Exception as exc:
        logger.exception(
            "Dataset loading failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to load dataset."
            ),
        )


# ============================================================
# GET: Visualization Types
# ============================================================

@router.get(
    "/types",
)
def get_visualization_types():

    return {
        "count": len(
            SUPPORTED_CHARTS
        ),
        "visualization_types": (
            SUPPORTED_CHARTS
        ),
    }


# ============================================================
# GET: Smart Recommendations
# ============================================================

@router.get(
    "/recommend/{dataset_id}",
    response_model=(
        VisualizationRecommendationResponse
    ),
)
def recommend_charts(
    dataset_id: str,
    goal: str = "automatic",
    limit: int = 10,
    current_user: dict = Depends(
        get_current_user
    ),
):

    dataset, _ = get_owned_dataset(
        dataset_id,
        current_user,
    )

    dataframe = get_dataset_dataframe(
        dataset
    )

    safe_limit = min(
        max(
            limit,
            1,
        ),
        25,
    )

    try:
        result = recommend_visualizations(
            dataframe=dataframe,
            goal=goal,
            limit=safe_limit,
        )

    except ValueError as exc:
        logger.exception(
            "Recommendation validation "
            "failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        )

    except Exception as exc:
        logger.exception(
            "Visualization recommendation "
            "failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to generate "
                "visualization recommendations."
            ),
        )

    return (
        VisualizationRecommendationResponse(
            dataset_id=dataset_id,
            **result,
        )
    )


# ============================================================
# POST: Automatically Generate Recommended Visualization
# ============================================================

@router.post(
    "/auto-generate/{dataset_id}",
    response_model=(
        AutoVisualizationResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
def auto_generate_visualization(
    dataset_id: str,
    goal: str = "automatic",
    rank: int = 1,
    current_user: dict = Depends(
        get_current_user
    ),
):

    # --------------------------------------------------------
    # Dataset / ownership
    # --------------------------------------------------------

    dataset, current_user_id = (
        get_owned_dataset(
            dataset_id,
            current_user,
        )
    )

    dataframe = get_dataset_dataframe(
        dataset
    )

    # --------------------------------------------------------
    # Validate recommendation rank
    # --------------------------------------------------------

    if rank < 1:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Recommendation rank must "
                "be 1 or greater."
            ),
        )

    # --------------------------------------------------------
    # Generate recommendations
    # --------------------------------------------------------

    try:
        recommendation_result = (
            recommend_visualizations(
                dataframe=dataframe,
                goal=goal,
                limit=25,
            )
        )

    except Exception as exc:
        logger.exception(
            "Automatic recommendation "
            "failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to determine an "
                "appropriate visualization."
            ),
        )

    recommendations = (
        recommendation_result.get(
            "recommendations",
            [],
        )
    )

    if not recommendations:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "No suitable visualization "
                "could be recommended."
            ),
        )

    if rank > len(
        recommendations
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                f"Recommendation rank {rank} "
                f"is unavailable. Only "
                f"{len(recommendations)} "
                f"recommendations were generated."
            ),
        )

    # --------------------------------------------------------
    # Select requested recommendation
    # --------------------------------------------------------

    selected = recommendations[
        rank - 1
    ]

    chart_type = selected[
        "chart_type"
    ]

    suggested_config = dict(
        selected.get(
            "suggested_config",
            {},
        )
    )

    # --------------------------------------------------------
    # Build VisualizationRequest
    # --------------------------------------------------------

    try:
        visualization_request = (
            VisualizationRequest(
                chart_type=chart_type,
                **suggested_config,
            )
        )

    except Exception as exc:
        logger.exception(
            "Automatic request creation "
            "failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "The recommended visualization "
                "configuration is invalid."
            ),
        )

    # --------------------------------------------------------
    # Generate chart
    # --------------------------------------------------------

    try:
        figure = generate_chart(
            dataframe,
            visualization_request,
        )

    except ValueError as exc:
        logger.exception(
            "Automatic chart generation "
            "validation failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        )

    except Exception as exc:
        logger.exception(
            "Automatic visualization "
            "generation failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Automatic visualization "
                "generation failed."
            ),
        )

    # --------------------------------------------------------
    # Convert Plotly chart to JSON-safe dictionary
    # --------------------------------------------------------

    chart_json = json.loads(
        json.dumps(
            figure.to_plotly_json(),
            cls=PlotlyJSONEncoder,
        )
    )

    created_at = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # Store automatic visualization metadata
    # --------------------------------------------------------

    document = {
        "dataset_id": dataset_id,
        "user_id": current_user_id,
        "visualization_type": (
            chart_type
        ),
        "generation_mode": (
            "automatic"
        ),
        "goal": goal,
        "recommendation_rank": (
            rank
        ),
        "recommendation": (
            selected
        ),
        "request": (
            visualization_request.model_dump()
        ),
        "created_at": (
            created_at
        ),
    }

    visualizations_collection.insert_one(
        document
    )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return AutoVisualizationResponse(
        dataset_id=dataset_id,
        visualization_type=chart_type,
        recommendation=selected,
        chart=chart_json,
        metadata={
            "generation_mode": (
                "automatic"
            ),
            "goal": goal,
            "recommendation_rank": (
                rank
            ),
            "confidence_percent": (
                selected[
                    "confidence_percent"
                ]
            ),
            "row_count": int(
                len(
                    dataframe
                )
            ),
            "column_count": int(
                len(
                    dataframe.columns
                )
            ),
            "warnings": (
                recommendation_result[
                    "dataset_profile"
                ].get(
                    "warnings",
                    [],
                )
            ),
            "created_at": (
                created_at.isoformat()
            ),
        },
    )


# ============================================================
# POST: Manual Visualization Generation
# ============================================================

@router.post(
    "/generate/{dataset_id}",
    response_model=(
        VisualizationResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
def generate_visualization(
    dataset_id: str,
    request: VisualizationRequest,
    current_user: dict = Depends(
        get_current_user
    ),
):

    dataset, current_user_id = (
        get_owned_dataset(
            dataset_id,
            current_user,
        )
    )

    dataframe = get_dataset_dataframe(
        dataset
    )

    # --------------------------------------------------------
    # Generate chart
    # --------------------------------------------------------

    try:
        figure = generate_chart(
            dataframe,
            request,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        )

    except Exception as exc:
        logger.exception(
            "Visualization generation "
            "failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Visualization generation "
                f"failed: {str(exc)}"
            ),
        )

    # --------------------------------------------------------
    # Plotly JSON serialization
    # --------------------------------------------------------

    chart_json = json.loads(
        json.dumps(
            figure.to_plotly_json(),
            cls=PlotlyJSONEncoder,
        )
    )

    created_at = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # Store metadata
    # --------------------------------------------------------

    document = {
        "dataset_id": dataset_id,
        "user_id": current_user_id,
        "visualization_type": (
            request.chart_type
        ),
        "generation_mode": (
            "manual"
        ),
        "request": (
            request.model_dump()
        ),
        "created_at": (
            created_at
        ),
    }

    visualizations_collection.insert_one(
        document
    )

    # --------------------------------------------------------
    # Return visualization
    # --------------------------------------------------------

    return VisualizationResponse(
        dataset_id=dataset_id,
        visualization_type=(
            request.chart_type
        ),
        chart=chart_json,
        metadata={
            "generation_mode": (
                "manual"
            ),
            "row_count": int(
                len(
                    dataframe
                )
            ),
            "column_count": int(
                len(
                    dataframe.columns
                )
            ),
            "created_at": (
                created_at.isoformat()
            ),
        },
    )
