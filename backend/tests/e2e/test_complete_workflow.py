"""End-to-end tests for complete user journeys."""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json
from datetime import datetime

from src.main import app


class TestCompleteWorkflow:
    """End-to-end tests for complete user workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    @patch('src.api.search.get_github_service')
    @patch('src.api.indexing.get_indexer_service')
    @patch('src.api.chat.get_rag_service')
    def test_complete_user_journey(self, mock_get_rag, mock_get_indexer, mock_get_github):
        """Test complete user journey from search to chat."""
        # Setup GitHub service mock
        mock_github_service = Mock()
        mock_github_service.search_repositories.return_value = Mock(
            repositories=[Mock(
                id="12345",
                name="test-repo",
                full_name="owner/test-repo",
                description="A test repository",
                url="https://github.com/owner/test-repo",
                html_url="https://github.com/owner/test-repo",
                stars=100,
                stargazers_count=100,
                forks=25,
                language="Python",
                topics=["python", "test"],
                owner="owner",
                default_branch="main",
                size=1024,
                updated_at="2023-01-01T00:00:00Z",
                created_at="2022-01-01T00:00:00Z"
            )],
            total_count=1,
            page=1
        )
        mock_github_service.validate_repository_url.return_value = Mock(
            valid=True,
            message="Repository is valid and accessible",
            repository_info=Mock(
                id="12345",
                name="test-repo",
                full_name="owner/test-repo",
                description="A test repository",
                url="https://github.com/owner/test-repo",
                html_url="https://github.com/owner/test-repo",
                stars=100,
                stargazers_count=100,
                forks=25,
                language="Python",
                topics=["python", "test"],
                owner="owner",
                default_branch="main",
                size=1024,
                updated_at="2023-01-01T00:00:00Z",
                created_at="2022-01-01T00:00:00Z"
            )
        )
        mock_github_service.get_repository.return_value = Mock(
            id="12345",
            name="test-repo",
            full_name="owner/test-repo",
            description="A test repository",
            url="https://github.com/owner/test-repo",
            html_url="https://github.com/owner/test-repo",
            stars=100,
            stargazers_count=100,
            forks=25,
            language="Python",
            topics=["python", "test"],
            owner="owner",
            default_branch="main",
            size=1024,
            updated_at="2023-01-01T00:00:00Z",
            created_at="2022-01-01T00:00:00Z",
            clone_url="https://github.com/owner/test-repo.git",
            ssh_url="git@github.com:owner/test-repo.git",
            open_issues=5,
            watchers=50,
            license="MIT",
            is_private=False,
            is_fork=False,
            has_wiki=True,
            has_issues=True
        )
        mock_get_github.return_value = mock_github_service

        # Setup indexer service mock
        mock_indexer_service = Mock()
        mock_indexer_service.start_indexing.return_value = Mock(
            task_id="task-123",
            status="pending",
            message="Indexing task created and queued",
            repository_url="https://github.com/owner/test-repo",
            estimated_time=300,
            created_at=datetime.utcnow()
        )
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
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error=None,
            result=Mock(
                files_indexed=100,
                total_size=1024000,
                processing_time=300.0
            )
        )
        mock_indexer_service.get_index_stats.return_value = Mock(
            is_indexed=True,
            repository_name="owner/test-repo",
            file_count=100,
            total_size=1024000,
            vector_count=1000,
            last_updated=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        mock_get_indexer.return_value = mock_indexer_service

        # Setup RAG service mock
        mock_rag_service = Mock()
        mock_rag_service.query.return_value = Mock(
            response="This is a Python repository with test code. The main functionality includes data processing and analysis functions.",
            sources=[
                Mock(
                    file_path="src/main.py",
                    start_line=10,
                    end_line=25,
                    content="def process_data(data):\n    return data.upper()",
                    score=0.95
                )
            ],
            conversation_id="conv-123",
            confidence=0.85,
            processing_time=1.5,
            model_used="codellama-7b"
        )
        mock_rag_service.get_chat_history.return_value = Mock(
            conversation_id="conv-123",
            messages=[
                Mock(
                    role="user",
                    content="What is this repository about?",
                    timestamp=datetime.utcnow(),
                    sources=None
                ),
                Mock(
                    role="assistant",
                    content="This is a Python repository with test code. The main functionality includes data processing and analysis functions.",
                    timestamp=datetime.utcnow(),
                    sources=[
                        Mock(
                            file_path="src/main.py",
                            start_line=10,
                            end_line=25,
                            content="def process_data(data):\n    return data.upper()",
                            score=0.95
                        )
                    ]
                )
            ],
            total_messages=2,
            created_at=datetime.utcnow()
        )
        mock_rag_service.get_chat_context.return_value = Mock(
            conversation_id="conv-123",
            message_count=2,
            user_message_count=1,
            assistant_message_count=1,
            last_query="What is this repository about?",
            last_response="This is a Python repository with test code. The main functionality includes data processing and analysis functions.",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        mock_get_rag.return_value = mock_rag_service

        # Step 1: Health check
        health_response = self.client.get("/api/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"

        # Step 2: Search for repositories
        search_response = self.client.post(
            "/api/search/repositories",
            json={"query": "python test repository", "limit": 10}
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert len(search_data["repositories"]) == 1
        assert search_data["repositories"][0]["name"] == "test-repo"

        # Step 3: Validate repository URL
        validate_response = self.client.post(
            "/api/validate/url",
            json={"url": "https://github.com/owner/test-repo"}
        )
        assert validate_response.status_code == 200
        validate_data = validate_response.json()
        assert validate_data["is_valid"] is True

        # Step 4: Get repository details
        repo_response = self.client.get("/api/repositories/owner/test-repo")
        assert repo_response.status_code == 200
        repo_data = repo_response.json()
        assert repo_data["name"] == "test-repo"
        assert repo_data["clone_url"] == "https://github.com/owner/test-repo.git"

        # Step 5: Start indexing
        index_response = self.client.post(
            "/api/index/start",
            json={
                "repository_url": "https://github.com/owner/test-repo",
                "branch": "main"
            }
        )
        assert index_response.status_code == 200
        index_data = index_response.json()
        assert index_data["task_id"] == "task-123"
        assert index_data["status"] == "pending"

        # Step 6: Check indexing status
        status_response = self.client.get("/api/index/status/task-123")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["task_id"] == "task-123"
        assert status_data["status"] == "completed"
        assert status_data["percentage"] == 100.0

        # Step 7: Get index stats
        stats_response = self.client.get("/api/index/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["is_indexed"] is True
        assert stats_data["repository_name"] == "owner/test-repo"
        assert stats_data["file_count"] == 100

        # Step 8: Start chat conversation
        chat_response = self.client.post(
            "/api/chat/query",
            json={"query": "What is this repository about?"}
        )
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert "Python repository" in chat_data["response"]
        assert chat_data["conversation_id"] == "conv-123"
        assert len(chat_data["sources"]) == 1

        # Step 9: Get chat history
        history_response = self.client.get("/api/chat/history?conversation_id=conv-123")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data["messages"]) == 2
        assert history_data["conversation_id"] == "conv-123"

        # Step 10: Get chat context
        context_response = self.client.get("/api/chat/context?conversation_id=conv-123")
        assert context_response.status_code == 200
        context_data = context_response.json()
        assert context_data["message_count"] == 2
        assert context_data["last_query"] == "What is this repository about?"

        # Step 11: Continue conversation
        follow_up_response = self.client.post(
            "/api/chat/query",
            json={
                "query": "Can you show me the main function?",
                "conversation_id": "conv-123"
            }
        )
        assert follow_up_response.status_code == 200

        # Step 12: Clear chat history
        clear_response = self.client.delete("/api/chat/history?conversation_id=conv-123")
        assert clear_response.status_code == 200
        clear_data = clear_response.json()
        assert clear_data["success"] is True

        # Step 13: Clear index
        clear_index_response = self.client.delete("/api/index/current")
        assert clear_index_response.status_code == 200
        clear_index_data = clear_index_response.json()
        assert clear_index_data["success"] is True

    @patch('src.api.search.get_github_service')
    @patch('src.api.indexing.get_indexer_service')
    def test_websocket_workflow(self, mock_get_indexer, mock_get_github):
        """Test WebSocket workflow for real-time updates."""
        # Setup mocks
        mock_github_service = Mock()
        mock_github_service.search_repositories.return_value = Mock(
            repositories=[Mock(
                id="12345",
                name="test-repo",
                full_name="owner/test-repo",
                description="A test repository",
                url="https://github.com/owner/test-repo",
                html_url="https://github.com/owner/test-repo",
                stars=100,
                stargazers_count=100,
                forks=25,
                language="Python",
                topics=["python", "test"],
                owner="owner",
                default_branch="main",
                size=1024,
                updated_at="2023-01-01T00:00:00Z",
                created_at="2022-01-01T00:00:00Z"
            )],
            total_count=1,
            page=1
        )
        mock_get_github.return_value = mock_github_service

        mock_indexer_service = Mock()
        mock_indexer_service.start_indexing.return_value = Mock(
            task_id="task-123",
            status="pending",
            message="Indexing task created and queued",
            repository_url="https://github.com/owner/test-repo",
            estimated_time=300,
            created_at=datetime.utcnow()
        )
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
            started_at=datetime.utcnow(),
            completed_at=None,
            error=None,
            result=None
        )
        mock_get_indexer.return_value = mock_indexer_service

        # Test WebSocket connection
        with self.client.websocket_connect("/ws/task-123") as websocket:
            # Send status check
            websocket.send_text(json.dumps({"type": "get_status"}))
            
            # Should receive status update
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "status_update"
            assert message["task_id"] == "task-123"
            assert message["status"] == "running"
            assert message["percentage"] == 50.0

            # Send ping
            websocket.send_text(json.dumps({"type": "ping"}))
            
            # Should receive pong
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "pong"

    @patch('src.api.search.get_github_service')
    @patch('src.api.indexing.get_indexer_service')
    @patch('src.api.chat.get_rag_service')
    def test_error_recovery_workflow(self, mock_get_rag, mock_get_indexer, mock_get_github):
        """Test error recovery throughout the workflow."""
        # Setup GitHub service to fail first, then succeed
        mock_github_service = Mock()
        mock_github_service.search_repositories.side_effect = [
            Exception("Network error"),
            Mock(
                repositories=[Mock(
                    id="12345",
                    name="test-repo",
                    full_name="owner/test-repo",
                    description="A test repository",
                    url="https://github.com/owner/test-repo",
                    html_url="https://github.com/owner/test-repo",
                    stars=100,
                    stargazers_count=100,
                    forks=25,
                    language="Python",
                    topics=["python", "test"],
                    owner="owner",
                    default_branch="main",
                    size=1024,
                    updated_at="2023-01-01T00:00:00Z",
                    created_at="2022-01-01T00:00:00Z"
                )],
                total_count=1,
                page=1
            )
        ]
        mock_get_github.return_value = mock_github_service

        # First search attempt should fail
        search_response = self.client.post(
            "/api/search/repositories",
            json={"query": "python test", "limit": 10}
        )
        assert search_response.status_code == 500

        # Second search attempt should succeed
        search_response = self.client.post(
            "/api/search/repositories",
            json={"query": "python test", "limit": 10}
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert len(search_data["repositories"]) == 1

    @patch('src.api.search.get_github_service')
    @patch('src.api.indexing.get_indexer_service')
    def test_large_repository_workflow(self, mock_get_indexer, mock_get_github):
        """Test workflow with large repository."""
        # Setup mocks for large repository
        mock_github_service = Mock()
        mock_github_service.search_repositories.return_value = Mock(
            repositories=[Mock(
                id="12345",
                name="large-repo",
                full_name="owner/large-repo",
                description="A large repository",
                url="https://github.com/owner/large-repo",
                html_url="https://github.com/owner/large-repo",
                stars=10000,
                stargazers_count=10000,
                forks=2500,
                language="Python",
                topics=["python", "large", "data"],
                owner="owner",
                default_branch="main",
                size=500000,  # Large size
                updated_at="2023-01-01T00:00:00Z",
                created_at="2022-01-01T00:00:00Z"
            )],
            total_count=1,
            page=1
        )
        mock_get_github.return_value = mock_github_service

        mock_indexer_service = Mock()
        mock_indexer_service.start_indexing.return_value = Mock(
            task_id="task-456",
            status="pending",
            message="Indexing task created and queued",
            repository_url="https://github.com/owner/large-repo",
            estimated_time=1800,  # 30 minutes for large repo
            created_at=datetime.utcnow()
        )
        mock_indexer_service.get_indexing_status.return_value = Mock(
            task_id="task-456",
            status="running",
            message="Indexing in progress",
            progress=Mock(
                files_processed=5000,
                total_files=10000,
                percentage=50.0
            ),
            percentage=50.0,
            repository_url="https://github.com/owner/large-repo",
            started_at=datetime.utcnow(),
            completed_at=None,
            error=None,
            result=None
        )
        mock_indexer_service.get_index_stats.return_value = Mock(
            is_indexed=True,
            repository_name="owner/large-repo",
            file_count=10000,
            total_size=50000000,  # 50MB
            vector_count=100000,
            last_updated=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        mock_get_indexer.return_value = mock_indexer_service

        # Test search for large repository
        search_response = self.client.post(
            "/api/search/repositories",
            json={"query": "large python data", "limit": 10}
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["repositories"][0]["name"] == "large-repo"
        assert search_data["repositories"][0]["size"] == 500000

        # Test indexing large repository
        index_response = self.client.post(
            "/api/index/start",
            json={"repository_url": "https://github.com/owner/large-repo"}
        )
        assert index_response.status_code == 200
        index_data = index_response.json()
        assert index_data["estimated_time"] == 1800

        # Test status check for large repository
        status_response = self.client.get("/api/index/status/task-456")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["progress"]["files_processed"] == 5000
        assert status_data["progress"]["total_files"] == 10000

        # Test stats for large repository
        stats_response = self.client.get("/api/index/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["file_count"] == 10000
        assert stats_data["total_size"] == 50000000
        assert stats_data["vector_count"] == 100000

    def test_concurrent_requests(self):
        """Test concurrent API requests."""
        import threading
        import time

        results = []

        def make_health_request():
            response = self.client.get("/api/health")
            results.append(response.status_code)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_health_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10

    def test_api_rate_limiting(self):
        """Test API rate limiting behavior."""
        # Make many requests quickly
        responses = []
        for i in range(100):
            response = self.client.get("/api/health")
            responses.append(response.status_code)

        # All should succeed (no rate limiting implemented yet)
        assert all(status == 200 for status in responses)

    def test_malformed_requests(self):
        """Test handling of malformed requests."""
        # Test malformed JSON
        response = self.client.post(
            "/api/search/repositories",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Test missing required fields
        response = self.client.post(
            "/api/search/repositories",
            json={"limit": 10}  # Missing query
        )
        assert response.status_code == 422

        # Test invalid field types
        response = self.client.post(
            "/api/search/repositories",
            json={"query": 123, "limit": "invalid"}  # Wrong types
        )
        assert response.status_code == 422

    def test_cors_headers(self):
        """Test CORS headers on all endpoints."""
        endpoints = [
            ("GET", "/api/health"),
            ("POST", "/api/search/repositories"),
            ("POST", "/api/validate/url"),
            ("GET", "/api/repositories/owner/test-repo"),
            ("POST", "/api/index/start"),
            ("GET", "/api/index/status/task-123"),
            ("GET", "/api/index/stats"),
            ("DELETE", "/api/index/current"),
            ("POST", "/api/chat/query"),
            ("GET", "/api/chat/history"),
            ("GET", "/api/chat/context"),
            ("DELETE", "/api/chat/history"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = self.client.get(endpoint)
            elif method == "POST":
                response = self.client.post(endpoint, json={})
            elif method == "DELETE":
                response = self.client.delete(endpoint)
            
            # Should have CORS headers
            assert "access-control-allow-origin" in response.headers

    def test_content_type_headers(self):
        """Test content type headers on all endpoints."""
        endpoints = [
            ("GET", "/api/health"),
            ("GET", "/api/index/stats"),
        ]

        for method, endpoint in endpoints:
            response = self.client.get(endpoint)
            assert response.headers["content-type"] == "application/json"

    def test_error_response_format(self):
        """Test error response format consistency."""
        # Test 404 error
        response = self.client.get("/api/repositories/nonexistent/repo")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

        # Test 422 error
        response = self.client.post("/api/search/repositories", json={})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

        # Test 500 error (with mocked service error)
        with patch('src.api.search.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_repositories.side_effect = Exception("Service error")
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/search/repositories",
                json={"query": "test", "limit": 10}
            )
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)
