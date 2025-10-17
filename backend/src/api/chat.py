"""Chat and query endpoints."""
from fastapi import APIRouter, HTTPException, Query

from src.models.query import (
    ChatContextResponse,
    ChatHistoryRequest,
    ChatHistoryResponse,
    QueryRequest,
    QueryResponse,
)
from src.models.response import ErrorResponse, NotFoundResponse
from src.services import get_rag_service

router = APIRouter()


@router.post(
    "/chat/query",
    response_model=QueryResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["chat"],
)
async def chat_query(request: QueryRequest) -> QueryResponse:
    """
    Process a chat query using RAG pipeline.

    Args:
        request: Query request with question and optional context

    Returns:
        QueryResponse with answer and sources

    Raises:
        HTTPException: If query processing fails
    """
    try:
        rag_service = get_rag_service()
        return rag_service.query(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}") from e


@router.get(
    "/chat/history",
    response_model=ChatHistoryResponse,
    responses={404: {"model": NotFoundResponse}},
    tags=["chat"],
)
async def get_chat_history(
    conversation_id: str = Query(..., description="Conversation identifier"),
    limit: int = Query(50, description="Maximum number of messages to return"),
) -> ChatHistoryResponse:
    """
    Get conversation history.

    Args:
        conversation_id: Conversation identifier
        limit: Maximum number of messages to return

    Returns:
        ChatHistoryResponse with message history

    Raises:
        HTTPException: If conversation not found
    """
    rag_service = get_rag_service()
    request = ChatHistoryRequest(conversation_id=conversation_id, limit=limit)
    history = rag_service.get_chat_history(request)

    if history is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )

    return history


@router.get(
    "/chat/context",
    response_model=ChatContextResponse,
    responses={404: {"model": NotFoundResponse}},
    tags=["chat"],
)
async def get_chat_context(
    conversation_id: str = Query(..., description="Conversation identifier"),
) -> ChatContextResponse:
    """
    Get conversation context summary.

    Args:
        conversation_id: Conversation identifier

    Returns:
        ChatContextResponse with conversation summary

    Raises:
        HTTPException: If conversation not found
    """
    rag_service = get_rag_service()
    context = rag_service.get_chat_context(conversation_id)

    if context is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )

    return context


@router.delete(
    "/chat/history",
    responses={400: {"model": ErrorResponse}},
    tags=["chat"],
)
async def clear_chat_history(
    conversation_id: str = Query(
        None, description="Specific conversation to clear, or None for all"
    ),
) -> dict:
    """
    Clear conversation history.

    Args:
        conversation_id: Optional specific conversation to clear

    Returns:
        Operation result

    Raises:
        HTTPException: If clear operation fails
    """
    try:
        rag_service = get_rag_service()
        result = rag_service.clear_history(conversation_id)

        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to clear history"),
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}") from e
