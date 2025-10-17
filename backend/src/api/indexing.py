"""Repository indexing endpoints."""
from fastapi import APIRouter, HTTPException

from src.models.index import (
    IndexClearResponse,
    IndexStartRequest,
    IndexStartResponse,
    IndexStats,
    IndexStatusResponse,
)
from src.models.response import ErrorResponse, NotFoundResponse
from src.services import get_indexer_service

router = APIRouter()


@router.post(
    "/index/start",
    response_model=IndexStartResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["indexing"],
)
async def start_indexing(request: IndexStartRequest) -> IndexStartResponse:
    """
    Start indexing a repository.

    Args:
        request: Index start request with repository URL

    Returns:
        IndexStartResponse with task ID

    Raises:
        HTTPException: If indexing start fails
    """
    try:
        indexer_service = get_indexer_service()
        return indexer_service.start_indexing(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start indexing: {str(e)}") from e


@router.get(
    "/index/status/{task_id}",
    response_model=IndexStatusResponse,
    responses={404: {"model": NotFoundResponse}},
    tags=["indexing"],
)
async def get_index_status(task_id: str) -> IndexStatusResponse:
    """
    Get indexing task status.

    Args:
        task_id: Task identifier

    Returns:
        IndexStatusResponse with current status

    Raises:
        HTTPException: If task not found
    """
    indexer_service = get_indexer_service()
    status = indexer_service.get_indexing_status(task_id)

    if status is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return status


@router.delete(
    "/index/current",
    response_model=IndexClearResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["indexing"],
)
async def clear_index() -> IndexClearResponse:
    """
    Clear the current index.

    Returns:
        IndexClearResponse with operation result

    Raises:
        HTTPException: If clear operation fails
    """
    try:
        indexer_service = get_indexer_service()
        result = indexer_service.clear_index()

        if not result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to clear index"),
            )

        return IndexClearResponse(
            success=True,
            message=result.get("message", "Index cleared successfully"),
            files_removed=result.get("files_removed", 0),
            space_freed=result.get("space_freed", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear index: {str(e)}") from e


@router.get(
    "/index/stats",
    response_model=IndexStats,
    tags=["indexing"],
)
async def get_index_stats() -> IndexStats:
    """
    Get current index statistics.

    Returns:
        IndexStats with current index information
    """
    indexer_service = get_indexer_service()
    return indexer_service.get_index_stats()
