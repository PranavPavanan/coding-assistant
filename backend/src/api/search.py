"""Repository search and validation endpoints."""
from fastapi import APIRouter, HTTPException

from src.models.repository import (
    RepositorySearchRequest,
    RepositorySearchResponse,
    RepositoryValidationRequest,
    RepositoryValidationResponse,
)
from src.models.response import ErrorResponse
from src.services import get_github_service

router = APIRouter()


@router.post(
    "/search/repositories",
    response_model=RepositorySearchResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["search"],
)
async def search_repositories(
    request: RepositorySearchRequest,
) -> RepositorySearchResponse:
    """
    Search for GitHub repositories.

    Args:
        request: Search request with query and filters

    Returns:
        RepositorySearchResponse with matching repositories

    Raises:
        HTTPException: If search fails
    """
    try:
        github_service = get_github_service()
        return github_service.search_repositories(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e


@router.post(
    "/validate/url",
    response_model=RepositoryValidationResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["search"],
)
async def validate_repository_url(
    request: RepositoryValidationRequest,
) -> RepositoryValidationResponse:
    """
    Validate a GitHub repository URL.

    Args:
        request: Validation request with repository URL

    Returns:
        RepositoryValidationResponse with validation result

    Raises:
        HTTPException: If validation fails
    """
    try:
        github_service = get_github_service()
        return github_service.validate_repository_url(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}") from e
