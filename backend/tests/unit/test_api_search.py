"""Unit tests for search API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json

from src.main import app


class TestSearchAPI:
    """Test cases for search endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    @patch('src.api.search.get_github_service')
    def test_search_repositories_success(self, mock_get_service):
        """Test successful repository search."""
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
        mock_repo.get_topics.return_value = ["python", "test"]
        
        mock_search_result = Mock()
        mock_search_result.totalCount = 1
        mock_search_result.__iter__ = Mock(return_value=iter([mock_repo]))
        mock_service.search_repositories.return_value = Mock(
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
        mock_get_service.return_value = mock_service

        # Execute
        response = self.client.post(
            "/api/search/repositories",
            json={"query": "python test", "limit": 10}
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "repositories" in data
        assert "total_count" in data
        assert "page" in data
        assert len(data["repositories"]) == 1
        assert data["repositories"][0]["name"] == "test-repo"
        assert data["total_count"] == 1

    def test_search_repositories_missing_query(self):
        """Test repository search with missing query."""
        response = self.client.post(
            "/api/search/repositories",
            json={"limit": 10}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_search_repositories_invalid_query(self):
        """Test repository search with invalid query."""
        response = self.client.post(
            "/api/search/repositories",
            json={"query": "", "limit": 10}
        )

        assert response.status_code == 422

    def test_search_repositories_invalid_limit(self):
        """Test repository search with invalid limit."""
        response = self.client.post(
            "/api/search/repositories",
            json={"query": "python", "limit": -1}
        )

        assert response.status_code == 422

    def test_search_repositories_large_limit(self):
        """Test repository search with large limit."""
        response = self.client.post(
            "/api/search/repositories",
            json={"query": "python", "limit": 1000}
        )

        assert response.status_code == 422

    def test_search_repositories_default_limit(self):
        """Test repository search with default limit."""
        with patch('src.api.search.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_repositories.return_value = Mock(
                repositories=[],
                total_count=0,
                page=1
            )
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/search/repositories",
                json={"query": "python"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 0

    @patch('src.api.search.get_github_service')
    def test_search_repositories_service_error(self, mock_get_service):
        """Test repository search with service error."""
        mock_service = Mock()
        mock_service.search_repositories.side_effect = ValueError("GitHub API error")
        mock_get_service.return_value = mock_service

        response = self.client.post(
            "/api/search/repositories",
            json={"query": "python", "limit": 10}
        )

        assert response.status_code == 500
        data = response.json()
        assert "Search failed" in data["detail"]

    def test_search_repositories_invalid_json(self):
        """Test repository search with invalid JSON."""
        response = self.client.post(
            "/api/search/repositories",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_search_repositories_wrong_method(self):
        """Test repository search with wrong HTTP method."""
        response = self.client.get("/api/search/repositories")
        assert response.status_code == 405

    @patch('src.api.search.get_github_service')
    def test_validate_url_success(self, mock_get_service):
        """Test successful URL validation."""
        mock_service = Mock()
        mock_service.validate_repository_url.return_value = Mock(
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
        mock_get_service.return_value = mock_service

        response = self.client.post(
            "/api/validate/url",
            json={"url": "https://github.com/owner/test-repo"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert "Repository is valid" in data["message"]
        assert "repository" in data

    def test_validate_url_missing_url(self):
        """Test URL validation with missing URL."""
        response = self.client.post(
            "/api/validate/url",
            json={}
        )

        assert response.status_code == 422

    def test_validate_url_invalid_url(self):
        """Test URL validation with invalid URL."""
        response = self.client.post(
            "/api/validate/url",
            json={"url": "not-a-url"}
        )

        assert response.status_code == 422

    @patch('src.api.search.get_github_service')
    def test_validate_url_invalid_repository(self, mock_get_service):
        """Test URL validation with invalid repository."""
        mock_service = Mock()
        mock_service.validate_repository_url.return_value = Mock(
            valid=False,
            message="Repository not found or not accessible",
            repository_info=None
        )
        mock_get_service.return_value = mock_service

        response = self.client.post(
            "/api/validate/url",
            json={"url": "https://github.com/owner/nonexistent"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert "not found" in data["message"].lower()

    @patch('src.api.search.get_github_service')
    def test_validate_url_service_error(self, mock_get_service):
        """Test URL validation with service error."""
        mock_service = Mock()
        mock_service.validate_repository_url.side_effect = Exception("Network error")
        mock_get_service.return_value = mock_service

        response = self.client.post(
            "/api/validate/url",
            json={"url": "https://github.com/owner/test-repo"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "Validation failed" in data["detail"]

    def test_validate_url_wrong_method(self):
        """Test URL validation with wrong HTTP method."""
        response = self.client.get("/api/validate/url")
        assert response.status_code == 405

    def test_search_repositories_content_type(self):
        """Test repository search content type."""
        with patch('src.api.search.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_repositories.return_value = Mock(
                repositories=[],
                total_count=0,
                page=1
            )
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/search/repositories",
                json={"query": "python"}
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    def test_validate_url_content_type(self):
        """Test URL validation content type."""
        with patch('src.api.search.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.validate_repository_url.return_value = Mock(
                valid=False,
                message="Invalid URL",
                repository_info=None
            )
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/validate/url",
                json={"url": "invalid-url"}
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    def test_search_repositories_cors_headers(self):
        """Test repository search CORS headers."""
        with patch('src.api.search.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_repositories.return_value = Mock(
                repositories=[],
                total_count=0,
                page=1
            )
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/search/repositories",
                json={"query": "python"}
            )

            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers

    def test_validate_url_cors_headers(self):
        """Test URL validation CORS headers."""
        with patch('src.api.search.get_github_service') as mock_get_service:
            mock_service = Mock()
            mock_service.validate_repository_url.return_value = Mock(
                valid=False,
                message="Invalid URL",
                repository_info=None
            )
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/validate/url",
                json={"url": "invalid-url"}
            )

            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers

    def test_search_repositories_large_response(self):
        """Test repository search with large response."""
        with patch('src.api.search.get_github_service') as mock_get_service:
            # Create mock repositories
            mock_repos = []
            for i in range(100):
                mock_repo = Mock(
                    id=str(i),
                    name=f"repo-{i}",
                    full_name=f"owner/repo-{i}",
                    description=f"Description {i}",
                    url=f"https://github.com/owner/repo-{i}",
                    html_url=f"https://github.com/owner/repo-{i}",
                    stars=i * 10,
                    stargazers_count=i * 10,
                    forks=i * 2,
                    language="Python",
                    topics=[],
                    owner="owner",
                    default_branch="main",
                    size=1024,
                    updated_at="2023-01-01T00:00:00Z",
                    created_at="2022-01-01T00:00:00Z"
                )
                mock_repos.append(mock_repo)

            mock_service = Mock()
            mock_service.search_repositories.return_value = Mock(
                repositories=mock_repos,
                total_count=100,
                page=1
            )
            mock_get_service.return_value = mock_service

            response = self.client.post(
                "/api/search/repositories",
                json={"query": "python", "limit": 100}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["repositories"]) == 100
            assert data["total_count"] == 100

    def test_search_repositories_empty_query(self):
        """Test repository search with empty query string."""
        response = self.client.post(
            "/api/search/repositories",
            json={"query": "   ", "limit": 10}
        )

        assert response.status_code == 422

    def test_validate_url_empty_url(self):
        """Test URL validation with empty URL."""
        response = self.client.post(
            "/api/validate/url",
            json={"url": ""}
        )

        assert response.status_code == 422

    def test_validate_url_whitespace_url(self):
        """Test URL validation with whitespace URL."""
        response = self.client.post(
            "/api/validate/url",
            json={"url": "   "}
        )

        assert response.status_code == 422
