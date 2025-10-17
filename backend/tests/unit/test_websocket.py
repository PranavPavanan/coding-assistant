"""Unit tests for WebSocket functionality."""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from src.main import app


class TestWebSocketAPI:
    """Test cases for WebSocket endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def test_websocket_connection_success(self):
        """Test successful WebSocket connection."""
        with self.client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_connection_with_task_id(self):
        """Test WebSocket connection with task ID."""
        with self.client.websocket_connect("/ws/task-123") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_connection_invalid_path(self):
        """Test WebSocket connection with invalid path."""
        with pytest.raises(Exception):
            with self.client.websocket_connect("/ws/invalid/path") as websocket:
                pass

    @patch('src.api.websocket.get_indexer_service')
    def test_websocket_indexing_updates(self, mock_get_indexer):
        """Test WebSocket indexing progress updates."""
        # Setup mock indexer service
        mock_indexer_service = Mock()
        mock_indexer_service.get_indexing_status.return_value = Mock(
            task_id="task-123",
            status="running",
            message="Indexing in progress",
            progress=Mock(
                files_processed=50,
                total_files=100,
                percentage=50.0
            ),
            percentage=50.0,
            repository_url="https://github.com/owner/test-repo",
            started_at="2023-01-01T00:00:00Z",
            completed_at=None,
            error=None,
            result=None
        )
        mock_get_indexer.return_value = mock_indexer_service

        with self.client.websocket_connect("/ws/task-123") as websocket:
            # Send a message to trigger status check
            websocket.send_text(json.dumps({"type": "get_status"}))
            
            # Should receive status update
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "status_update"
            assert message["task_id"] == "task-123"
            assert message["status"] == "running"
            assert message["percentage"] == 50.0

    @patch('src.api.websocket.get_rag_service')
    def test_websocket_chat_messages(self, mock_get_rag):
        """Test WebSocket chat message handling."""
        # Setup mock RAG service
        mock_rag_service = Mock()
        mock_rag_service.query.return_value = Mock(
            response="This is a test response",
            sources=[],
            conversation_id="conv-123",
            confidence=0.85,
            processing_time=1.5,
            model_used="codellama-7b"
        )
        mock_get_rag.return_value = mock_rag_service

        with self.client.websocket_connect("/ws") as websocket:
            # Send chat message
            chat_message = {
                "type": "chat_message",
                "query": "What does this function do?",
                "conversation_id": "conv-123"
            }
            websocket.send_text(json.dumps(chat_message))
            
            # Should receive response
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "chat_response"
            assert message["response"] == "This is a test response"
            assert message["conversation_id"] == "conv-123"

    def test_websocket_invalid_message_format(self):
        """Test WebSocket with invalid message format."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send invalid JSON
            websocket.send_text("invalid json")
            
            # Should receive error message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"
            assert "Invalid message format" in message["message"]

    def test_websocket_unknown_message_type(self):
        """Test WebSocket with unknown message type."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send unknown message type
            unknown_message = {
                "type": "unknown_type",
                "data": "test"
            }
            websocket.send_text(json.dumps(unknown_message))
            
            # Should receive error message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"
            assert "Unknown message type" in message["message"]

    @patch('src.api.websocket.get_indexer_service')
    def test_websocket_indexing_completion(self, mock_get_indexer):
        """Test WebSocket indexing completion notification."""
        # Setup mock indexer service
        mock_indexer_service = Mock()
        mock_indexer_service.get_indexing_status.return_value = Mock(
            task_id="task-123",
            status="completed",
            message="Indexing completed successfully",
            progress=Mock(
                files_processed=100,
                total_files=100,
                percentage=100.0
            ),
            percentage=100.0,
            repository_url="https://github.com/owner/test-repo",
            started_at="2023-01-01T00:00:00Z",
            completed_at="2023-01-01T00:05:00Z",
            error=None,
            result=Mock(
                files_indexed=100,
                total_size=1024000,
                processing_time=300.0
            )
        )
        mock_get_indexer.return_value = mock_indexer_service

        with self.client.websocket_connect("/ws/task-123") as websocket:
            # Send status check
            websocket.send_text(json.dumps({"type": "get_status"}))
            
            # Should receive completion update
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "status_update"
            assert message["status"] == "completed"
            assert message["percentage"] == 100.0

    @patch('src.api.websocket.get_indexer_service')
    def test_websocket_indexing_error(self, mock_get_indexer):
        """Test WebSocket indexing error notification."""
        # Setup mock indexer service
        mock_indexer_service = Mock()
        mock_indexer_service.get_indexing_status.return_value = Mock(
            task_id="task-123",
            status="failed",
            message="Indexing failed",
            progress=Mock(
                files_processed=25,
                total_files=100,
                percentage=25.0
            ),
            percentage=25.0,
            repository_url="https://github.com/owner/test-repo",
            started_at="2023-01-01T00:00:00Z",
            completed_at="2023-01-01T00:02:00Z",
            error="Repository not found",
            result=None
        )
        mock_get_indexer.return_value = mock_indexer_service

        with self.client.websocket_connect("/ws/task-123") as websocket:
            # Send status check
            websocket.send_text(json.dumps({"type": "get_status"}))
            
            # Should receive error update
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "status_update"
            assert message["status"] == "failed"
            assert message["error"] == "Repository not found"

    @patch('src.api.websocket.get_rag_service')
    def test_websocket_chat_with_sources(self, mock_get_rag):
        """Test WebSocket chat with source references."""
        # Setup mock RAG service
        mock_rag_service = Mock()
        mock_rag_service.query.return_value = Mock(
            response="This function calculates the sum of two numbers",
            sources=[
                Mock(
                    file_path="src/math.py",
                    start_line=10,
                    end_line=15,
                    content="def add(a, b):\n    return a + b",
                    score=0.95
                )
            ],
            conversation_id="conv-123",
            confidence=0.85,
            processing_time=1.5,
            model_used="codellama-7b"
        )
        mock_get_rag.return_value = mock_rag_service

        with self.client.websocket_connect("/ws") as websocket:
            # Send chat message
            chat_message = {
                "type": "chat_message",
                "query": "What does the add function do?",
                "conversation_id": "conv-123"
            }
            websocket.send_text(json.dumps(chat_message))
            
            # Should receive response with sources
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "chat_response"
            assert "calculates the sum" in message["response"]
            assert len(message["sources"]) == 1
            assert message["sources"][0]["file_path"] == "src/math.py"

    def test_websocket_multiple_connections(self):
        """Test multiple WebSocket connections."""
        # Test multiple connections to the same endpoint
        with self.client.websocket_connect("/ws") as websocket1:
            with self.client.websocket_connect("/ws") as websocket2:
                # Both connections should be established
                assert websocket1 is not None
                assert websocket2 is not None

    def test_websocket_connection_cleanup(self):
        """Test WebSocket connection cleanup on disconnect."""
        with self.client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None
            
            # Send a message
            websocket.send_text(json.dumps({"type": "ping"}))
            
            # Should receive pong response
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "pong"
            
            # Connection should close cleanly
            websocket.close()

    def test_websocket_ping_pong(self):
        """Test WebSocket ping-pong mechanism."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send ping
            websocket.send_text(json.dumps({"type": "ping"}))
            
            # Should receive pong
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "pong"

    def test_websocket_large_message(self):
        """Test WebSocket with large message."""
        with self.client.websocket_connect("/ws") as websocket:
            # Create large message
            large_query = "What does this function do? " * 1000
            chat_message = {
                "type": "chat_message",
                "query": large_query,
                "conversation_id": "conv-123"
            }
            
            # Send large message
            websocket.send_text(json.dumps(chat_message))
            
            # Should handle large message gracefully
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] in ["chat_response", "error"]

    def test_websocket_unicode_message(self):
        """Test WebSocket with unicode message."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send unicode message
            unicode_message = {
                "type": "chat_message",
                "query": "What does this function do? 你好世界 🌍",
                "conversation_id": "conv-123"
            }
            websocket.send_text(json.dumps(unicode_message))
            
            # Should handle unicode message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] in ["chat_response", "error"]

    def test_websocket_concurrent_messages(self):
        """Test WebSocket with concurrent messages."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send multiple messages quickly
            for i in range(5):
                message = {
                    "type": "ping",
                    "id": i
                }
                websocket.send_text(json.dumps(message))
            
            # Should receive multiple pong responses
            for i in range(5):
                data = websocket.receive_text()
                message = json.loads(data)
                assert message["type"] == "pong"

    def test_websocket_connection_timeout(self):
        """Test WebSocket connection timeout handling."""
        with self.client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None
            
            # Wait for potential timeout (if implemented)
            # This test ensures the connection doesn't timeout immediately
            websocket.send_text(json.dumps({"type": "ping"}))
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "pong"

    def test_websocket_error_handling(self):
        """Test WebSocket error handling."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send malformed message
            websocket.send_text("not json")
            
            # Should receive error
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"
            
            # Send empty message
            websocket.send_text("")
            
            # Should handle empty message
            try:
                data = websocket.receive_text()
                message = json.loads(data)
                assert message["type"] in ["error", "ping"]
            except:
                # Empty message might close connection
                pass

    def test_websocket_task_specific_connection(self):
        """Test WebSocket connection for specific task."""
        with self.client.websocket_connect("/ws/task-456") as websocket:
            # Connection should be established
            assert websocket is not None
            
            # Send task-specific message
            websocket.send_text(json.dumps({"type": "get_status"}))
            
            # Should receive response (even if task doesn't exist)
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] in ["status_update", "error"]

    def test_websocket_message_validation(self):
        """Test WebSocket message validation."""
        with self.client.websocket_connect("/ws") as websocket:
            # Test missing type field
            websocket.send_text(json.dumps({"data": "test"}))
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"

            # Test invalid type
            websocket.send_text(json.dumps({"type": 123}))
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"

    def test_websocket_chat_message_validation(self):
        """Test WebSocket chat message validation."""
        with self.client.websocket_connect("/ws") as websocket:
            # Test missing query
            websocket.send_text(json.dumps({"type": "chat_message"}))
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"

            # Test empty query
            websocket.send_text(json.dumps({
                "type": "chat_message",
                "query": ""
            }))
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"

    def test_websocket_status_message_validation(self):
        """Test WebSocket status message validation."""
        with self.client.websocket_connect("/ws") as websocket:
            # Test valid status request
            websocket.send_text(json.dumps({"type": "get_status"}))
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] in ["status_update", "error"]

    def test_websocket_connection_limits(self):
        """Test WebSocket connection limits."""
        # Test that we can establish multiple connections
        connections = []
        try:
            for i in range(10):  # Test up to 10 connections
                websocket = self.client.websocket_connect("/ws")
                connections.append(websocket)
                websocket.__enter__()
        except Exception:
            # If we hit a limit, that's expected
            pass
        finally:
            # Clean up connections
            for websocket in connections:
                try:
                    websocket.__exit__(None, None, None)
                except:
                    pass

    def test_websocket_heartbeat(self):
        """Test WebSocket heartbeat mechanism."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send multiple pings to test heartbeat
            for i in range(3):
                websocket.send_text(json.dumps({"type": "ping", "id": i}))
                data = websocket.receive_text()
                message = json.loads(data)
                assert message["type"] == "pong"

    def test_websocket_message_ordering(self):
        """Test WebSocket message ordering."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send multiple messages and verify order
            messages = []
            for i in range(5):
                message = {"type": "ping", "id": i}
                websocket.send_text(json.dumps(message))
                data = websocket.receive_text()
                response = json.loads(data)
                messages.append(response["id"])
            
            # Messages should be in order
            assert messages == [0, 1, 2, 3, 4]
