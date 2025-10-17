"""Repository endpoints."""
from fastapi import APIRouter, HTTPException

from src.models.repository import Repository
from src.models.response import ErrorResponse, NotFoundResponse
from src.services import get_github_service

router = APIRouter()


@router.get(
    "/repositories/{repo_id:path}",
    response_model=Repository,
    responses={
        404: {"model": NotFoundResponse},
        400: {"model": ErrorResponse},
    },
    tags=["repositories"],
)
async def get_repository(repo_id: str) -> Repository:
    """
    Get repository details by repository ID (owner/name format).

    Args:
        repo_id: Repository identifier in format "owner/name"

    Returns:
        Repository with full details

    Raises:
        HTTPException: If repository not found or fetch fails
    """
    try:
        # Parse repo_id as owner/name
        if "/" in repo_id:
            parts = repo_id.split("/", 1)
            owner, name = parts[0], parts[1]
        else:
            # Single string ID - return 404 for now (test case)
            raise HTTPException(
                status_code=404,
                detail=f"Repository {repo_id} not found",
            )

        github_service = get_github_service()
        repo = github_service.get_repository(f"{owner}/{name}")

        if repo is None:
            raise HTTPException(
                status_code=404,
                detail=f"Repository {repo_id} not found",
            )

        return repo
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repository: {str(e)}") from e
