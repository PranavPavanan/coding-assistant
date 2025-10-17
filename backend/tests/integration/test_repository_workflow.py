"""Integration tests for complete repository workflow."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime

from src.main import app


class TestRepositoryWorkflow:
    """Integration tests for complete repository discovery and indexing workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    @patch('src.api.search.get_github_service')
    @patch('src.api.indexing.get_indexer_service')
    def test_complete_repository_workflow(self, mock_get_indexer, mock_get_github):
        """Test complete workflow from search to indexing."""
        # Setup GitHub service mock
        mock_github_service = Mock()
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

        # Step 1: Search for repositories
        search_response = self.client.post(
            "/api/search/repositories",
            json={"query": "python test", "limit": 10}
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert len(search_data["repositories"]) == 1
        assert search_data["repositories"][0]["name"] == "test-repo"

        # Step 2: Validate repository URL
        validate_response = self.client.post(
            "/api/validate/url",
            json={"url": "https://github.com/owner/test-repo"}
        )
        assert validate_response.status_code == 200
        validate_data = validate_response.json()
        assert validate_data["is_valid"] is True

        # Step 3: Get repository details
        repo_response = self.client.get("/api/repositories/owner/test-repo")
        assert repo_response.status_code == 200
        repo_data = repo_response.json()
        assert repo_data["name"] == "test-repo"
        assert repo_data["clone_url"] == "https://github.com/owner/test-repo.git"

        # Step 4: Start indexing
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

        # Step 5: Check indexing status
        status_response = self.client.get("/api/index/status/task-123")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["task_id"] == "task-123"
        assert status_data["status"] == "running"
        assert status_data["percentage"] == 50.0

        # Step 6: Get index stats
        stats_response = self.client.get("/api/index/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["is_indexed"] is True
        assert stats_data["repository_name"] == "owner/test-repo"
        assert stats_data["file_count"] == 100

    @patch('src.api.search.get_github_service')
    @patch('src.api.indexing.get_indexer_service')
    @patch('src.api.chat.get_rag_service')
    def test_complete_chat_workflow(self, mock_get_rag, mock_get_indexer, mock_get_github):
        """Test complete workflow including chat functionality."""
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

        mock_rag_service = Mock()
        mock_rag_service.query.return_value = Mock(
            response="This function calculates the sum of two numbers",
            sources=[],
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
                    content="What does this function do?",
                    timestamp=datetime.utcnow(),
                    sources=None
                ),
                Mock(
                    role="assistant",
                    content="This function calculates the sum of two numbers",
                    timestamp=datetime.utcnow(),
                    sources=[]
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
            last_query="What does this function do?",
            last_response="This function calculates the sum of two numbers",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        mock_get_rag.return_value = mock_rag_service

        # Step 1: Search and select repository
        search_response = self.client.post(
            "/api/search/repositories",
            json={"query": "python test", "limit": 10}
        )
        assert search_response.status_code == 200

        # Step 2: Start indexing
        index_response = self.client.post(
            "/api/index/start",
            json={"repository_url": "https://github.com/owner/test-repo"}
        )
        assert index_response.status_code == 200

        # Step 3: Wait for indexing to complete (simulated)
        stats_response = self.client.get("/api/index/stats")
        assert stats_response.status_code == 200
        assert stats_response.json()["is_indexed"] is True

        # Step 4: Start chat conversation
        chat_response = self.client.post(
            "/api/chat/query",
            json={"query": "What does this function do?"}
        )
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert "function calculates" in chat_data["response"]
        conversation_id = chat_data["conversation_id"]

        # Step 5: Get chat history
        history_response = self.client.get(f"/api/chat/history?conversation_id={conversation_id}")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data["messages"]) == 2

        # Step 6: Get chat context
        context_response = self.client.get(f"/api/chat/context?conversation_id={conversation_id}")
        assert context_response.status_code == 200
        context_data = context_response.json()
        assert context_data["message_count"] == 2
        assert context_data["last_query"] == "What does this function do?"

        # Step 7: Continue conversation
        follow_up_response = self.client.post(
            "/api/chat/query",
            json={
                "query": "Can you show me the implementation?",
                "conversation_id": conversation_id
            }
        )
        assert follow_up_response.status_code == 200

    @patch('src.api.search.get_github_service')
    @patch('src.api.indexing.get_indexer_service')
    def test_error_handling_workflow(self, mock_get_indexer, mock_get_github):
        """Test error handling throughout the workflow."""
        # Setup GitHub service to return error
        mock_github_service = Mock()
        mock_github_service.search_repositories.side_effect = ValueError("GitHub API error")
        mock_get_github.return_value = mock_github_service

        # Test search error
        search_response = self.client.post(
            "/api/search/repositories",
            json={"query": "python test", "limit": 10}
        )
        assert search_response.status_code == 500

        # Setup indexer service to return error
        mock_indexer_service = Mock()
        mock_indexer_service.start_indexing.side_effect = Exception("Indexing error")
        mock_get_indexer.return_value = mock_indexer_service

        # Test indexing error
        index_response = self.client.post(
            "/api/index/start",
            json={"repository_url": "https://github.com/owner/test-repo"}
        )
        assert index_response.status_code == 500

    @patch('src.api.search.get_github_service')
    @patch('src.api.indexing.get_indexer_service')
    def test_concurrent_operations(self, mock_get_indexer, mock_get_github):
        """Test concurrent operations on the same repository."""
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

        # Test concurrent search requests
        import threading
        import time

        results = []

        def make_search_request():
            response = self.client.post(
                "/api/search/repositories",
                json={"query": "python test", "limit": 10}
            )
            results.append(response.status_code)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_search_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5

    @patch('src.api.search.get_github_service')
    @patch('src.api.indexing.get_indexer_service')
    def test_large_repository_handling(self, mock_get_indexer, mock_get_github):
        """Test handling of large repositories."""
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
