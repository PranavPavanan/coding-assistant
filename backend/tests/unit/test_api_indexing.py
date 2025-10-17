"""Unit tests for indexing API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime

from src.main import app


class TestIndexingAPI:
    """Test cases for indexing endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    @patch('src.api.indexing.get_indexer_service')
    def test_start_indexing_success(self, mock_get_service):
        """Test successful indexing start."""
        # Setup mock
        mock_service = Mock()
        mock_service.start_indexing.return_value = Mock(
            task_id="task-123",
            status="pending",
            message="Indexing task created and queued",
            repository_url="https://github.com/owner/test-repo",
            estimated_time=300,
            created_at=datetime.utcnow()
        )
        mock_get_service.return_value = mock_service

        # Execute
        response = self.client.post(
            "/api/index/start",
            json={
                "repository_url": "https://github.com/owner/test-repo",
                "branch": "main"
            }
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-123"
        assert data["status"] == "pending"
        assert data["repository_url"] == "https://github.com/owner/test-repo"
        assert data["estimated_time"] == 300

    def test_start_indexing_missing_repository_url(self):
        """Test indexing start with missing repository URL."""
        response = self.client.post(
            "/api/index/start",
            json={"branch": "main"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_indexing_invalid_repository_url(self):
        """Test indexing start with invalid repository URL."""
        response = self.client.post(
            "/api/index/start",
            json={"repository_url": "not-a-url"}
        )

        assert response.status_code == 422

    def test_start_indexing_empty_repository_url(self):
        """Test indexing start with empty repository URL."""
        response = self.client.post(
            "/api/index/start",
            json={"repository_url": ""}
        )

        assert response.status_code == 422

    def test_start_indexing_default_branch(self):
        """Test indexing start with default branch."""
        with patch('src.api.indexing.get_indexer_service') as mock_get_service:
            mock_service = Mock()
            mock_service.start_indexing.return_value = Mock(
                task_id="task-123",
                status="pending",
                message="Indexing task created and queued",
                repository_url="https://github.com/owner/test-repo",
                estimated_time=300,
                created_at=datetime.utcnow()
            )
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/index/start",
                json={"repository_url": "https://github.com/owner/test-repo"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "task-123"

    def test_start_indexing_invalid_branch(self):
        """Test indexing start with invalid branch."""
        response = self.client.post(
            "/api/index/start",
            json={
                "repository_url": "https://github.com/owner/test-repo",
                "branch": ""
            }
        )

        assert response.status_code == 422

    @patch('src.api.indexing.get_indexer_service')
    def test_start_indexing_service_error(self, mock_get_service):
        """Test indexing start with service error."""
        mock_service = Mock()
        mock_service.start_indexing.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        response = self.client.post(
            "/api/index/start",
            json={
                "repository_url": "https://github.com/owner/test-repo",
                "branch": "main"
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert "Failed to start indexing" in data["detail"]

    def test_start_indexing_wrong_method(self):
        """Test indexing start with wrong HTTP method."""
        response = self.client.get("/api/index/start")
        assert response.status_code == 405

        response = self.client.put("/api/index/start")
        assert response.status_code == 405

        response = self.client.delete("/api/index/start")
        assert response.status_code == 405

    def test_start_indexing_invalid_json(self):
        """Test indexing start with invalid JSON."""
        response = self.client.post(
            "/api/index/start",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @patch('src.api.indexing.get_indexer_service')
    def test_get_index_status_success(self, mock_get_service):
        """Test successful index status retrieval."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_indexing_status.return_value = Mock(
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
        mock_get_service.return_value = mock_service

        # Execute
        response = self.client.get("/api/index/status/task-123")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-123"
        assert data["status"] == "running"
        assert data["percentage"] == 50.0
        assert data["repository_url"] == "https://github.com/owner/test-repo"

    @patch('src.api.indexing.get_indexer_service')
    def test_get_index_status_not_found(self, mock_get_service):
        """Test index status retrieval for non-existent task."""
        mock_service = Mock()
        mock_service.get_indexing_status.return_value = None
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/index/status/nonexistent-task")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_index_status_invalid_task_id(self):
        """Test index status retrieval with invalid task ID."""
        response = self.client.get("/api/index/status/")

        assert response.status_code == 404

    @patch('src.api.indexing.get_indexer_service')
    def test_get_index_status_service_error(self, mock_get_service):
        """Test index status retrieval with service error."""
        mock_service = Mock()
        mock_service.get_indexing_status.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/index/status/task-123")

        assert response.status_code == 500
        data = response.json()
        assert "Status retrieval failed" in data["detail"]

    def test_get_index_status_wrong_method(self):
        """Test index status retrieval with wrong HTTP method."""
        response = self.client.post("/api/index/status/task-123")
        assert response.status_code == 405

        response = self.client.put("/api/index/status/task-123")
        assert response.status_code == 405

        response = self.client.delete("/api/index/status/task-123")
        assert response.status_code == 405

    @patch('src.api.indexing.get_indexer_service')
    def test_get_index_stats_success(self, mock_get_service):
        """Test successful index stats retrieval."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_index_stats.return_value = Mock(
            is_indexed=True,
            repository_name="owner/test-repo",
            file_count=100,
            total_size=1024000,
            vector_count=1000,
            last_updated=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        mock_get_service.return_value = mock_service

        # Execute
        response = self.client.get("/api/index/stats")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["is_indexed"] is True
        assert data["repository_name"] == "owner/test-repo"
        assert data["file_count"] == 100
        assert data["total_size"] == 1024000
        assert data["vector_count"] == 1000

    @patch('src.api.indexing.get_indexer_service')
    def test_get_index_stats_not_indexed(self, mock_get_service):
        """Test index stats retrieval when not indexed."""
        mock_service = Mock()
        mock_service.get_index_stats.return_value = Mock(
            is_indexed=False,
            repository_name=None,
            file_count=0,
            total_size=0,
            vector_count=0,
            last_updated=None,
            created_at=None
        )
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/index/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["is_indexed"] is False
        assert data["repository_name"] is None
        assert data["file_count"] == 0

    @patch('src.api.indexing.get_indexer_service')
    def test_get_index_stats_service_error(self, mock_get_service):
        """Test index stats retrieval with service error."""
        mock_service = Mock()
        mock_service.get_index_stats.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/index/stats")

        assert response.status_code == 500
        data = response.json()
        assert "Stats retrieval failed" in data["detail"]

    def test_get_index_stats_wrong_method(self):
        """Test index stats retrieval with wrong HTTP method."""
        response = self.client.post("/api/index/stats")
        assert response.status_code == 405

        response = self.client.put("/api/index/stats")
        assert response.status_code == 405

        response = self.client.delete("/api/index/stats")
        assert response.status_code == 405

    @patch('src.api.indexing.get_indexer_service')
    def test_clear_index_success(self, mock_get_service):
        """Test successful index clearing."""
        # Setup mock
        mock_service = Mock()
        mock_service.clear_index.return_value = {
            "success": True,
            "files_removed": 5,
            "space_freed": 1024000,
            "message": "Index cleared successfully"
        }
        mock_get_service.return_value = mock_service

        # Execute
        response = self.client.delete("/api/index/current")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["files_removed"] == 5
        assert data["space_freed"] == 1024000
        assert "cleared successfully" in data["message"]

    @patch('src.api.indexing.get_indexer_service')
    def test_clear_index_failure(self, mock_get_service):
        """Test index clearing failure."""
        mock_service = Mock()
        mock_service.clear_index.return_value = {
            "success": False,
            "error": "Permission denied",
            "message": "Failed to clear index"
        }
        mock_get_service.return_value = mock_service

        response = self.client.delete("/api/index/current")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Failed to clear" in data["message"]

    @patch('src.api.indexing.get_indexer_service')
    def test_clear_index_service_error(self, mock_get_service):
        """Test index clearing with service error."""
        mock_service = Mock()
        mock_service.clear_index.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        response = self.client.delete("/api/index/current")

        assert response.status_code == 500
        data = response.json()
        assert "Index clearing failed" in data["detail"]

    def test_clear_index_wrong_method(self):
        """Test index clearing with wrong HTTP method."""
        response = self.client.get("/api/index/current")
        assert response.status_code == 405

        response = self.client.post("/api/index/current")
        assert response.status_code == 405

        response = self.client.put("/api/index/current")
        assert response.status_code == 405

    def test_start_indexing_content_type(self):
        """Test indexing start content type."""
        with patch('src.api.indexing.get_indexer_service') as mock_get_service:
            mock_service = Mock()
            mock_service.start_indexing.return_value = Mock(
                task_id="task-123",
                status="pending",
                message="Indexing task created and queued",
                repository_url="https://github.com/owner/test-repo",
                estimated_time=300,
                created_at=datetime.utcnow()
            )
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/index/start",
                json={"repository_url": "https://github.com/owner/test-repo"}
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    def test_get_index_status_content_type(self):
        """Test index status retrieval content type."""
        with patch('src.api.indexing.get_indexer_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_indexing_status.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/index/status/task-123")

            assert response.status_code == 404
            assert response.headers["content-type"] == "application/json"

    def test_get_index_stats_content_type(self):
        """Test index stats retrieval content type."""
        with patch('src.api.indexing.get_indexer_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_index_stats.return_value = Mock(
                is_indexed=False,
                repository_name=None,
                file_count=0,
                total_size=0,
                vector_count=0,
                last_updated=None,
                created_at=None
            )
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/index/stats")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    def test_clear_index_content_type(self):
        """Test index clearing content type."""
        with patch('src.api.indexing.get_indexer_service') as mock_get_service:
            mock_service = Mock()
            mock_service.clear_index.return_value = {
                "success": True,
                "files_removed": 0,
                "space_freed": 0,
                "message": "Index cleared successfully"
            }
            mock_get_service.return_value = mock_service

            response = self.client.delete("/api/index/current")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    def test_cors_headers(self):
        """Test CORS headers for all indexing endpoints."""
        with patch('src.api.indexing.get_indexer_service') as mock_get_service:
            mock_service = Mock()
            mock_service.start_indexing.return_value = Mock(
                task_id="task-123",
                status="pending",
                message="Indexing task created and queued",
                repository_url="https://github.com/owner/test-repo",
                estimated_time=300,
                created_at=datetime.utcnow()
            )
            mock_service.get_indexing_status.return_value = None
            mock_service.get_index_stats.return_value = Mock(
                is_indexed=False,
                repository_name=None,
                file_count=0,
                total_size=0,
                vector_count=0,
                last_updated=None,
                created_at=None
            )
            mock_service.clear_index.return_value = {
                "success": True,
                "files_removed": 0,
                "space_freed": 0,
                "message": "Index cleared successfully"
            }
            mock_get_service.return_value = mock_service

            # Test all endpoints
            response1 = self.client.post(
                "/api/index/start",
                json={"repository_url": "https://github.com/owner/test-repo"}
            )
            response2 = self.client.get("/api/index/status/task-123")
            response3 = self.client.get("/api/index/stats")
            response4 = self.client.delete("/api/index/current")

            # All should have CORS headers
            for response in [response1, response2, response3, response4]:
                assert "access-control-allow-origin" in response.headers
