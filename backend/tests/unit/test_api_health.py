"""Unit tests for health API endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.main import app


class TestHealthAPI:
    """Test cases for health endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def test_health_check_success(self):
        """Test successful health check."""
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Backend is running" in data["message"]

    def test_health_check_response_format(self):
        """Test health check response format."""
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)

    def test_health_check_headers(self):
        """Test health check response headers."""
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_health_check_methods(self):
        """Test health check with different HTTP methods."""
        # GET should work
        response = self.client.get("/api/health")
        assert response.status_code == 200
        
        # POST should not work
        response = self.client.post("/api/health")
        assert response.status_code == 405
        
        # PUT should not work
        response = self.client.put("/api/health")
        assert response.status_code == 405
        
        # DELETE should not work
        response = self.client.delete("/api/health")
        assert response.status_code == 405

    def test_health_check_path_variations(self):
        """Test health check with different path variations."""
        # Test with trailing slash
        response = self.client.get("/api/health/")
        assert response.status_code == 200
        
        # Test without /api prefix (should not work)
        response = self.client.get("/health")
        assert response.status_code == 404

    def test_health_check_concurrent_requests(self):
        """Test health check with concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = self.client.get("/api/health")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10

    def test_health_check_performance(self):
        """Test health check performance."""
        import time
        
        start_time = time.time()
        response = self.client.get("/api/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # Should respond quickly (less than 1 second)
        assert (end_time - start_time) < 1.0

    def test_health_check_with_query_params(self):
        """Test health check with query parameters (should be ignored)."""
        response = self.client.get("/api/health?test=value&another=param")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_with_headers(self):
        """Test health check with custom headers."""
        headers = {
            "User-Agent": "Test Client",
            "Accept": "application/json",
            "X-Custom-Header": "test-value"
        }
        
        response = self.client.get("/api/health", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_cors_headers(self):
        """Test health check CORS headers."""
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        # CORS headers should be present due to CORS middleware
        assert "access-control-allow-origin" in response.headers

    def test_health_check_content_type(self):
        """Test health check content type."""
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_health_check_json_serialization(self):
        """Test health check JSON serialization."""
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify JSON structure
        assert isinstance(data, dict)
        assert len(data) == 2  # status and message
        assert "status" in data
        assert "message" in data
        
        # Verify data types
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)
        
        # Verify values
        assert data["status"] == "healthy"
        assert len(data["message"]) > 0
