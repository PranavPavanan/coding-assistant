"""Health check endpoint."""
from fastapi import APIRouter

from src.models.response import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    Check if the API is healthy.

    Returns:
        HealthResponse with status and message
    """
    return HealthResponse(
        status="healthy",
        message="Backend is running",
    )
