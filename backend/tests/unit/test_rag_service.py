"""Unit tests for RAG service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.rag_service import RAGService
from src.models.query import (
    QueryRequest,
    QueryResponse,
    ChatMessage,
    ChatHistoryRequest,
    ChatHistoryResponse,
    ChatContextResponse,
    SourceReference,
)


class TestRAGService:
    """Test cases for RAGService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rag_service = RAGService()
        self.mock_model = Mock()
        self.mock_model.return_value = {
            "choices": [{"text": "This is a test response"}]
        }

    def test_init(self):
        """Test RAG service initialization."""
        service = RAGService(
            vector_store_path="/tmp/vectors",
            model_path="/tmp/model.gguf"
        )
        
        assert service.vector_store_path == "/tmp/vectors"
        assert service.model_path == "/tmp/model.gguf"
        assert service.conversations == {}
        assert service.is_initialized is False
        assert service.vector_store is None
        assert service.model is None
        assert service.embeddings is None

    @patch('src.services.rag_service.LLAMA_AVAILABLE', True)
    @patch('src.services.rag_service.settings')
    @patch('src.services.rag_service.Path')
    def test_initialize_success(self, mock_path, mock_settings):
        """Test successful RAG service initialization."""
        # Setup
        mock_settings.get_model_path.return_value = "/tmp/model.gguf"
        mock_model_file = Mock()
        mock_model_file.exists.return_value = True
        mock_path.return_value = mock_model_file
        
        with patch('src.services.rag_service.Llama') as mock_llama:
            mock_llama.return_value = self.mock_model
            
            # Execute
            result = await self.rag_service.initialize()
            
            # Verify
            assert result is True
            assert self.rag_service.is_initialized is True
            assert self.rag_service.model is not None

    @patch('src.services.rag_service.LLAMA_AVAILABLE', False)
    @patch('src.services.rag_service.settings')
    def test_initialize_llama_not_available(self, mock_settings):
        """Test initialization when llama-cpp-python is not available."""
        mock_settings.get_model_path.return_value = "/tmp/model.gguf"
        
        result = await self.rag_service.initialize()
        
        assert result is False
        assert self.rag_service.is_initialized is False

    @patch('src.services.rag_service.LLAMA_AVAILABLE', True)
    @patch('src.services.rag_service.settings')
    @patch('src.services.rag_service.Path')
    def test_initialize_model_not_found(self, mock_path, mock_settings):
        """Test initialization when model file doesn't exist."""
        mock_settings.get_model_path.return_value = "/tmp/model.gguf"
        mock_model_file = Mock()
        mock_model_file.exists.return_value = False
        mock_path.return_value = mock_model_file
        
        result = await self.rag_service.initialize()
        
        assert result is False
        assert self.rag_service.is_initialized is False

    @patch('src.services.rag_service.LLAMA_AVAILABLE', True)
    @patch('src.services.rag_service.settings')
    def test_initialize_no_model_path(self, mock_settings):
        """Test initialization when no model path is configured."""
        mock_settings.get_model_path.return_value = None
        
        result = await self.rag_service.initialize()
        
        assert result is False
        assert self.rag_service.is_initialized is False

    @patch('src.services.rag_service.LLAMA_AVAILABLE', True)
    @patch('src.services.rag_service.settings')
    @patch('src.services.rag_service.Path')
    def test_initialize_exception(self, mock_path, mock_settings):
        """Test initialization with exception."""
        mock_settings.get_model_path.return_value = "/tmp/model.gguf"
        mock_model_file = Mock()
        mock_model_file.exists.return_value = True
        mock_path.return_value = mock_model_file
        
        with patch('src.services.rag_service.Llama', side_effect=Exception("Model load error")):
            result = await self.rag_service.initialize()
            
            assert result is False
            assert self.rag_service.is_initialized is False

    def test_query_without_model(self):
        """Test query when model is not initialized."""
        request = QueryRequest(query="What does this code do?")
        
        result = self.rag_service.query(request)
        
        assert isinstance(result, QueryResponse)
        assert "mock response" in result.response.lower()
        assert result.confidence == 0.0
        assert result.model_used == "codellama-7b (mock - model not loaded)"
        assert result.conversation_id is not None

    def test_query_with_conversation_id(self):
        """Test query with provided conversation ID."""
        conversation_id = "test-conversation-123"
        request = QueryRequest(
            query="What does this code do?",
            conversation_id=conversation_id
        )
        
        result = self.rag_service.query(request)
        
        assert result.conversation_id == conversation_id
        assert conversation_id in self.rag_service.conversations

    def test_query_without_conversation_id(self):
        """Test query without provided conversation ID."""
        request = QueryRequest(query="What does this code do?")
        
        result = self.rag_service.query(request)
        
        assert result.conversation_id is not None
        assert result.conversation_id in self.rag_service.conversations

    def test_query_adds_messages_to_conversation(self):
        """Test that query adds messages to conversation history."""
        request = QueryRequest(query="What does this code do?")
        
        result = self.rag_service.query(request)
        conversation_id = result.conversation_id
        
        # Check conversation has both user and assistant messages
        messages = self.rag_service.conversations[conversation_id]
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "What does this code do?"
        assert messages[1].role == "assistant"
        assert messages[1].content == result.response

    def test_query_with_model(self):
        """Test query with initialized model."""
        # Setup
        self.rag_service.model = self.mock_model
        self.rag_service.is_initialized = True
        
        request = QueryRequest(query="What does this code do?")
        
        result = self.rag_service.query(request)
        
        assert isinstance(result, QueryResponse)
        assert result.model_used == "codellama-7b"
        assert result.confidence == 0.85
        assert result.processing_time > 0

    def test_generate_mock_response(self):
        """Test mock response generation."""
        query = "What does this function do?"
        result = self.rag_service._generate_mock_response(query)
        
        assert "What does this function do?" in result
        assert "mock response" in result.lower()
        assert "CodeLlama model is not loaded" in result

    def test_generate_mock_sources(self):
        """Test mock source generation."""
        result = self.rag_service._generate_mock_sources()
        
        assert len(result) == 1
        assert isinstance(result[0], SourceReference)
        assert result[0].file == "src/example.py"
        assert result[0].line_start == 10
        assert result[0].line_end == 25
        assert result[0].score == 0.95

    def test_build_conversation_context(self):
        """Test conversation context building."""
        conversation_id = "test-conversation"
        self.rag_service.conversations[conversation_id] = [
            ChatMessage(role="user", content="First question", timestamp=datetime.utcnow()),
            ChatMessage(role="assistant", content="First answer", timestamp=datetime.utcnow()),
            ChatMessage(role="user", content="Second question", timestamp=datetime.utcnow()),
            ChatMessage(role="assistant", content="Second answer", timestamp=datetime.utcnow()),
        ]
        
        result = self.rag_service._build_conversation_context(conversation_id)
        
        assert "User: First question" in result
        assert "Assistant: First answer" in result
        assert "User: Second question" in result
        assert "Assistant: Second answer" in result

    def test_build_conversation_context_nonexistent(self):
        """Test conversation context building for non-existent conversation."""
        result = self.rag_service._build_conversation_context("nonexistent")
        assert result == ""

    def test_build_conversation_context_limits_messages(self):
        """Test that conversation context limits to last 5 messages."""
        conversation_id = "test-conversation"
        # Create 10 messages
        messages = []
        for i in range(10):
            messages.append(ChatMessage(
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                timestamp=datetime.utcnow()
            ))
        self.rag_service.conversations[conversation_id] = messages
        
        result = self.rag_service._build_conversation_context(conversation_id)
        
        # Should only contain last 5 messages
        assert "Message 0" not in result  # First message should not be included
        assert "Message 5" in result     # Last 5 messages should be included

    def test_get_chat_history_success(self):
        """Test successful chat history retrieval."""
        conversation_id = "test-conversation"
        messages = [
            ChatMessage(role="user", content="Question 1", timestamp=datetime.utcnow()),
            ChatMessage(role="assistant", content="Answer 1", timestamp=datetime.utcnow()),
        ]
        self.rag_service.conversations[conversation_id] = messages
        
        request = ChatHistoryRequest(conversation_id=conversation_id)
        result = self.rag_service.get_chat_history(request)
        
        assert result is not None
        assert isinstance(result, ChatHistoryResponse)
        assert result.conversation_id == conversation_id
        assert len(result.messages) == 2
        assert result.total_messages == 2

    def test_get_chat_history_with_limit(self):
        """Test chat history retrieval with limit."""
        conversation_id = "test-conversation"
        messages = [
            ChatMessage(role="user", content=f"Question {i}", timestamp=datetime.utcnow())
            for i in range(10)
        ]
        self.rag_service.conversations[conversation_id] = messages
        
        request = ChatHistoryRequest(conversation_id=conversation_id, limit=3)
        result = self.rag_service.get_chat_history(request)
        
        assert len(result.messages) == 3
        assert result.total_messages == 10

    def test_get_chat_history_nonexistent(self):
        """Test chat history retrieval for non-existent conversation."""
        request = ChatHistoryRequest(conversation_id="nonexistent")
        result = self.rag_service.get_chat_history(request)
        
        assert result is None

    def test_get_chat_context_success(self):
        """Test successful chat context retrieval."""
        conversation_id = "test-conversation"
        messages = [
            ChatMessage(role="user", content="Question 1", timestamp=datetime.utcnow()),
            ChatMessage(role="assistant", content="Answer 1", timestamp=datetime.utcnow()),
            ChatMessage(role="user", content="Question 2", timestamp=datetime.utcnow()),
        ]
        self.rag_service.conversations[conversation_id] = messages
        
        result = self.rag_service.get_chat_context(conversation_id)
        
        assert result is not None
        assert isinstance(result, ChatContextResponse)
        assert result.conversation_id == conversation_id
        assert result.message_count == 3
        assert result.user_message_count == 2
        assert result.assistant_message_count == 1
        assert result.last_query == "Question 2"
        assert result.last_response == "Answer 1"

    def test_get_chat_context_nonexistent(self):
        """Test chat context retrieval for non-existent conversation."""
        result = self.rag_service.get_chat_context("nonexistent")
        assert result is None

    def test_clear_history_specific_conversation(self):
        """Test clearing specific conversation history."""
        conversation_id = "test-conversation"
        self.rag_service.conversations[conversation_id] = [
            ChatMessage(role="user", content="Test", timestamp=datetime.utcnow())
        ]
        
        result = self.rag_service.clear_history(conversation_id)
        
        assert result["success"] is True
        assert conversation_id not in self.rag_service.conversations

    def test_clear_history_nonexistent_conversation(self):
        """Test clearing non-existent conversation history."""
        result = self.rag_service.clear_history("nonexistent")
        
        assert result["success"] is False
        assert "error" in result

    def test_clear_history_all_conversations(self):
        """Test clearing all conversation history."""
        # Add some conversations
        self.rag_service.conversations["conv1"] = [ChatMessage(role="user", content="Test1", timestamp=datetime.utcnow())]
        self.rag_service.conversations["conv2"] = [ChatMessage(role="user", content="Test2", timestamp=datetime.utcnow())]
        
        result = self.rag_service.clear_history()
        
        assert result["success"] is True
        assert result["message"] == "Cleared 2 conversations"
        assert len(self.rag_service.conversations) == 0

    def test_clear_history_exception(self):
        """Test clearing history with exception."""
        with patch.object(self.rag_service, 'conversations', side_effect=Exception("Test error")):
            result = self.rag_service.clear_history()
            
            assert result["success"] is False
            assert "error" in result

    def test_get_conversation_history(self):
        """Test getting conversation history."""
        conversation_id = "test-conversation"
        messages = [ChatMessage(role="user", content="Test", timestamp=datetime.utcnow())]
        self.rag_service.conversations[conversation_id] = messages
        
        result = self.rag_service.get_conversation_history(conversation_id)
        
        assert result == messages

    def test_get_conversation_history_nonexistent(self):
        """Test getting conversation history for non-existent conversation."""
        result = self.rag_service.get_conversation_history("nonexistent")
        assert result == []

    def test_clear_conversations(self):
        """Test clearing all conversations."""
        self.rag_service.conversations["conv1"] = [ChatMessage(role="user", content="Test", timestamp=datetime.utcnow())]
        self.rag_service.conversations["conv2"] = [ChatMessage(role="user", content="Test", timestamp=datetime.utcnow())]
        
        self.rag_service.clear_conversations()
        
        assert len(self.rag_service.conversations) == 0

    def test_semantic_search(self):
        """Test semantic search (placeholder implementation)."""
        result = self.rag_service.semantic_search("test query", top_k=5)
        assert result == []

    def test_keyword_search(self):
        """Test keyword search (placeholder implementation)."""
        result = self.rag_service.keyword_search("test query", top_k=5)
        assert result == []

    def test_hybrid_search(self):
        """Test hybrid search (placeholder implementation)."""
        result = self.rag_service.hybrid_search("test query", top_k=10)
        assert result == []

    def test_generate_response_with_model(self):
        """Test response generation with model."""
        self.rag_service.model = self.mock_model
        
        result = self.rag_service.generate_response("test query", [], "")
        
        assert result == "This is a test response"
        self.mock_model.assert_called_once()

    def test_generate_response_without_model(self):
        """Test response generation without model."""
        result = self.rag_service.generate_response("test query", [], "")
        
        assert result == "Model not loaded"

    def test_generate_response_with_context(self):
        """Test response generation with context."""
        self.rag_service.model = self.mock_model
        context = [
            SourceReference(
                file_path="test.py",
                start_line=1,
                end_line=10,
                content="def test():\n    pass",
                score=0.9
            )
        ]
        
        result = self.rag_service.generate_response("test query", context, "")
        
        assert result == "This is a test response"
        # Verify the model was called with context
        call_args = self.mock_model.call_args[0][0]
        assert "test.py" in call_args
        assert "def test():" in call_args

    def test_generate_response_exception(self):
        """Test response generation with exception."""
        self.rag_service.model = Mock()
        self.rag_service.model.side_effect = Exception("Model error")
        
        result = self.rag_service.generate_response("test query", [], "")
        
        assert "Error generating response" in result
