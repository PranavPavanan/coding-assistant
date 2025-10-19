"""Chat and query endpoints."""
from fastapi import APIRouter, HTTPException, Query

from src.models.query import (
    ChatContextResponse,
    ChatHistoryRequest,
    ChatHistoryResponse,
    QueryRequest,
    QueryResponse,
    SessionInfo,
    ConversationInfo,
    SessionClearRequest,
    SessionClearResponse,
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


@router.post(
    "/chat/session/clear",
    response_model=SessionClearResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["chat", "session"],
)
async def clear_session(request: SessionClearRequest) -> SessionClearResponse:
    """
    Clear session data and all associated conversations.

    Args:
        request: Session clear request with session_id and optional clear_all flag

    Returns:
        SessionClearResponse with operation result

    Raises:
        HTTPException: If clear operation fails
    """
    try:
        rag_service = get_rag_service()
        result = rag_service.clear_session(request)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.message,
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}") from e


@router.get(
    "/chat/session/{session_id}",
    response_model=SessionInfo,
    responses={404: {"model": NotFoundResponse}},
    tags=["chat", "session"],
)
async def get_session_info(session_id: str) -> SessionInfo:
    """
    Get session information.

    Args:
        session_id: Session identifier

    Returns:
        SessionInfo with session details

    Raises:
        HTTPException: If session not found
    """
    rag_service = get_rag_service()
    session_info = rag_service.get_session_info(session_id)

    if session_info is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found",
        )

    return session_info


@router.get(
    "/chat/session/{session_id}/conversations",
    response_model=list[ConversationInfo],
    tags=["chat", "session"],
)
async def list_conversations_in_session(session_id: str) -> list[ConversationInfo]:
    """
    List all conversations in a session.

    Args:
        session_id: Session identifier

    Returns:
        List of ConversationInfo objects
    """
    rag_service = get_rag_service()
    return rag_service.list_conversations_in_session(session_id)


@router.get(
    "/chat/conversation/{conversation_id}",
    response_model=ConversationInfo,
    responses={404: {"model": NotFoundResponse}},
    tags=["chat", "conversation"],
)
async def get_conversation_info(conversation_id: str) -> ConversationInfo:
    """
    Get conversation information.

    Args:
        conversation_id: Conversation identifier

    Returns:
        ConversationInfo with conversation details

    Raises:
        HTTPException: If conversation not found
    """
    rag_service = get_rag_service()
    conversation_info = rag_service.get_conversation_info(conversation_id)

    if conversation_info is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )

    return conversation_info


@router.get(
    "/chat/sessions",
    response_model=list[SessionInfo],
    tags=["chat", "session"],
)
async def list_sessions() -> list[SessionInfo]:
    """
    List all active sessions.

    Returns:
        List of SessionInfo objects
    """
    rag_service = get_rag_service()
    return rag_service.list_sessions()
