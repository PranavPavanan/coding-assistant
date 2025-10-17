"""Unit tests for chat API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime

from src.main import app


class TestChatAPI:
    """Test cases for chat endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    @patch('src.api.chat.get_rag_service')
    def test_chat_query_success(self, mock_get_service):
        """Test successful chat query."""
        # Setup mock
        mock_service = Mock()
        mock_service.query.return_value = Mock(
            response="This is a test response",
            sources=[],
            conversation_id="conv-123",
            confidence=0.85,
            processing_time=1.5,
            model_used="codellama-7b"
        )
        mock_get_service.return_value = mock_service

        # Execute
        response = self.client.post(
            "/api/chat/query",
            json={
                "query": "What does this function do?",
                "conversation_id": "conv-123"
            }
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "This is a test response"
        assert data["conversation_id"] == "conv-123"
        assert data["confidence"] == 0.85
        assert data["processing_time"] == 1.5
        assert data["model_used"] == "codellama-7b"

    def test_chat_query_missing_query(self):
        """Test chat query with missing query."""
        response = self.client.post(
            "/api/chat/query",
            json={"conversation_id": "conv-123"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_chat_query_empty_query(self):
        """Test chat query with empty query."""
        response = self.client.post(
            "/api/chat/query",
            json={"query": ""}
        )

        assert response.status_code == 422

    def test_chat_query_whitespace_query(self):
        """Test chat query with whitespace-only query."""
        response = self.client.post(
            "/api/chat/query",
            json={"query": "   "}
        )

        assert response.status_code == 422

    def test_chat_query_without_conversation_id(self):
        """Test chat query without conversation ID."""
        with patch('src.api.chat.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.query.return_value = Mock(
                response="This is a test response",
                sources=[],
                conversation_id="conv-456",
                confidence=0.85,
                processing_time=1.5,
                model_used="codellama-7b"
            )
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/chat/query",
                json={"query": "What does this function do?"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "conv-456"

    @patch('src.api.chat.get_rag_service')
    def test_chat_query_service_error(self, mock_get_service):
        """Test chat query with service error."""
        mock_service = Mock()
        mock_service.query.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        response = self.client.post(
            "/api/chat/query",
            json={"query": "What does this function do?"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "Query processing failed" in data["detail"]

    def test_chat_query_wrong_method(self):
        """Test chat query with wrong HTTP method."""
        response = self.client.get("/api/chat/query")
        assert response.status_code == 405

        response = self.client.put("/api/chat/query")
        assert response.status_code == 405

        response = self.client.delete("/api/chat/query")
        assert response.status_code == 405

    def test_chat_query_invalid_json(self):
        """Test chat query with invalid JSON."""
        response = self.client.post(
            "/api/chat/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @patch('src.api.chat.get_rag_service')
    def test_get_chat_history_success(self, mock_get_service):
        """Test successful chat history retrieval."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_chat_history.return_value = Mock(
            conversation_id="conv-123",
            messages=[
                Mock(
                    role="user",
                    content="What does this do?",
                    timestamp=datetime.utcnow(),
                    sources=None
                ),
                Mock(
                    role="assistant",
                    content="This does X",
                    timestamp=datetime.utcnow(),
                    sources=[]
                )
            ],
            total_messages=2,
            created_at=datetime.utcnow()
        )
        mock_get_service.return_value = mock_service

        # Execute
        response = self.client.get("/api/chat/history?conversation_id=conv-123")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "conv-123"
        assert len(data["messages"]) == 2
        assert data["total_messages"] == 2

    def test_get_chat_history_missing_conversation_id(self):
        """Test chat history retrieval with missing conversation ID."""
        response = self.client.get("/api/chat/history")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_chat_history_empty_conversation_id(self):
        """Test chat history retrieval with empty conversation ID."""
        response = self.client.get("/api/chat/history?conversation_id=")

        assert response.status_code == 422

    @patch('src.api.chat.get_rag_service')
    def test_get_chat_history_not_found(self, mock_get_service):
        """Test chat history retrieval for non-existent conversation."""
        mock_service = Mock()
        mock_service.get_chat_history.return_value = None
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/chat/history?conversation_id=nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch('src.api.chat.get_rag_service')
    def test_get_chat_history_service_error(self, mock_get_service):
        """Test chat history retrieval with service error."""
        mock_service = Mock()
        mock_service.get_chat_history.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/chat/history?conversation_id=conv-123")

        assert response.status_code == 500
        data = response.json()
        assert "History retrieval failed" in data["detail"]

    def test_get_chat_history_wrong_method(self):
        """Test chat history retrieval with wrong HTTP method."""
        response = self.client.post("/api/chat/history")
        assert response.status_code == 405

        response = self.client.put("/api/chat/history")
        assert response.status_code == 405

        response = self.client.delete("/api/chat/history")
        assert response.status_code == 405

    @patch('src.api.chat.get_rag_service')
    def test_get_chat_context_success(self, mock_get_service):
        """Test successful chat context retrieval."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_chat_context.return_value = Mock(
            conversation_id="conv-123",
            message_count=10,
            user_message_count=5,
            assistant_message_count=5,
            last_query="What does this do?",
            last_response="This does X",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        mock_get_service.return_value = mock_service

        # Execute
        response = self.client.get("/api/chat/context?conversation_id=conv-123")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "conv-123"
        assert data["message_count"] == 10
        assert data["user_message_count"] == 5
        assert data["assistant_message_count"] == 5
        assert data["last_query"] == "What does this do?"
        assert data["last_response"] == "This does X"

    def test_get_chat_context_missing_conversation_id(self):
        """Test chat context retrieval with missing conversation ID."""
        response = self.client.get("/api/chat/context")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_chat_context_empty_conversation_id(self):
        """Test chat context retrieval with empty conversation ID."""
        response = self.client.get("/api/chat/context?conversation_id=")

        assert response.status_code == 422

    @patch('src.api.chat.get_rag_service')
    def test_get_chat_context_not_found(self, mock_get_service):
        """Test chat context retrieval for non-existent conversation."""
        mock_service = Mock()
        mock_service.get_chat_context.return_value = None
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/chat/context?conversation_id=nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch('src.api.chat.get_rag_service')
    def test_get_chat_context_service_error(self, mock_get_service):
        """Test chat context retrieval with service error."""
        mock_service = Mock()
        mock_service.get_chat_context.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/chat/context?conversation_id=conv-123")

        assert response.status_code == 500
        data = response.json()
        assert "Context retrieval failed" in data["detail"]

    def test_get_chat_context_wrong_method(self):
        """Test chat context retrieval with wrong HTTP method."""
        response = self.client.post("/api/chat/context")
        assert response.status_code == 405

        response = self.client.put("/api/chat/context")
        assert response.status_code == 405

        response = self.client.delete("/api/chat/context")
        assert response.status_code == 405

    @patch('src.api.chat.get_rag_service')
    def test_clear_chat_history_success(self, mock_get_service):
        """Test successful chat history clearing."""
        # Setup mock
        mock_service = Mock()
        mock_service.clear_history.return_value = {
            "success": True,
            "message": "Conversation cleared"
        }
        mock_get_service.return_value = mock_service

        # Execute
        response = self.client.delete("/api/chat/history?conversation_id=conv-123")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cleared" in data["message"]

    @patch('src.api.chat.get_rag_service')
    def test_clear_chat_history_all(self, mock_get_service):
        """Test clearing all chat history."""
        mock_service = Mock()
        mock_service.clear_history.return_value = {
            "success": True,
            "message": "Cleared 5 conversations"
        }
        mock_get_service.return_value = mock_service

        response = self.client.delete("/api/chat/history")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Cleared" in data["message"]

    @patch('src.api.chat.get_rag_service')
    def test_clear_chat_history_failure(self, mock_get_service):
        """Test chat history clearing failure."""
        mock_service = Mock()
        mock_service.clear_history.return_value = {
            "success": False,
            "error": "Conversation not found"
        }
        mock_get_service.return_value = mock_service

        response = self.client.delete("/api/chat/history?conversation_id=nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]

    @patch('src.api.chat.get_rag_service')
    def test_clear_chat_history_service_error(self, mock_get_service):
        """Test chat history clearing with service error."""
        mock_service = Mock()
        mock_service.clear_history.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        response = self.client.delete("/api/chat/history?conversation_id=conv-123")

        assert response.status_code == 500
        data = response.json()
        assert "History clearing failed" in data["detail"]

    def test_clear_chat_history_wrong_method(self):
        """Test chat history clearing with wrong HTTP method."""
        response = self.client.get("/api/chat/history")
        assert response.status_code == 200  # GET is allowed for history retrieval

        response = self.client.post("/api/chat/history")
        assert response.status_code == 405

        response = self.client.put("/api/chat/history")
        assert response.status_code == 405

    def test_chat_query_content_type(self):
        """Test chat query content type."""
        with patch('src.api.chat.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.query.return_value = Mock(
                response="Test response",
                sources=[],
                conversation_id="conv-123",
                confidence=0.85,
                processing_time=1.5,
                model_used="codellama-7b"
            )
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/chat/query",
                json={"query": "Test question"}
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    def test_get_chat_history_content_type(self):
        """Test chat history retrieval content type."""
        with patch('src.api.chat.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_chat_history.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/chat/history?conversation_id=nonexistent")

            assert response.status_code == 404
            assert response.headers["content-type"] == "application/json"

    def test_get_chat_context_content_type(self):
        """Test chat context retrieval content type."""
        with patch('src.api.chat.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_chat_context.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/chat/context?conversation_id=nonexistent")

            assert response.status_code == 404
            assert response.headers["content-type"] == "application/json"

    def test_clear_chat_history_content_type(self):
        """Test chat history clearing content type."""
        with patch('src.api.chat.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.clear_history.return_value = {
                "success": True,
                "message": "Conversation cleared"
            }
            mock_get_service.return_value = mock_service

            response = self.client.delete("/api/chat/history?conversation_id=conv-123")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    def test_cors_headers(self):
        """Test CORS headers for all chat endpoints."""
        with patch('src.api.chat.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.query.return_value = Mock(
                response="Test response",
                sources=[],
                conversation_id="conv-123",
                confidence=0.85,
                processing_time=1.5,
                model_used="codellama-7b"
            )
            mock_service.get_chat_history.return_value = None
            mock_service.get_chat_context.return_value = None
            mock_service.clear_history.return_value = {
                "success": True,
                "message": "Conversation cleared"
            }
            mock_get_service.return_value = mock_service

            # Test all endpoints
            response1 = self.client.post(
                "/api/chat/query",
                json={"query": "Test question"}
            )
            response2 = self.client.get("/api/chat/history?conversation_id=conv-123")
            response3 = self.client.get("/api/chat/context?conversation_id=conv-123")
            response4 = self.client.delete("/api/chat/history?conversation_id=conv-123")

            # All should have CORS headers
            for response in [response1, response2, response3, response4]:
                assert "access-control-allow-origin" in response.headers

    def test_chat_query_large_query(self):
        """Test chat query with large query text."""
        with patch('src.api.chat.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.query.return_value = Mock(
                response="Test response",
                sources=[],
                conversation_id="conv-123",
                confidence=0.85,
                processing_time=1.5,
                model_used="codellama-7b"
            )
            mock_get_service.return_value = mock_service

            # Create a large query
            large_query = "What does this function do? " * 1000

            response = self.client.post(
                "/api/chat/query",
                json={"query": large_query}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Test response"

    def test_chat_query_special_characters(self):
        """Test chat query with special characters."""
        with patch('src.api.chat.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.query.return_value = Mock(
                response="Test response",
                sources=[],
                conversation_id="conv-123",
                confidence=0.85,
                processing_time=1.5,
                model_used="codellama-7b"
            )
            mock_get_service.return_value = mock_service

            special_query = "What does this function do? @#$%^&*()_+-=[]{}|;':\",./<>?"

            response = self.client.post(
                "/api/chat/query",
                json={"query": special_query}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Test response"

    def test_chat_query_unicode_characters(self):
        """Test chat query with unicode characters."""
        with patch('src.api.chat.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.query.return_value = Mock(
                response="Test response",
                sources=[],
                conversation_id="conv-123",
                confidence=0.85,
                processing_time=1.5,
                model_used="codellama-7b"
            )
            mock_get_service.return_value = mock_service

            unicode_query = "What does this function do? 你好世界 🌍"

            response = self.client.post(
                "/api/chat/query",
                json={"query": unicode_query}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Test response"
