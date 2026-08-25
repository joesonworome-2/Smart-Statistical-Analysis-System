from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import (
    analyses_collection,
    datasets_collection,
)

from app.models.analysis import create_analysis_document
from app.schemas.analysis import AnalysisResponse
from app.security.dependencies import get_current_user

from app.services.dataset_reader import load_dataset
from app.services.descriptive_statistics import analyze_dataframe
from app.services.correlation_analysis import analyze_correlation

from app.statistics.regression import (
    simple_linear_regression,
)

from app.statistics.multiple_regression import (
    multiple_linear_regression,
)

from app.statistics.regression_diagnostics import (
    analyze_regression_diagnostics,
)

from app.statistics.hypothesis_testing import (
    one_sample_t_test,
    independent_t_test,
    paired_t_test,
    chi_square_independence,
    shapiro_normality_test,
    mann_whitney_test,
    wilcoxon_test,
    kruskal_wallis_test,
)

from app.statistics.anova import (
    one_way_anova,
    tukey_hsd,
    levene_test,
)


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


# ============================================================
# Correlation Analysis
# ============================================================

@router.post(
    "/correlation/{dataset_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def correlation_analysis(
    dataset_id: str,
    current_user=Depends(get_current_user),
):

    try:
        dataset_object_id = ObjectId(dataset_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one(
        {"_id": dataset_object_id}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    dataset_user_id = str(
        dataset.get("user_id")
    )

    current_user_id = str(
        current_user["_id"]
    )

    if dataset_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to "
                "analyze this dataset."
            ),
        )

    filename = dataset.get("filename")

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file information is missing.",
        )

    try:
        dataframe = load_dataset(filename)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Dataset file could not be found "
                "in storage."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to read dataset: {str(exc)}",
        )

    try:
        results = analyze_correlation(
            dataframe
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Correlation analysis failed: {str(exc)}"
            ),
        )

    analysis_document = create_analysis_document(
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="correlation",
        results=results,
    )

    result = analyses_collection.insert_one(
        analysis_document
    )

    return AnalysisResponse(
        id=str(result.inserted_id),
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="correlation",
        results=results,
        created_at=analysis_document[
            "created_at"
        ].isoformat(),
    )


# ============================================================
# Descriptive Statistics
# ============================================================

@router.post(
    "/descriptive/{dataset_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def descriptive_analysis(
    dataset_id: str,
    current_user=Depends(get_current_user),
):

    try:
        dataset_object_id = ObjectId(dataset_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one(
        {"_id": dataset_object_id}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    dataset_user_id = str(
        dataset.get("user_id")
    )

    current_user_id = str(
        current_user["_id"]
    )

    if dataset_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to "
                "analyze this dataset."
            ),
        )

    filename = dataset.get("filename")

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file information is missing.",
        )

    try:
        dataframe = load_dataset(filename)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Dataset file could not be found "
                "in storage."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to read dataset: {str(exc)}",
        )

    try:
        results = analyze_dataframe(
            dataframe
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Statistical analysis failed: {str(exc)}"
            ),
        )

    analysis_document = create_analysis_document(
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="descriptive_statistics",
        results=results,
    )

    result = analyses_collection.insert_one(
        analysis_document
    )

    return AnalysisResponse(
        id=str(result.inserted_id),
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="descriptive_statistics",
        results=results,
        created_at=analysis_document[
            "created_at"
        ].isoformat(),
    )


# ============================================================
# Simple Linear Regression
# ============================================================

@router.post(
    "/regression/{dataset_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def regression_analysis(
    dataset_id: str,
    x_variable: str,
    y_variable: str,
    current_user=Depends(get_current_user),
):

    try:
        dataset_object_id = ObjectId(dataset_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one(
        {"_id": dataset_object_id}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    dataset_user_id = str(
        dataset.get("user_id")
    )

    current_user_id = str(
        current_user["_id"]
    )

    if dataset_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to "
                "analyze this dataset."
            ),
        )

    if x_variable == y_variable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Predictor and response variables "
                "must be different."
            ),
        )

    filename = dataset.get("filename")

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file information is missing.",
        )

    try:
        dataframe = load_dataset(filename)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Dataset file could not be found "
                "in storage."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to read dataset: {str(exc)}",
        )

    if x_variable not in dataframe.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Predictor variable '{x_variable}' "
                "was not found in the dataset."
            ),
        )

    if y_variable not in dataframe.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Response variable '{y_variable}' "
                "was not found in the dataset."
            ),
        )

    try:
        results = simple_linear_regression(
            dataframe=dataframe,
            x_variable=x_variable,
            y_variable=y_variable,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Regression analysis failed: {str(exc)}"
            ),
        )

    analysis_document = create_analysis_document(
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="simple_linear_regression",
        results=results,
    )

    result = analyses_collection.insert_one(
        analysis_document
    )

    return AnalysisResponse(
        id=str(result.inserted_id),
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="simple_linear_regression",
        results=results,
        created_at=analysis_document[
            "created_at"
        ].isoformat(),
    )


# ============================================================
# Multiple Linear Regression
# ============================================================

@router.post(
    "/multiple-regression/{dataset_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def multiple_regression_analysis(
    dataset_id: str,
    dependent_variable: str,
    independent_variables: str,
    current_user=Depends(get_current_user),
):

    try:
        dataset_object_id = ObjectId(dataset_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one(
        {"_id": dataset_object_id}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    dataset_user_id = str(
        dataset.get("user_id")
    )

    current_user_id = str(
        current_user["_id"]
    )

    if dataset_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to "
                "analyze this dataset."
            ),
        )

    filename = dataset.get("filename")

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file information is missing.",
        )

    try:
        dataframe = load_dataset(filename)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Dataset file could not be found "
                "in storage."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to read dataset: {str(exc)}",
        )

    predictor_variables = [
        variable.strip()
        for variable in independent_variables.split(",")
        if variable.strip()
    ]

    if len(predictor_variables) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Multiple linear regression requires "
                "at least two independent variables."
            ),
        )

    if dependent_variable in predictor_variables:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The dependent variable cannot also be "
                "an independent variable."
            ),
        )

    variables_to_check = [
        dependent_variable
    ] + predictor_variables

    missing_variables = [
        variable
        for variable in variables_to_check
        if variable not in dataframe.columns
    ]

    if missing_variables:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The following variables were not found "
                f"in the dataset: {missing_variables}"
            ),
        )

    try:
        results = multiple_linear_regression(
            dataframe=dataframe,
            predictor_variables=predictor_variables,
            response_variable=dependent_variable,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Multiple linear regression failed: "
                f"{str(exc)}"
            ),
        )

    analysis_document = create_analysis_document(
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="multiple_linear_regression",
        results=results,
    )

    result = analyses_collection.insert_one(
        analysis_document
    )

    return AnalysisResponse(
        id=str(result.inserted_id),
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="multiple_linear_regression",
        results=results,
        created_at=analysis_document[
            "created_at"
        ].isoformat(),
    )


# ============================================================
# Regression Diagnostics
# ============================================================

@router.post(
    "/regression-diagnostics/{dataset_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def regression_diagnostics_analysis(
    dataset_id: str,
    response_variable: str,
    predictor_variables: str,
    alpha: float = 0.05,
    current_user=Depends(get_current_user),
):

    # ---------------------------------------------------------
    # Validate dataset ID
    # ---------------------------------------------------------

    try:
        dataset_object_id = ObjectId(dataset_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID.",
        )

    # ---------------------------------------------------------
    # Validate alpha
    # ---------------------------------------------------------

    if not 0 < alpha < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alpha must be between 0 and 1.",
        )

    # ---------------------------------------------------------
    # Find dataset
    # ---------------------------------------------------------

    dataset = datasets_collection.find_one(
        {"_id": dataset_object_id}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    # ---------------------------------------------------------
    # Verify ownership
    # ---------------------------------------------------------

    dataset_user_id = str(
        dataset.get("user_id")
    )

    current_user_id = str(
        current_user["_id"]
    )

    if dataset_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to "
                "analyze this dataset."
            ),
        )

    # ---------------------------------------------------------
    # Get stored filename
    # ---------------------------------------------------------

    filename = dataset.get("filename")

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file information is missing.",
        )

    # ---------------------------------------------------------
    # Load dataset
    # ---------------------------------------------------------

    try:
        dataframe = load_dataset(filename)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Dataset file could not be found "
                "in storage."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to read dataset: {str(exc)}",
        )

    # ---------------------------------------------------------
    # Parse predictor variables
    # ---------------------------------------------------------

    predictor_variable_list = [
        variable.strip()
        for variable in predictor_variables.split(",")
        if variable.strip()
    ]

    if not predictor_variable_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "At least one predictor variable "
                "is required."
            ),
        )

    # ---------------------------------------------------------
    # Validate variables
    # ---------------------------------------------------------

    if response_variable in predictor_variable_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The response variable cannot also "
                "be a predictor variable."
            ),
        )

    variables_to_check = (
        predictor_variable_list
        + [response_variable]
    )

    missing_variables = [
        variable
        for variable in variables_to_check
        if variable not in dataframe.columns
    ]

    if missing_variables:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The following variables were not "
                "found in the dataset: "
                f"{missing_variables}"
            ),
        )

    # ---------------------------------------------------------
    # Run regression diagnostics
    # ---------------------------------------------------------

    try:
        results = analyze_regression_diagnostics(
            dataframe=dataframe,
            response_variable=response_variable,
            predictor_variables=predictor_variable_list,
            alpha=alpha,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Regression diagnostics failed: "
                f"{str(exc)}"
            ),
        )

    # ---------------------------------------------------------
    # Store diagnostics
    # ---------------------------------------------------------

    analysis_document = create_analysis_document(
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="regression_diagnostics",
        results=results,
    )

    result = analyses_collection.insert_one(
        analysis_document
    )

    # ---------------------------------------------------------
    # Return response
    # ---------------------------------------------------------

    return AnalysisResponse(
        id=str(result.inserted_id),
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="regression_diagnostics",
        results=results,
        created_at=analysis_document[
            "created_at"
        ].isoformat(),
    )


# ============================================================
# Hypothesis Testing
# ============================================================

@router.post(
    "/hypothesis/{dataset_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def hypothesis_test(
    dataset_id: str,
    test_type: str,
    current_user=Depends(get_current_user),
    variable: str | None = None,
    variable2: str | None = None,
    group_variable: str | None = None,
    group1: str | None = None,
    group2: str | None = None,
    population_mean: float | None = None,
    alpha: float = 0.05,
):

    try:
        dataset_object_id = ObjectId(dataset_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID.",
        )

    if not 0 < alpha < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alpha must be between 0 and 1.",
        )

    dataset = datasets_collection.find_one(
        {"_id": dataset_object_id}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    dataset_user_id = str(
        dataset.get("user_id")
    )

    current_user_id = str(
        current_user["_id"]
    )

    if dataset_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to "
                "analyze this dataset."
            ),
        )

    filename = dataset.get("filename")

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file information is missing.",
        )

    try:
        dataframe = load_dataset(filename)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Dataset file could not be found "
                "in storage."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to read dataset: {str(exc)}",
        )

    try:

        if test_type == "one_sample_t":

            if variable is None or population_mean is None:
                raise ValueError(
                    "variable and population_mean are required."
                )

            results = one_sample_t_test(
                dataframe,
                variable,
                population_mean,
                alpha,
            )

        elif test_type == "independent_t":

            if not all(
                [
                    variable,
                    group_variable,
                    group1,
                    group2,
                ]
            ):
                raise ValueError(
                    "variable, group_variable, group1 "
                    "and group2 are required."
                )

            results = independent_t_test(
                dataframe,
                variable,
                group_variable,
                group1,
                group2,
                alpha,
            )

        elif test_type == "paired_t":

            if not variable or not variable2:
                raise ValueError(
                    "variable and variable2 are required."
                )

            results = paired_t_test(
                dataframe,
                variable,
                variable2,
                alpha,
            )

        elif test_type == "anova":

            if not variable or not group_variable:
                raise ValueError(
                    "variable and group_variable are required."
                )

            results = one_way_anova(
                dataframe=dataframe,
                value_variable=variable,
                group_variable=group_variable,
                alpha=alpha,
            )

        elif test_type == "chi_square":

            if not variable or not variable2:
                raise ValueError(
                    "variable and variable2 are required."
                )

            results = chi_square_independence(
                dataframe,
                variable,
                variable2,
                alpha,
            )

        elif test_type == "shapiro":

            if not variable:
                raise ValueError(
                    "variable is required."
                )

            results = shapiro_normality_test(
                dataframe,
                variable,
                alpha,
            )

        elif test_type == "mann_whitney":

            if not all(
                [
                    variable,
                    group_variable,
                    group1,
                    group2,
                ]
            ):
                raise ValueError(
                    "variable, group_variable, group1 "
                    "and group2 are required."
                )

            results = mann_whitney_test(
                dataframe,
                variable,
                group_variable,
                group1,
                group2,
                alpha,
            )

        elif test_type == "wilcoxon":

            if not variable or not variable2:
                raise ValueError(
                    "variable and variable2 are required."
                )

            results = wilcoxon_test(
                dataframe,
                variable,
                variable2,
                alpha,
            )

        elif test_type == "kruskal_wallis":

            if not variable or not group_variable:
                raise ValueError(
                    "variable and group_variable are required."
                )

            results = kruskal_wallis_test(
                dataframe,
                variable,
                group_variable,
                alpha,
            )

        else:
            raise ValueError(
                "Unsupported hypothesis test. "
                "Available tests: "
                "one_sample_t, independent_t, paired_t, "
                "anova, chi_square, shapiro, "
                "mann_whitney, wilcoxon, "
                "kruskal_wallis."
            )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Hypothesis testing failed: {str(exc)}"
            ),
        )

    analysis_document = create_analysis_document(
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="hypothesis_testing",
        results=results,
    )

    result = analyses_collection.insert_one(
        analysis_document
    )

    return AnalysisResponse(
        id=str(result.inserted_id),
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="hypothesis_testing",
        results=results,
        created_at=analysis_document[
            "created_at"
        ].isoformat(),
    )


# ============================================================
# One-Way ANOVA
# ============================================================

@router.post(
    "/anova/{dataset_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def anova_analysis(
    dataset_id: str,
    value_variable: str,
    group_variable: str,
    alpha: float = 0.05,
    current_user=Depends(get_current_user),
):

    try:
        dataset_object_id = ObjectId(dataset_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID.",
        )

    dataset = datasets_collection.find_one(
        {"_id": dataset_object_id}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    dataset_user_id = str(
        dataset.get("user_id")
    )

    current_user_id = str(
        current_user["_id"]
    )

    if dataset_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to analyze this dataset."
            ),
        )

    filename = dataset.get("filename")

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file information is missing.",
        )

    try:
        dataframe = load_dataset(filename)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Dataset file could not be found "
                "in storage."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Unable to read dataset: {str(exc)}"
            ),
        )

    if not 0 < alpha < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Alpha must be greater than 0 "
                "and less than 1."
            ),
        )

    try:
        anova_result = one_way_anova(
            dataframe=dataframe,
            value_variable=value_variable,
            group_variable=group_variable,
            alpha=alpha,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"ANOVA analysis failed: {str(exc)}"
            ),
        )

    try:
        levene_result = levene_test(
            dataframe=dataframe,
            value_variable=value_variable,
            group_variable=group_variable,
            alpha=alpha,
        )

    except Exception as exc:
        levene_result = {
            "error": (
                "Levene's test could not be performed: "
                f"{str(exc)}"
            )
        }

    tukey_result = None

    if anova_result["p_value"] < alpha:

        try:
            tukey_result = tukey_hsd(
                dataframe=dataframe,
                value_variable=value_variable,
                group_variable=group_variable,
                alpha=alpha,
            )

        except Exception as exc:
            tukey_result = {
                "error": (
                    "Tukey HSD could not be performed: "
                    f"{str(exc)}"
                )
            }

    results = {
        "anova": anova_result,
        "assumption_tests": {
            "levene": levene_result,
        },
        "post_hoc": {
            "tukey_hsd": tukey_result,
        },
    }

    analysis_document = create_analysis_document(
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="anova",
        results=results,
    )

    result = analyses_collection.insert_one(
        analysis_document
    )

    return AnalysisResponse(
        id=str(result.inserted_id),
        dataset_id=dataset_id,
        user_id=current_user_id,
        analysis_type="anova",
        results=results,
        created_at=analysis_document[
            "created_at"
        ].isoformat(),
    )


# ============================================================
# Get Analysis Result
# IMPORTANT:
# Keep this generic route AFTER all specific analysis routes.
# ============================================================

@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
)
def get_analysis(
    analysis_id: str,
    current_user=Depends(get_current_user),
):

    try:
        analysis_object_id = ObjectId(
            analysis_id
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID.",
        )

    analysis = analyses_collection.find_one(
        {
            "_id": analysis_object_id,
            "user_id": str(
                current_user["_id"]
            ),
        }
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result not found.",
        )

    return AnalysisResponse(
        id=str(analysis["_id"]),
        dataset_id=analysis["dataset_id"],
        user_id=analysis["user_id"],
        analysis_type=analysis["analysis_type"],
        results=analysis["results"],
        created_at=analysis[
            "created_at"
        ].isoformat(),
    )
