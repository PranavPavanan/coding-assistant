"""Unit tests for GitHub service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from github import GithubException

from src.services.github_service import GitHubService
from src.models.repository import (
    RepositorySearchRequest,
    RepositoryValidationRequest,
    RepositoryBase,
    Repository,
)


class TestGitHubService:
    """Test cases for GitHubService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.github_service = GitHubService()
        self.mock_repo = Mock()
        self.mock_repo.id = 12345
        self.mock_repo.name = "test-repo"
        self.mock_repo.full_name = "owner/test-repo"
        self.mock_repo.description = "A test repository"
        self.mock_repo.html_url = "https://github.com/owner/test-repo"
        self.mock_repo.stargazers_count = 100
        self.mock_repo.forks_count = 25
        self.mock_repo.language = "Python"
        self.mock_repo.owner.login = "owner"
        self.mock_repo.default_branch = "main"
        self.mock_repo.size = 1024
        self.mock_repo.updated_at = "2023-01-01T00:00:00Z"
        self.mock_repo.created_at = "2022-01-01T00:00:00Z"
        self.mock_repo.clone_url = "https://github.com/owner/test-repo.git"
        self.mock_repo.ssh_url = "git@github.com:owner/test-repo.git"
        self.mock_repo.open_issues_count = 5
        self.mock_repo.watchers_count = 50
        self.mock_repo.license = Mock()
        self.mock_repo.license.name = "MIT"
        self.mock_repo.private = False
        self.mock_repo.fork = False
        self.mock_repo.has_wiki = True
        self.mock_repo.has_issues = True

    @patch('src.services.github_service.Github')
    def test_init_with_token(self, mock_github):
        """Test initialization with GitHub token."""
        token = "test-token"
        service = GitHubService(token)
        mock_github.assert_called_once_with(token)
        assert service.github_token == token

    @patch('src.services.github_service.Github')
    def test_init_without_token(self, mock_github):
        """Test initialization without GitHub token."""
        service = GitHubService()
        mock_github.assert_called_once_with()
        assert service.github_token is None

    @patch('src.services.github_service.Github')
    def test_search_repositories_success(self, mock_github):
        """Test successful repository search."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        
        mock_search_result = Mock()
        mock_search_result.totalCount = 1
        mock_search_result.__iter__ = Mock(return_value=iter([self.mock_repo]))
        mock_github_instance.search_repositories.return_value = mock_search_result

        service = GitHubService()
        request = RepositorySearchRequest(query="test", limit=10)

        # Execute
        result = service.search_repositories(request)

        # Verify
        assert len(result.repositories) == 1
        assert result.total_count == 1
        assert result.page == 1
        assert result.repositories[0].name == "test-repo"
        assert result.repositories[0].full_name == "owner/test-repo"

    @patch('src.services.github_service.Github')
    def test_search_repositories_with_limit(self, mock_github):
        """Test repository search with limit."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        
        mock_search_result = Mock()
        mock_search_result.totalCount = 5
        mock_search_result.__iter__ = Mock(return_value=iter([self.mock_repo] * 5))
        mock_github_instance.search_repositories.return_value = mock_search_result

        service = GitHubService()
        request = RepositorySearchRequest(query="test", limit=3)

        # Execute
        result = service.search_repositories(request)

        # Verify
        assert len(result.repositories) == 3
        assert result.total_count == 5

    @patch('src.services.github_service.Github')
    def test_search_repositories_github_exception(self, mock_github):
        """Test repository search with GitHub API exception."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        
        github_exception = GithubException(403, {"message": "API rate limit exceeded"})
        mock_github_instance.search_repositories.side_effect = github_exception

        service = GitHubService()
        request = RepositorySearchRequest(query="test", limit=10)

        # Execute & Verify
        with pytest.raises(ValueError, match="GitHub API error"):
            service.search_repositories(request)

    @patch('src.services.github_service.Github')
    def test_search_repositories_general_exception(self, mock_github):
        """Test repository search with general exception."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_instance.search_repositories.side_effect = Exception("Network error")

        service = GitHubService()
        request = RepositorySearchRequest(query="test", limit=10)

        # Execute & Verify
        with pytest.raises(ValueError, match="Search failed"):
            service.search_repositories(request)

    @patch('src.services.github_service.Github')
    def test_validate_repository_url_valid(self, mock_github):
        """Test valid repository URL validation."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_instance.get_repo.return_value = self.mock_repo

        service = GitHubService()
        request = RepositoryValidationRequest(url="https://github.com/owner/test-repo")

        # Execute
        result = service.validate_repository_url(request)

        # Verify
        assert result.valid is True
        assert result.message == "Repository is valid and accessible"
        assert result.repository_info is not None
        assert result.repository_info.name == "test-repo"

    def test_validate_repository_url_invalid_format(self):
        """Test invalid repository URL format."""
        service = GitHubService()
        request = RepositoryValidationRequest(url="https://gitlab.com/owner/repo")

        # Execute
        result = service.validate_repository_url(request)

        # Verify
        assert result.valid is False
        assert "Invalid GitHub repository URL format" in result.message

    def test_validate_repository_url_malformed(self):
        """Test malformed repository URL."""
        service = GitHubService()
        request = RepositoryValidationRequest(url="not-a-url")

        # Execute
        result = service.validate_repository_url(request)

        # Verify
        assert result.valid is False
        assert "Invalid GitHub repository URL format" in result.message

    @patch('src.services.github_service.Github')
    def test_validate_repository_url_not_found(self, mock_github):
        """Test repository URL validation for non-existent repository."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        
        github_exception = GithubException(404, {"message": "Not Found"})
        mock_github_instance.get_repo.side_effect = github_exception

        service = GitHubService()
        request = RepositoryValidationRequest(url="https://github.com/owner/nonexistent")

        # Execute
        result = service.validate_repository_url(request)

        # Verify
        assert result.valid is False
        assert result.message == "Repository not found or not accessible"

    @patch('src.services.github_service.Github')
    def test_validate_repository_url_other_error(self, mock_github):
        """Test repository URL validation with other GitHub error."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        
        github_exception = GithubException(500, {"message": "Internal Server Error"})
        mock_github_instance.get_repo.side_effect = github_exception

        service = GitHubService()
        request = RepositoryValidationRequest(url="https://github.com/owner/test-repo")

        # Execute
        result = service.validate_repository_url(request)

        # Verify
        assert result.valid is False
        assert "Error accessing repository" in result.message

    @patch('src.services.github_service.Github')
    def test_validate_repository_url_general_exception(self, mock_github):
        """Test repository URL validation with general exception."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_instance.get_repo.side_effect = Exception("Network error")

        service = GitHubService()
        request = RepositoryValidationRequest(url="https://github.com/owner/test-repo")

        # Execute
        result = service.validate_repository_url(request)

        # Verify
        assert result.valid is False
        assert "Validation error" in result.message

    @patch('src.services.github_service.Github')
    def test_get_repository_success(self, mock_github):
        """Test successful repository retrieval."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_instance.get_repo.return_value = self.mock_repo

        service = GitHubService()

        # Execute
        result = service.get_repository("owner/test-repo")

        # Verify
        assert result is not None
        assert result.name == "test-repo"
        assert result.full_name == "owner/test-repo"
        assert result.clone_url == "https://github.com/owner/test-repo.git"

    @patch('src.services.github_service.Github')
    def test_get_repository_not_found(self, mock_github):
        """Test repository retrieval for non-existent repository."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        
        github_exception = GithubException(404, {"message": "Not Found"})
        mock_github_instance.get_repo.side_effect = github_exception

        service = GitHubService()

        # Execute
        result = service.get_repository("owner/nonexistent")

        # Verify
        assert result is None

    @patch('src.services.github_service.Github')
    def test_get_repository_general_exception(self, mock_github):
        """Test repository retrieval with general exception."""
        # Setup
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_instance.get_repo.side_effect = Exception("Network error")

        service = GitHubService()

        # Execute
        result = service.get_repository("owner/test-repo")

        # Verify
        assert result is None

    def test_get_repository_by_url_valid(self):
        """Test getting repository by valid URL."""
        with patch.object(self.github_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value = Mock()
            
            result = self.github_service.get_repository_by_url("https://github.com/owner/test-repo")
            
            mock_get_repo.assert_called_once_with("owner/test-repo")
            assert result is not None

    def test_get_repository_by_url_invalid(self):
        """Test getting repository by invalid URL."""
        result = self.github_service.get_repository_by_url("https://gitlab.com/owner/repo")
        assert result is None

    @patch('src.services.github_service.git')
    def test_clone_repository_success(self, mock_git):
        """Test successful repository cloning."""
        mock_repo = Mock()
        mock_git.Repo.clone_from.return_value = mock_repo

        result = self.github_service.clone_repository("https://github.com/owner/repo", "/tmp/repo")

        assert result is True
        mock_git.Repo.clone_from.assert_called_once_with("https://github.com/owner/repo", "/tmp/repo")

    @patch('src.services.github_service.git')
    def test_clone_repository_failure(self, mock_git):
        """Test repository cloning failure."""
        mock_git.Repo.clone_from.side_effect = Exception("Clone failed")

        result = self.github_service.clone_repository("https://github.com/owner/repo", "/tmp/repo")

        assert result is False

    def test_convert_to_repository_base(self):
        """Test conversion to RepositoryBase model."""
        result = self.github_service._convert_to_repository_base(self.mock_repo)

        assert isinstance(result, RepositoryBase)
        assert result.id == "12345"
        assert result.name == "test-repo"
        assert result.full_name == "owner/test-repo"
        assert result.description == "A test repository"
        assert result.stars == 100
        assert result.language == "Python"
        assert result.owner == "owner"

    def test_convert_to_repository(self):
        """Test conversion to full Repository model."""
        result = self.github_service._convert_to_repository(self.mock_repo)

        assert isinstance(result, Repository)
        assert result.name == "test-repo"
        assert result.clone_url == "https://github.com/owner/test-repo.git"
        assert result.ssh_url == "git@github.com:owner/test-repo.git"
        assert result.open_issues == 5
        assert result.license == "MIT"
        assert result.is_private is False
        assert result.is_fork is False
