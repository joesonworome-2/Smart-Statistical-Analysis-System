import logging

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.database import (
    datasets_collection,
)

from app.schemas.interpretation import (
    VisualizationInterpretationResponse,
)

from app.security.dependencies import (
    get_current_user,
)

from app.services.dataset_reader import (
    load_dataset,
)

from app.services.interpretation_engine import (
    interpret_visualization,
)

from app.services.recommendation_engine import (
    recommend_visualizations,
)


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/visualizations",
    tags=[
        "Visualization Interpretation"
    ],
)


# ============================================================
# GET: Smart visualization interpretation
# ============================================================


@router.get(
    "/interpret/{dataset_id}",
    response_model=(
        VisualizationInterpretationResponse
    ),
)
def interpret_recommended_visualization(
    dataset_id: str,
    goal: str = "automatic",
    rank: int = 1,
    current_user: dict = Depends(
        get_current_user
    ),
):

    # --------------------------------------------------------
    # Validate ID
    # --------------------------------------------------------

    if not ObjectId.is_valid(
        dataset_id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail="Invalid dataset ID.",
        )

    # --------------------------------------------------------
    # Find dataset
    # --------------------------------------------------------

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
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Dataset not found.",
        )

    # --------------------------------------------------------
    # Ownership
    # --------------------------------------------------------

    current_user_id = str(
        current_user.get("_id")
        or current_user.get("id")
    )

    dataset_user_id = str(
        dataset.get(
            "user_id",
            "",
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

    # --------------------------------------------------------
    # Validate rank
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
    # Filename
    # --------------------------------------------------------

    filename = dataset.get(
        "filename"
    )

    if not filename:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Dataset filename is missing."
            ),
        )

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    try:
        dataframe = load_dataset(
            filename
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Dataset file could not "
                "be found."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(
                exc
            ),
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
            "Recommendation generation "
            "failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to generate chart "
                "recommendations."
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
                "recommendation was found."
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
                f"is unavailable. "
                f"{len(recommendations)} "
                "recommendations were found."
            ),
        )

    selected = recommendations[
        rank - 1
    ]

    # --------------------------------------------------------
    # Interpret selected visualization
    # --------------------------------------------------------

    try:
        interpretation = (
            interpret_visualization(
                dataframe=dataframe,
                recommendation=selected,
                profile=(
                    recommendation_result[
                        "dataset_profile"
                    ]
                ),
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(
                exc
            ),
        )

    except Exception as exc:
        logger.exception(
            "Visualization interpretation "
            "failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to interpret "
                "visualization."
            ),
        )

    # --------------------------------------------------------
    # Return interpretation
    # --------------------------------------------------------

    return (
        VisualizationInterpretationResponse(
            dataset_id=dataset_id,
            goal=goal,
            rank=rank,
            recommendation=selected,
            interpretation=interpretation,
        )
    )
