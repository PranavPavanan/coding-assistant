"""GitHub API service for repository operations."""
import re
from typing import Optional

from github import Github, GithubException
from github import Repository as GHRepository

from src.config import settings
from src.models.repository import (
    Repository,
    RepositoryBase,
    RepositorySearchRequest,
    RepositorySearchResponse,
    RepositoryValidationRequest,
    RepositoryValidationResponse,
)


class GitHubService:
    """Service for interacting with GitHub API."""

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub service.

        Args:
            github_token: Optional GitHub personal access token for authenticated requests
        """
        self.github = Github(github_token) if github_token else Github()
        self.github_token = github_token

    def search_repositories(self, request: RepositorySearchRequest) -> RepositorySearchResponse:
        """
        Search GitHub repositories.

        Args:
            request: Search request with query and limit

        Returns:
            RepositorySearchResponse with matching repositories
        """
        try:
            # Search repositories using GitHub API
            repositories = self.github.search_repositories(
                query=request.query, sort="stars", order="desc"
            )

            # Convert to our model format
            results = []
            for i, repo in enumerate(repositories):
                if i >= request.limit:
                    break

                repo_base = self._convert_to_repository_base(repo)
                results.append(repo_base)

            return RepositorySearchResponse(
                repositories=results,
                total_count=repositories.totalCount,
                page=1,
            )

        except GithubException as e:
            # Handle GitHub API errors
            raise ValueError(f"GitHub API error: {e.data.get('message', str(e))}") from e
        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}") from e

    def validate_repository_url(
        self, request: RepositoryValidationRequest
    ) -> RepositoryValidationResponse:
        """
        Validate a GitHub repository URL.

        Args:
            request: Validation request with URL

        Returns:
            RepositoryValidationResponse with validation result
        """
        url = request.url.strip()

        # Check if it's a valid GitHub URL
        github_pattern = r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
        match = re.match(github_pattern, url)

        if not match:
            return RepositoryValidationResponse(
                valid=False,
                message="Invalid GitHub repository URL format. Expected: https://github.com/owner/repo",
            )

        owner, repo_name = match.groups()

        try:
            # Try to fetch the repository to verify it exists
            repo = self.github.get_repo(f"{owner}/{repo_name}")

            # Repository exists, return info
            repo_base = self._convert_to_repository_base(repo)

            return RepositoryValidationResponse(
                valid=True,
                message="Repository is valid and accessible",
                repository_info=repo_base,
            )

        except GithubException as e:
            if e.status == 404:
                return RepositoryValidationResponse(
                    valid=False,
                    message="Repository not found or not accessible",
                )
            else:
                return RepositoryValidationResponse(
                    valid=False,
                    message=f"Error accessing repository: {e.data.get('message', str(e))}",
                )
        except Exception as e:
            return RepositoryValidationResponse(
                valid=False,
                message=f"Validation error: {str(e)}",
            )

    def get_repository(self, repo_id: str) -> Optional[Repository]:
        """
        Get detailed repository information.

        Args:
            repo_id: Repository identifier (owner/repo format)

        Returns:
            Repository object or None if not found
        """
        try:
            repo = self.github.get_repo(repo_id)
            return self._convert_to_repository(repo)
        except GithubException:
            return None
        except Exception:
            return None

    def get_repository_by_url(self, url: str) -> Optional[Repository]:
        """
        Get repository by GitHub URL.

        Args:
            url: GitHub repository URL

        Returns:
            Repository object or None if invalid
        """
        github_pattern = r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
        match = re.match(github_pattern, url)

        if not match:
            return None

        owner, repo_name = match.groups()
        return self.get_repository(f"{owner}/{repo_name}")

    def clone_repository(self, repo_url: str, target_dir: str) -> bool:
        """
        Clone a repository to local directory.

        Args:
            repo_url: Repository URL to clone
            target_dir: Target directory for cloning

        Returns:
            True if successful, False otherwise
        """
        try:
            import git

            git.Repo.clone_from(repo_url, target_dir)
            return True
        except Exception as e:
            print(f"Clone failed: {e}")
            return False

    def _convert_to_repository_base(self, gh_repo: GHRepository) -> RepositoryBase:
        """Convert GitHub repository to RepositoryBase model."""
        return RepositoryBase(
            id=str(gh_repo.id),
            name=gh_repo.name,
            full_name=gh_repo.full_name,
            description=gh_repo.description,
            url=gh_repo.html_url,
            html_url=gh_repo.html_url,
            stars=gh_repo.stargazers_count,
            stargazers_count=gh_repo.stargazers_count,
            forks=gh_repo.forks_count,
            language=gh_repo.language,
            topics=gh_repo.get_topics() if hasattr(gh_repo, "get_topics") else [],
            owner=gh_repo.owner.login,
            default_branch=gh_repo.default_branch,
            size=gh_repo.size,
            updated_at=gh_repo.updated_at,
            created_at=gh_repo.created_at,
        )

    def _convert_to_repository(self, gh_repo: GHRepository) -> Repository:
        """Convert GitHub repository to full Repository model."""
        base_dict = self._convert_to_repository_base(gh_repo).model_dump()

        return Repository(
            **base_dict,
            clone_url=gh_repo.clone_url,
            ssh_url=gh_repo.ssh_url,
            open_issues=gh_repo.open_issues_count,
            watchers=gh_repo.watchers_count,
            license=gh_repo.license.name if gh_repo.license else None,
            is_private=gh_repo.private,
            is_fork=gh_repo.fork,
            has_wiki=gh_repo.has_wiki,
            has_issues=gh_repo.has_issues,
        )


# Singleton instance
_github_service: Optional[GitHubService] = None


def get_github_service(github_token: Optional[str] = None) -> GitHubService:
    """
    Get or create GitHub service instance.

    Args:
        github_token: Optional GitHub token, defaults to env variable

    Returns:
        GitHubService instance
    """
    global _github_service
    if _github_service is None:
        # Use provided token or fall back to settings
        token = github_token or settings.get_github_token()
        _github_service = GitHubService(token)
    return _github_service
