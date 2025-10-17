"""Unit tests for repositories API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from src.main import app


class TestRepositoriesAPI:
    """Test cases for repositories endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    @patch('src.api.repositories.get_github_service')
    def test_get_repository_success(self, mock_get_service):
        """Test successful repository retrieval."""
        # Setup mock
        mock_service = Mock()
        mock_repo = Mock()
        mock_repo.id = "12345"
        mock_repo.name = "test-repo"
        mock_repo.full_name = "owner/test-repo"
        mock_repo.description = "A test repository"
        mock_repo.html_url = "https://github.com/owner/test-repo"
        mock_repo.stargazers_count = 100
        mock_repo.forks_count = 25
        mock_repo.language = "Python"
        mock_repo.owner.login = "owner"
        mock_repo.default_branch = "main"
        mock_repo.size = 1024
        mock_repo.updated_at = "2023-01-01T00:00:00Z"
        mock_repo.created_at = "2022-01-01T00:00:00Z"
        mock_repo.clone_url = "https://github.com/owner/test-repo.git"
        mock_repo.ssh_url = "git@github.com:owner/test-repo.git"
        mock_repo.open_issues_count = 5
        mock_repo.watchers_count = 50
        mock_repo.license = Mock()
        mock_repo.license.name = "MIT"
        mock_repo.private = False
        mock_repo.fork = False
        mock_repo.has_wiki = True
        mock_repo.has_issues = True
        mock_repo.get_topics.return_value = ["python", "test"]
        
        mock_service.get_repository.return_value = Mock(
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
        mock_get_service.return_value = mock_service

        # Execute
        response = self.client.get("/api/repositories/owner/test-repo")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-repo"
        assert data["full_name"] == "owner/test-repo"
        assert data["description"] == "A test repository"
        assert data["stars"] == 100
        assert data["language"] == "Python"
        assert data["clone_url"] == "https://github.com/owner/test-repo.git"

    @patch('src.api.repositories.get_github_service')
    def test_get_repository_not_found(self, mock_get_service):
        """Test repository retrieval for non-existent repository."""
        mock_service = Mock()
        mock_service.get_repository.return_value = None
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/repositories/owner/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_repository_invalid_format(self):
        """Test repository retrieval with invalid format."""
        response = self.client.get("/api/repositories/invalid-format")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_repository_missing_owner(self):
        """Test repository retrieval with missing owner."""
        response = self.client.get("/api/repositories/test-repo")

        assert response.status_code == 422

    def test_get_repository_empty_owner(self):
        """Test repository retrieval with empty owner."""
        response = self.client.get("/api/repositories//test-repo")

        assert response.status_code == 422

    def test_get_repository_empty_repo_name(self):
        """Test repository retrieval with empty repo name."""
        response = self.client.get("/api/repositories/owner/")

        assert response.status_code == 422

    def test_get_repository_special_characters(self):
        """Test repository retrieval with special characters."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/repositories/owner/repo-with-dashes")

            assert response.status_code == 404

    def test_get_repository_unicode_characters(self):
        """Test repository retrieval with unicode characters."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/repositories/owner/répô")

            assert response.status_code == 404

    @patch('src.api.repositories.get_github_service')
    def test_get_repository_service_error(self, mock_get_service):
        """Test repository retrieval with service error."""
        mock_service = Mock()
        mock_service.get_repository.side_effect = Exception("Network error")
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/repositories/owner/test-repo")

        assert response.status_code == 500
        data = response.json()
        assert "Repository retrieval failed" in data["detail"]

    def test_get_repository_wrong_method(self):
        """Test repository retrieval with wrong HTTP method."""
        response = self.client.post("/api/repositories/owner/test-repo")
        assert response.status_code == 405

        response = self.client.put("/api/repositories/owner/test-repo")
        assert response.status_code == 405

        response = self.client.delete("/api/repositories/owner/test-repo")
        assert response.status_code == 405

    def test_get_repository_content_type(self):
        """Test repository retrieval content type."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/repositories/owner/test-repo")

            assert response.status_code == 404
            assert response.headers["content-type"] == "application/json"

    def test_get_repository_cors_headers(self):
        """Test repository retrieval CORS headers."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/repositories/owner/test-repo")

            assert response.status_code == 404
            assert "access-control-allow-origin" in response.headers

    def test_get_repository_with_query_params(self):
        """Test repository retrieval with query parameters."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/repositories/owner/test-repo?include=forks&format=json")

            assert response.status_code == 404

    def test_get_repository_with_headers(self):
        """Test repository retrieval with custom headers."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            headers = {
                "User-Agent": "Test Client",
                "Accept": "application/json",
                "X-Custom-Header": "test-value"
            }

            response = self.client.get("/api/repositories/owner/test-repo", headers=headers)

            assert response.status_code == 404

    def test_get_repository_case_sensitivity(self):
        """Test repository retrieval case sensitivity."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            # Test different cases
            response1 = self.client.get("/api/repositories/owner/test-repo")
            response2 = self.client.get("/api/repositories/owner/Test-Repo")
            response3 = self.client.get("/api/repositories/Owner/test-repo")

            assert response1.status_code == 404
            assert response2.status_code == 404
            assert response3.status_code == 404

    def test_get_repository_long_names(self):
        """Test repository retrieval with long names."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            # Test with very long repository name
            long_repo_name = "a" * 100
            response = self.client.get(f"/api/repositories/owner/{long_repo_name}")

            assert response.status_code == 404

    def test_get_repository_numeric_names(self):
        """Test repository retrieval with numeric names."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/repositories/owner/123")

            assert response.status_code == 404

    def test_get_repository_with_dots(self):
        """Test repository retrieval with dots in name."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/repositories/owner/repo.name")

            assert response.status_code == 404

    def test_get_repository_with_underscores(self):
        """Test repository retrieval with underscores in name."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            response = self.client.get("/api/repositories/owner/repo_name")

            assert response.status_code == 404

    def test_get_repository_path_traversal(self):
        """Test repository retrieval with path traversal attempts."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            # Test path traversal attempts
            response1 = self.client.get("/api/repositories/owner/../other")
            response2 = self.client.get("/api/repositories/owner/./test")
            response3 = self.client.get("/api/repositories/owner/test/../other")

            # Should be treated as literal repository names
            assert response1.status_code == 404
            assert response2.status_code == 404
            assert response3.status_code == 404

    def test_get_repository_encoding(self):
        """Test repository retrieval with URL encoding."""
        with patch('src.api.repositories.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_repository.return_value = None
            mock_get_service.return_value = mock_service

            # Test URL encoded characters
            response = self.client.get("/api/repositories/owner/repo%20name")

            assert response.status_code == 404
