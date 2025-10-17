"""Unit tests for data models."""
import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.repository import (
    RepositoryBase,
    Repository,
    RepositorySearchRequest,
    RepositorySearchResponse,
    RepositoryValidationRequest,
    RepositoryValidationResponse,
)
from src.models.index import (
    IndexStartRequest,
    IndexStartResponse,
    IndexStatusResponse,
    IndexProgressInfo,
    IndexingStatus,
    IndexStats,
    FileIndexEntry,
)
from src.models.query import (
    QueryRequest,
    QueryResponse,
    ChatMessage,
    ChatHistoryRequest,
    ChatHistoryResponse,
    ChatContextResponse,
    SourceReference,
)
from src.models.response import HealthResponse


class TestRepositoryModels:
    """Test cases for repository models."""

    def test_repository_base_valid(self):
        """Test valid RepositoryBase creation."""
        repo = RepositoryBase(
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
        )
        
        assert repo.id == "12345"
        assert repo.name == "test-repo"
        assert repo.full_name == "owner/test-repo"
        assert repo.description == "A test repository"
        assert repo.stars == 100
        assert repo.language == "Python"
        assert repo.topics == ["python", "test"]

    def test_repository_base_optional_fields(self):
        """Test RepositoryBase with optional fields."""
        repo = RepositoryBase(
            id="12345",
            name="test-repo",
            full_name="owner/test-repo",
            description=None,
            url="https://github.com/owner/test-repo",
            html_url="https://github.com/owner/test-repo",
            stars=100,
            stargazers_count=100,
            forks=25,
            language=None,
            topics=[],
            owner="owner",
            default_branch="main",
            size=1024,
            updated_at="2023-01-01T00:00:00Z",
            created_at="2022-01-01T00:00:00Z",
        )
        
        assert repo.description is None
        assert repo.language is None
        assert repo.topics == []

    def test_repository_valid(self):
        """Test valid Repository creation."""
        repo = Repository(
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
            has_issues=True,
        )
        
        assert repo.clone_url == "https://github.com/owner/test-repo.git"
        assert repo.ssh_url == "git@github.com:owner/test-repo.git"
        assert repo.open_issues == 5
        assert repo.watchers == 50
        assert repo.license == "MIT"
        assert repo.is_private is False
        assert repo.is_fork is False
        assert repo.has_wiki is True
        assert repo.has_issues is True

    def test_repository_search_request_valid(self):
        """Test valid RepositorySearchRequest creation."""
        request = RepositorySearchRequest(query="python test", limit=10)
        
        assert request.query == "python test"
        assert request.limit == 10

    def test_repository_search_request_default_limit(self):
        """Test RepositorySearchRequest with default limit."""
        request = RepositorySearchRequest(query="python test")
        
        assert request.query == "python test"
        assert request.limit == 10

    def test_repository_search_response_valid(self):
        """Test valid RepositorySearchResponse creation."""
        repos = [
            RepositoryBase(
                id="1", name="repo1", full_name="owner/repo1",
                description="Test repo 1", url="https://github.com/owner/repo1",
                html_url="https://github.com/owner/repo1", stars=100,
                stargazers_count=100, forks=25, language="Python",
                topics=[], owner="owner", default_branch="main",
                size=1024, updated_at="2023-01-01T00:00:00Z",
                created_at="2022-01-01T00:00:00Z"
            )
        ]
        
        response = RepositorySearchResponse(
            repositories=repos,
            total_count=1,
            page=1
        )
        
        assert len(response.repositories) == 1
        assert response.total_count == 1
        assert response.page == 1

    def test_repository_validation_request_valid(self):
        """Test valid RepositoryValidationRequest creation."""
        request = RepositoryValidationRequest(url="https://github.com/owner/repo")
        
        assert request.url == "https://github.com/owner/repo"

    def test_repository_validation_response_valid(self):
        """Test valid RepositoryValidationResponse creation."""
        repo_info = RepositoryBase(
            id="12345", name="test-repo", full_name="owner/test-repo",
            description="A test repository", url="https://github.com/owner/test-repo",
            html_url="https://github.com/owner/test-repo", stars=100,
            stargazers_count=100, forks=25, language="Python",
            topics=[], owner="owner", default_branch="main",
            size=1024, updated_at="2023-01-01T00:00:00Z",
            created_at="2022-01-01T00:00:00Z"
        )
        
        response = RepositoryValidationResponse(
            valid=True,
            message="Repository is valid",
            repository_info=repo_info
        )
        
        assert response.valid is True
        assert response.message == "Repository is valid"
        assert response.repository_info is not None

    def test_repository_validation_response_invalid(self):
        """Test invalid RepositoryValidationResponse creation."""
        response = RepositoryValidationResponse(
            valid=False,
            message="Repository not found"
        )
        
        assert response.valid is False
        assert response.message == "Repository not found"
        assert response.repository_info is None


class TestIndexModels:
    """Test cases for index models."""

    def test_index_start_request_valid(self):
        """Test valid IndexStartRequest creation."""
        request = IndexStartRequest(
            repository_url="https://github.com/owner/repo",
            branch="main"
        )
        
        assert request.repository_url == "https://github.com/owner/repo"
        assert request.branch == "main"

    def test_index_start_request_default_branch(self):
        """Test IndexStartRequest with default branch."""
        request = IndexStartRequest(repository_url="https://github.com/owner/repo")
        
        assert request.repository_url == "https://github.com/owner/repo"
        assert request.branch == "main"

    def test_index_start_response_valid(self):
        """Test valid IndexStartResponse creation."""
        response = IndexStartResponse(
            task_id="task-123",
            status=IndexingStatus.PENDING,
            message="Task created",
            repository_url="https://github.com/owner/repo",
            estimated_time=300,
            created_at=datetime.utcnow()
        )
        
        assert response.task_id == "task-123"
        assert response.status == IndexingStatus.PENDING
        assert response.message == "Task created"
        assert response.repository_url == "https://github.com/owner/repo"
        assert response.estimated_time == 300

    def test_index_progress_info_valid(self):
        """Test valid IndexProgressInfo creation."""
        progress = IndexProgressInfo(
            files_processed=50,
            total_files=100,
            percentage=50.0
        )
        
        assert progress.files_processed == 50
        assert progress.total_files == 100
        assert progress.percentage == 50.0

    def test_index_status_response_valid(self):
        """Test valid IndexStatusResponse creation."""
        progress = IndexProgressInfo(
            files_processed=50,
            total_files=100,
            percentage=50.0
        )
        
        response = IndexStatusResponse(
            task_id="task-123",
            status=IndexingStatus.RUNNING,
            message="Indexing in progress",
            progress=progress,
            percentage=50.0,
            repository_url="https://github.com/owner/repo",
            started_at=datetime.utcnow(),
            completed_at=None,
            error=None,
            result=None
        )
        
        assert response.task_id == "task-123"
        assert response.status == IndexingStatus.RUNNING
        assert response.message == "Indexing in progress"
        assert response.progress == progress
        assert response.percentage == 50.0

    def test_index_stats_valid(self):
        """Test valid IndexStats creation."""
        stats = IndexStats(
            is_indexed=True,
            repository_name="owner/repo",
            file_count=100,
            total_size=1024000,
            vector_count=1000,
            last_updated=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        assert stats.is_indexed is True
        assert stats.repository_name == "owner/repo"
        assert stats.file_count == 100
        assert stats.total_size == 1024000
        assert stats.vector_count == 1000

    def test_index_stats_not_indexed(self):
        """Test IndexStats for non-indexed state."""
        stats = IndexStats(
            is_indexed=False,
            repository_name=None,
            file_count=0,
            total_size=0,
            vector_count=0,
            last_updated=None,
            created_at=None
        )
        
        assert stats.is_indexed is False
        assert stats.repository_name is None
        assert stats.file_count == 0

    def test_file_index_entry_valid(self):
        """Test valid FileIndexEntry creation."""
        entry = FileIndexEntry(
            file_path="src/test.py",
            content_hash="abc123",
            size=1024,
            language="python",
            chunk_count=5,
            indexed_at=datetime.utcnow()
        )
        
        assert entry.file_path == "src/test.py"
        assert entry.content_hash == "abc123"
        assert entry.size == 1024
        assert entry.language == "python"
        assert entry.chunk_count == 5

    def test_indexing_status_enum(self):
        """Test IndexingStatus enum values."""
        assert IndexingStatus.PENDING == "pending"
        assert IndexingStatus.RUNNING == "running"
        assert IndexingStatus.COMPLETED == "completed"
        assert IndexingStatus.FAILED == "failed"
        assert IndexingStatus.CANCELLED == "cancelled"


class TestQueryModels:
    """Test cases for query models."""

    def test_query_request_valid(self):
        """Test valid QueryRequest creation."""
        request = QueryRequest(
            query="What does this function do?",
            conversation_id="conv-123"
        )
        
        assert request.query == "What does this function do?"
        assert request.conversation_id == "conv-123"

    def test_query_request_without_conversation_id(self):
        """Test QueryRequest without conversation ID."""
        request = QueryRequest(query="What does this function do?")
        
        assert request.query == "What does this function do?"
        assert request.conversation_id is None

    def test_query_response_valid(self):
        """Test valid QueryResponse creation."""
        sources = [
            SourceReference(
                file_path="src/test.py",
                start_line=10,
                end_line=20,
                content="def test():\n    pass",
                score=0.95
            )
        ]
        
        response = QueryResponse(
            response="This function does X",
            sources=sources,
            conversation_id="conv-123",
            confidence=0.85,
            processing_time=1.5,
            model_used="codellama-7b"
        )
        
        assert response.response == "This function does X"
        assert len(response.sources) == 1
        assert response.conversation_id == "conv-123"
        assert response.confidence == 0.85
        assert response.processing_time == 1.5
        assert response.model_used == "codellama-7b"

    def test_chat_message_valid(self):
        """Test valid ChatMessage creation."""
        message = ChatMessage(
            role="user",
            content="Hello",
            timestamp=datetime.utcnow(),
            sources=None
        )
        
        assert message.role == "user"
        assert message.content == "Hello"
        assert message.timestamp is not None
        assert message.sources is None

    def test_chat_message_with_sources(self):
        """Test ChatMessage with sources."""
        sources = [
            SourceReference(
                file_path="src/test.py",
                start_line=10,
                end_line=20,
                content="def test():\n    pass",
                score=0.95
            )
        ]
        
        message = ChatMessage(
            role="assistant",
            content="Here's the answer",
            timestamp=datetime.utcnow(),
            sources=sources
        )
        
        assert message.role == "assistant"
        assert message.content == "Here's the answer"
        assert len(message.sources) == 1

    def test_chat_history_request_valid(self):
        """Test valid ChatHistoryRequest creation."""
        request = ChatHistoryRequest(
            conversation_id="conv-123",
            limit=50
        )
        
        assert request.conversation_id == "conv-123"
        assert request.limit == 50

    def test_chat_history_request_default_limit(self):
        """Test ChatHistoryRequest with default limit."""
        request = ChatHistoryRequest(conversation_id="conv-123")
        
        assert request.conversation_id == "conv-123"
        assert request.limit is None

    def test_chat_history_response_valid(self):
        """Test valid ChatHistoryResponse creation."""
        messages = [
            ChatMessage(role="user", content="Hello", timestamp=datetime.utcnow()),
            ChatMessage(role="assistant", content="Hi there", timestamp=datetime.utcnow())
        ]
        
        response = ChatHistoryResponse(
            conversation_id="conv-123",
            messages=messages,
            total_messages=2,
            created_at=datetime.utcnow()
        )
        
        assert response.conversation_id == "conv-123"
        assert len(response.messages) == 2
        assert response.total_messages == 2

    def test_chat_context_response_valid(self):
        """Test valid ChatContextResponse creation."""
        response = ChatContextResponse(
            conversation_id="conv-123",
            message_count=10,
            user_message_count=5,
            assistant_message_count=5,
            last_query="What does this do?",
            last_response="It does X",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        assert response.conversation_id == "conv-123"
        assert response.message_count == 10
        assert response.user_message_count == 5
        assert response.assistant_message_count == 5
        assert response.last_query == "What does this do?"
        assert response.last_response == "It does X"

    def test_source_reference_valid(self):
        """Test valid SourceReference creation."""
        source = SourceReference(
            file_path="src/test.py",
            start_line=10,
            end_line=20,
            content="def test():\n    pass",
            score=0.95
        )
        
        assert source.file_path == "src/test.py"
        assert source.start_line == 10
        assert source.end_line == 20
        assert source.content == "def test():\n    pass"
        assert source.score == 0.95


class TestResponseModels:
    """Test cases for response models."""

    def test_health_response_valid(self):
        """Test valid HealthResponse creation."""
        response = HealthResponse(
            status="healthy",
            message="Backend is running"
        )
        
        assert response.status == "healthy"
        assert response.message == "Backend is running"

    def test_health_response_unhealthy(self):
        """Test HealthResponse for unhealthy state."""
        response = HealthResponse(
            status="unhealthy",
            message="Service is down"
        )
        
        assert response.status == "unhealthy"
        assert response.message == "Service is down"


class TestModelValidation:
    """Test cases for model validation."""

    def test_repository_base_validation_error(self):
        """Test RepositoryBase validation with missing required fields."""
        with pytest.raises(ValidationError):
            RepositoryBase(
                # Missing required fields
                name="test-repo"
            )

    def test_query_request_validation_error(self):
        """Test QueryRequest validation with empty query."""
        with pytest.raises(ValidationError):
            QueryRequest(query="")  # Empty query should fail

    def test_chat_message_validation_error(self):
        """Test ChatMessage validation with invalid role."""
        with pytest.raises(ValidationError):
            ChatMessage(
                role="invalid_role",  # Invalid role
                content="Hello",
                timestamp=datetime.utcnow()
            )

    def test_source_reference_validation_error(self):
        """Test SourceReference validation with invalid score."""
        with pytest.raises(ValidationError):
            SourceReference(
                file_path="test.py",
                start_line=10,
                end_line=20,
                content="test",
                score=1.5  # Score should be between 0 and 1
            )
