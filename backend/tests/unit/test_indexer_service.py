"""Unit tests for Indexer service."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from src.services.indexer_service import IndexerService
from src.models.index import (
    IndexStartRequest,
    IndexingStatus,
    IndexProgressInfo,
    IndexStats,
    FileIndexEntry,
)


class TestIndexerService:
    """Test cases for IndexerService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_storage = Path("/tmp/test_storage")
        self.service = IndexerService(str(self.temp_storage))

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up any created directories
        if self.temp_storage.exists():
            import shutil
            shutil.rmtree(self.temp_storage, ignore_errors=True)

    def test_init_creates_directories(self):
        """Test that initialization creates required directories."""
        assert self.service.storage_dir == self.temp_storage
        assert self.service.repos_dir.exists()
        assert self.service.indices_dir.exists()
        assert self.service.metadata_dir.exists()
        assert self.service.active_tasks == {}
        assert self.service.current_task is None

    def test_start_indexing_creates_task(self):
        """Test that starting indexing creates a task."""
        request = IndexStartRequest(
            repository_url="https://github.com/owner/repo",
            branch="main"
        )

        result = self.service.start_indexing(request)

        assert result.task_id is not None
        assert result.status == IndexingStatus.PENDING
        assert result.repository_url == "https://github.com/owner/repo"
        assert result.message == "Indexing task created and queued"
        assert result.estimated_time == 300

        # Check task is stored
        assert result.task_id in self.service.active_tasks
        task = self.service.active_tasks[result.task_id]
        assert task["repository_url"] == "https://github.com/owner/repo"
        assert task["branch"] == "main"
        assert task["status"] == IndexingStatus.RUNNING
        assert self.service.current_task == result.task_id

    def test_start_indexing_with_exception(self):
        """Test starting indexing with exception handling."""
        request = IndexStartRequest(
            repository_url="https://github.com/owner/repo",
            branch="main"
        )

        with patch.object(self.service, 'active_tasks', side_effect=Exception("Test error")):
            result = self.service.start_indexing(request)

        # Should still return a response even with exception
        assert result.task_id is not None
        assert result.status == IndexingStatus.PENDING

    def test_get_indexing_status_existing_task(self):
        """Test getting status for existing task."""
        # Create a task first
        request = IndexStartRequest(
            repository_url="https://github.com/owner/repo",
            branch="main"
        )
        start_result = self.service.start_indexing(request)
        task_id = start_result.task_id

        # Get status
        result = self.service.get_indexing_status(task_id)

        assert result is not None
        assert result.task_id == task_id
        assert result.status == IndexingStatus.RUNNING
        assert result.repository_url == "https://github.com/owner/repo"
        assert result.message == "Indexing in progress"
        assert isinstance(result.progress, IndexProgressInfo)

    def test_get_indexing_status_nonexistent_task(self):
        """Test getting status for non-existent task."""
        result = self.service.get_indexing_status("nonexistent-task-id")
        assert result is None

    def test_get_task_status_alias(self):
        """Test that get_task_status is an alias for get_indexing_status."""
        # Create a task first
        request = IndexStartRequest(
            repository_url="https://github.com/owner/repo",
            branch="main"
        )
        start_result = self.service.start_indexing(request)
        task_id = start_result.task_id

        # Both methods should return the same result
        status1 = self.service.get_indexing_status(task_id)
        status2 = self.service.get_task_status(task_id)

        assert status1 is not None
        assert status2 is not None
        assert status1.task_id == status2.task_id
        assert status1.status == status2.status

    def test_clear_index_success(self):
        """Test successful index clearing."""
        # Create some mock files
        (self.service.indices_dir / "test.faiss").write_text("mock data")
        (self.service.metadata_dir / "test.json").write_text('{"test": "data"}')

        result = self.service.clear_index()

        assert result["success"] is True
        assert result["files_removed"] == 1
        assert result["space_freed"] > 0
        assert result["message"] == "Index cleared successfully"

    def test_clear_index_with_exception(self):
        """Test index clearing with exception."""
        with patch.object(self.service.indices_dir, 'glob', side_effect=Exception("Test error")):
            result = self.service.clear_index()

        assert result["success"] is False
        assert "error" in result
        assert result["message"] == "Failed to clear index"

    def test_get_index_stats_no_index(self):
        """Test getting index stats when no index exists."""
        result = self.service.get_index_stats()

        assert result.is_indexed is False
        assert result.repository_name is None
        assert result.file_count == 0
        assert result.total_size == 0
        assert result.vector_count == 0
        assert result.last_updated is None
        assert result.created_at is None

    def test_get_index_stats_with_index(self):
        """Test getting index stats when index exists."""
        # Create mock index files
        (self.service.indices_dir / "test.faiss").write_text("mock index data")
        
        # Create mock metadata
        metadata = {
            "repository_name": "owner/test-repo",
            "file_count": 100,
            "indexed_at": "2023-01-01T00:00:00",
            "created_at": "2023-01-01T00:00:00"
        }
        (self.service.metadata_dir / "metadata.json").write_text(json.dumps(metadata))

        result = self.service.get_index_stats()

        assert result.is_indexed is True
        assert result.repository_name == "owner/test-repo"
        assert result.file_count == 100
        assert result.total_size > 0
        assert result.vector_count == 1000  # file_count * 10
        assert result.last_updated is not None
        assert result.created_at is not None

    def test_get_index_stats_with_invalid_metadata(self):
        """Test getting index stats with invalid metadata file."""
        # Create mock index files
        (self.service.indices_dir / "test.faiss").write_text("mock index data")
        
        # Create invalid metadata
        (self.service.metadata_dir / "metadata.json").write_text("invalid json")

        result = self.service.get_index_stats()

        assert result.is_indexed is True
        assert result.repository_name is None
        assert result.file_count == 0

    def test_index_file_success(self):
        """Test successful file indexing."""
        # Create a temporary file
        test_file = self.temp_storage / "test.py"
        test_file.write_text("def hello():\n    print('world')")
        
        repo_root = self.temp_storage

        result = self.service.index_file(test_file, repo_root)

        assert result is not None
        assert isinstance(result, FileIndexEntry)
        assert result.file_path == "test.py"
        assert result.language == "python"
        assert result.size > 0
        assert result.chunk_count > 0
        assert result.content_hash is not None
        assert result.indexed_at is not None

    def test_index_file_too_large(self):
        """Test indexing file that's too large."""
        # Create a large file (simulate > 1MB)
        test_file = self.temp_storage / "large.txt"
        with patch.object(test_file, 'stat') as mock_stat:
            mock_stat.return_value.st_size = 2 * 1024 * 1024  # 2MB
            result = self.service.index_file(test_file, self.temp_storage)

        assert result is None

    def test_index_file_binary(self):
        """Test indexing binary file."""
        # Create a binary file
        test_file = self.temp_storage / "binary.bin"
        test_file.write_bytes(b'\x00\x01\x02\x03')
        
        repo_root = self.temp_storage

        result = self.service.index_file(test_file, repo_root)

        assert result is None

    def test_index_file_unicode_error(self):
        """Test indexing file with Unicode decode error."""
        test_file = self.temp_storage / "test.txt"
        test_file.write_bytes(b'\xff\xfe\x00\x00')  # Invalid UTF-8
        
        repo_root = self.temp_storage

        result = self.service.index_file(test_file, repo_root)

        assert result is None

    def test_index_file_exception(self):
        """Test indexing file with general exception."""
        test_file = self.temp_storage / "test.py"
        test_file.write_text("def hello():\n    print('world')")
        
        repo_root = self.temp_storage

        with patch.object(test_file, 'read_text', side_effect=Exception("Read error")):
            result = self.service.index_file(test_file, repo_root)

        assert result is None

    def test_detect_language(self):
        """Test language detection from file extensions."""
        # Test various file extensions
        test_cases = [
            (".py", "python"),
            (".js", "javascript"),
            (".ts", "typescript"),
            (".jsx", "javascript"),
            (".tsx", "typescript"),
            (".java", "java"),
            (".cpp", "cpp"),
            (".c", "c"),
            (".h", "c"),
            (".hpp", "cpp"),
            (".rs", "rust"),
            (".go", "go"),
            (".rb", "ruby"),
            (".php", "php"),
            (".swift", "swift"),
            (".kt", "kotlin"),
            (".scala", "scala"),
            (".sh", "shell"),
            (".bash", "shell"),
            (".md", "markdown"),
            (".json", "json"),
            (".yaml", "yaml"),
            (".yml", "yaml"),
            (".xml", "xml"),
            (".html", "html"),
            (".css", "css"),
            (".scss", "scss"),
            (".sql", "sql"),
            (".unknown", None),
        ]

        for extension, expected_language in test_cases:
            result = self.service._detect_language(extension)
            assert result == expected_language, f"Failed for extension {extension}"

    def test_get_status_message(self):
        """Test status message generation."""
        test_cases = [
            (IndexingStatus.PENDING, "Task is queued and waiting to start"),
            (IndexingStatus.RUNNING, "Indexing in progress"),
            (IndexingStatus.COMPLETED, "Indexing completed successfully"),
            (IndexingStatus.FAILED, "Indexing failed"),
            (IndexingStatus.CANCELLED, "Indexing was cancelled"),
        ]

        for status, expected_message in test_cases:
            result = self.service._get_status_message(status)
            assert result == expected_message

    def test_get_status_message_unknown(self):
        """Test status message for unknown status."""
        # Create a mock status that's not in the mapping
        class UnknownStatus:
            pass
        
        result = self.service._get_status_message(UnknownStatus())
        assert result == "Unknown status"
