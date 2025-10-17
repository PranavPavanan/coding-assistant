"""RAG (Retrieval-Augmented Generation) pipeline service."""
import json
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import time

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("Warning: llama-cpp-python not available. Install with: pip install llama-cpp-python")

from src.models.query import (
    ChatContextResponse,
    ChatHistoryRequest,
    ChatHistoryResponse,
    ChatMessage,
    QueryRequest,
    QueryResponse,
    SourceReference,
)
from src.config import settings


class RAGService:
    """Service for RAG-powered code querying."""

    def __init__(
        self,
        vector_store_path: Optional[str] = None,
        model_path: Optional[str] = None,
    ):
        """
        Initialize RAG service.

        Args:
            vector_store_path: Path to FAISS vector store
            model_path: Path to LLM model (CodeLlama)
        """
        self.vector_store_path = vector_store_path
        self.model_path = model_path

        # In-memory conversation storage (MVP - should use database in production)
        self.conversations: dict[str, list[ChatMessage]] = {}
        
        # Response cache for common queries
        self.response_cache = {}
        self.cache_max_size = 100

        # Flag to indicate if index is loaded
        self.is_initialized = False

        # Placeholder for vector store and model
        self.vector_store = None
        self.model = None
        self.embeddings = None

    async def initialize(self):
        """
        Initialize vector store and LLM model.

        Returns:
            True if initialization successful
        """
        try:
            model_path = settings.get_model_path()
            # Loads: backend/models/codellama-7b-python-ai-assistant.F16.gguf
            
            # Check if llama-cpp-python is available
            if not LLAMA_AVAILABLE:
                print(f"ERROR: llama-cpp-python not installed")
                print("   Install with: pip install llama-cpp-python")
                self.is_initialized = False
                return False
            
            # Check if model path is configured
            if not model_path:
                print(f"ERROR: MODEL_PATH not configured")
                print("   Set MODEL_PATH in .env file")
                self.is_initialized = False
                return False
            
            # Check if model file exists
            model_file = Path(model_path)
            if not model_file.exists():
                print(f"ERROR: Model file not found at {model_path}")
                print("   Download CodeLlama GGUF model and place in backend/models/ directory")
                self.is_initialized = False
                return False
            
            print(f"Loading CodeLlama model from {model_path}...")
            print("This may take a few minutes on first load...")
            
            # Load the model with minimal settings first
            self.model = Llama(
                model_path=str(model_file),
                n_ctx=2048,  # Smaller context window
                n_threads=2,  # Fewer threads
                n_gpu_layers=0,  # CPU only
                verbose=True,  # Enable verbose for debugging
            )
            
            print("SUCCESS: CodeLlama model loaded successfully!")

            # TODO: Load FAISS index
            # TODO: Load sentence-transformers for embeddings

            self.is_initialized = True
            return True
        except Exception as e:
            error_msg = str(e)
            print(f"ERROR: RAG initialization failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            
            # Provide specific guidance for common errors
            if "key not found in model: tokenizer.ggml.tokens" in error_msg:
                print("   This appears to be a LoRA adapter model that requires a base model.")
                print("   Solution: Download a base CodeLlama model and merge with this adapter.")
                print("   Alternative: Use a complete GGUF model instead of an adapter.")
            elif "failed to load model" in error_msg:
                print("   The model file may be corrupted or incompatible.")
                print("   Solution: Re-download the model file or try a different model.")
            else:
                print(f"   Error details: {error_msg}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
            
            self.is_initialized = False
            return False

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a query using RAG pipeline.

        Args:
            request: Query request with question and optional context

        Returns:
            QueryResponse with answer and sources
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{request.query.lower().strip()}:{request.max_sources or 5}"
        if cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key]
            print(f"Cache hit for query: {request.query[:50]}...")
            return cached_response
        
        # Generate or use provided conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Add user message to conversation history
        user_message = ChatMessage(
            role="user",
            content=request.query,
            timestamp=datetime.utcnow(),
        )

        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        self.conversations[conversation_id].append(user_message)

        # Check if model is loaded
        if not self.is_initialized or self.model is None:
            error_msg = "RAG service not initialized. Model failed to load during startup."
            print(f"ERROR: {error_msg}")
            
            # Create error response
            answer = f"Error: {error_msg}\n\nPlease check the server logs for initialization errors and restart the server after fixing the issues."
            sources = []
            model = "error - model not loaded"
        else:
            # Use actual CodeLlama model with basic retrieval from indexed content
            # Retrieve relevant content from indexed files
            retrieved_content, sources = self._retrieve_relevant_content(request.query)
            
            # Generate response using CodeLlama with retrieved context
            answer = self.generate_response(request.query, retrieved_content, "")
            model = "codellama-7b"

        # Create assistant message
        assistant_message = ChatMessage(
            role="assistant",
            content=answer,
            timestamp=datetime.utcnow(),
            sources=sources,
        )
        self.conversations[conversation_id].append(assistant_message)

        processing_time = time.time() - start_time

        # Create response
        response = QueryResponse(
            response=answer,
            sources=sources,
            conversation_id=conversation_id,
            model=model,
        )
        
        # Cache the response (with size limit)
        if len(self.response_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]
        
        self.response_cache[cache_key] = response
        print(f"Response cached for query: {request.query[:50]}...")
        
        return response
    
    
    def _build_conversation_context(self, conversation_id: str) -> str:
        """Build context string from conversation history."""
        if conversation_id not in self.conversations:
            return ""
        
        messages = self.conversations[conversation_id]
        # Get last 5 messages for context
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        
        context_parts = []
        for msg in recent_messages:
            role = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)

    def get_chat_history(self, request: ChatHistoryRequest) -> Optional[ChatHistoryResponse]:
        """
        Get conversation history.

        Args:
            request: Chat history request with conversation ID

        Returns:
            ChatHistoryResponse or None if not found
        """
        conversation_id = request.conversation_id

        if conversation_id not in self.conversations:
            return None

        messages = self.conversations[conversation_id]

        # Apply limit if specified
        if request.limit:
            messages = messages[-request.limit :]

        return ChatHistoryResponse(
            conversation_id=conversation_id,
            messages=messages,
            total_messages=len(self.conversations[conversation_id]),
            created_at=messages[0].timestamp if messages else datetime.utcnow(),
        )

    def get_chat_context(self, conversation_id: str) -> Optional[ChatContextResponse]:
        """
        Get conversation context summary.

        Args:
            conversation_id: Conversation identifier

        Returns:
            ChatContextResponse or None if not found
        """
        if conversation_id not in self.conversations:
            return None

        messages = self.conversations[conversation_id]

        # Count messages by role
        user_messages = sum(1 for m in messages if m.role == "user")
        assistant_messages = sum(1 for m in messages if m.role == "assistant")

        # Get last query and response
        last_user_message = next((m for m in reversed(messages) if m.role == "user"), None)
        last_assistant_message = next(
            (m for m in reversed(messages) if m.role == "assistant"), None
        )

        return ChatContextResponse(
            conversation_id=conversation_id,
            message_count=len(messages),
            user_message_count=user_messages,
            assistant_message_count=assistant_messages,
            last_query=last_user_message.content if last_user_message else None,
            last_response=last_assistant_message.content if last_assistant_message else None,
            created_at=messages[0].timestamp if messages else datetime.utcnow(),
            last_updated=messages[-1].timestamp if messages else datetime.utcnow(),
        )

    def clear_history(self, conversation_id: Optional[str] = None) -> dict:
        """
        Clear conversation history.

        Args:
            conversation_id: Optional specific conversation to clear, or None for all

        Returns:
            Dictionary with operation result
        """
        try:
            if conversation_id:
                if conversation_id in self.conversations:
                    del self.conversations[conversation_id]
                    return {
                        "success": True,
                        "message": f"Conversation {conversation_id} cleared",
                    }
                else:
                    return {
                        "success": False,
                        "error": "Conversation not found",
                    }
            else:
                count = len(self.conversations)
                self.conversations.clear()
                return {
                    "success": True,
                    "message": f"Cleared {count} conversations",
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_conversation_history(self, conversation_id: str) -> list[ChatMessage]:
        """
        Get conversation history for a specific conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of chat messages
        """
        return self.conversations.get(conversation_id, [])

    def clear_conversations(self) -> None:
        """Clear all conversations."""
        self.conversations.clear()

    def get_conversation_context(self, conversation_id: str) -> Optional[ChatContextResponse]:
        """
        Get conversation context summary.

        Args:
            conversation_id: Conversation identifier

        Returns:
            ChatContextResponse or None if not found
        """
        if conversation_id not in self.conversations:
            return None

        messages = self.conversations[conversation_id]

        # Count messages by role
        user_messages = sum(1 for m in messages if m.role == "user")
        assistant_messages = sum(1 for m in messages if m.role == "assistant")

        # Get last query and response
        last_user_message = next((m for m in reversed(messages) if m.role == "user"), None)
        last_assistant_message = next(
            (m for m in reversed(messages) if m.role == "assistant"), None
        )

        return ChatContextResponse(
            conversation_id=conversation_id,
            message_count=len(messages),
            user_message_count=user_messages,
            assistant_message_count=assistant_messages,
            last_query=last_user_message.content if last_user_message else None,
            last_response=last_assistant_message.content if last_assistant_message else None,
            created_at=messages[0].timestamp if messages else datetime.utcnow(),
            last_updated=messages[-1].timestamp if messages else datetime.utcnow(),
        )

    def semantic_search(self, query: str, top_k: int = 5) -> list[SourceReference]:
        """
        Perform semantic search on indexed code.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of source references
        """
        # TODO: Implement using FAISS vector search
        # 1. Generate query embedding
        # 2. Search FAISS index
        # 3. Retrieve corresponding code chunks
        # 4. Return as SourceReference objects

        return []

    def keyword_search(self, query: str, top_k: int = 5) -> list[SourceReference]:
        """
        Perform keyword-based search (BM25).

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of source references
        """
        # TODO: Implement using rank-bm25
        # 1. Tokenize query
        # 2. Search BM25 index
        # 3. Retrieve matching code chunks
        # 4. Return as SourceReference objects

        return []

    def hybrid_search(self, query: str, top_k: int = 10) -> list[SourceReference]:
        """
        Perform hybrid search combining semantic and keyword search.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            Combined and reranked source references
        """
        # TODO: Combine semantic_search and keyword_search results
        # 1. Get results from both methods
        # 2. Merge and deduplicate
        # 3. Rerank based on combined scores
        # 4. Return top_k results

        return []

    def generate_response(self, query: str, context: list[SourceReference], conversation_context: str = "") -> str:
        """
        Generate response using LLM with retrieved context.

        Args:
            query: User query
            context: Retrieved source references
            conversation_context: Previous conversation context

        Returns:
            Generated response text
        """
        if not self.model:
            return "Model not loaded"
        
        # Build prompt with system message and context
        system_prompt = """You are an expert code analysis assistant. Your role is to help developers understand codebases by:
- Explaining code functionality clearly and concisely
- Identifying patterns, best practices, and potential issues
- Providing actionable insights and recommendations
- Answering questions about code structure, dependencies, and implementation details

When analyzing code, be specific, accurate, and helpful."""

        # Add retrieved code context if available
        code_context = ""
        if context:
            code_context = "\n\nRelevant Code:\n"
            for src in context[:3]:  # Top 3 most relevant
                if isinstance(src, str):
                    # Handle string content directly
                    code_context += f"\n{src}\n"
                else:
                    # Handle SourceReference objects
                    code_context += f"\nFile: {src.file} (score: {src.score})\n"
                    code_context += f"```\n{src.content}\n```\n"
        
        # Build full prompt with better instructions
        prompt = f"""<s>[INST] <<SYS>>
{system_prompt}

IMPORTANT: When answering technical questions:
1. Be precise with specific values, names, and parameters
2. Quote exact code snippets when available
3. Distinguish between different files and their purposes
4. If you're unsure about specific values, say so rather than guessing
5. Focus on the most relevant information from the source files
<</SYS>>

{code_context}

User Question: {query} [/INST]

Based on the provided source code, please provide a detailed and accurate answer. Include specific values, file names, and implementation details when available.

Answer:"""

        try:
            # Generate response using CodeLlama
            response = self.model(
                prompt,
                max_tokens=256,  # Reduced from 512
                temperature=0.7,
                top_p=0.95,
                stop=["</s>", "[INST]", "<|endoftext|>", "\n\nUser Question:", "\n\nFile:"],
                echo=False,
            )
            
            # Extract the generated text
            generated_text = response["choices"][0]["text"].strip()
            
            # Validate and clean the response
            generated_text = self._validate_response(generated_text, context)
            
            # Fact-check the response against source content
            generated_text = self._fact_check_response(generated_text, context, query)
            return generated_text
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"

    def _retrieve_relevant_content(self, query: str) -> tuple[List[str], List[SourceReference]]:
        """
        Retrieve relevant content from indexed files based on query.
        
        Args:
            query: User query
            
        Returns:
            Tuple of (retrieved_content, sources)
        """
        try:
            # Load the most recent metadata file
            metadata_dir = Path("./storage/metadata")
            if not metadata_dir.exists():
                return [], []
            
            # Find the most recent metadata file
            metadata_files = list(metadata_dir.glob("*.json"))
            if not metadata_files:
                return [], []
            
            # Sort by modification time and get the most recent
            latest_metadata = max(metadata_files, key=lambda f: f.stat().st_mtime)
            
            # Load metadata
            with open(latest_metadata, 'r') as f:
                metadata = json.load(f)
            
            files = metadata.get('files', [])
            if not files:
                return [], []
            
            # Improved keyword-based retrieval with better scoring
            query_lower = query.lower()
            query_words = set(query_lower.split())
            relevant_files = []
            
            # Score files based on query keywords
            for file_info in files:
                file_path = file_info.get('file_path', '')
                language = file_info.get('language', '')
                
                # Calculate relevance score
                score = 0
                
                # High priority: exact keyword matches in file path
                for word in query_words:
                    if word in file_path.lower():
                        score += 8  # Increased from 5
                
                # Medium priority: partial matches in file path
                for word in query_words:
                    if len(word) > 3 and any(word in part for part in file_path.lower().split('_')):
                        score += 5  # Increased from 3
                
                # Boost for exact class/function name matches
                for word in query_words:
                    if word in ['chunker', 'chunking', 'chunk', 'service']:
                        if 'chunker' in file_path.lower():
                            score += 10  # High boost for exact matches
                    elif word in ['embedding', 'model', 'config', 'configuration']:
                        if any(keyword in file_path.lower() for keyword in ['config', 'chunker', 'embedding']):
                            score += 8  # High boost for embedding-related files
                    elif word in ['default', 'parameter', 'setting']:
                        if any(keyword in file_path.lower() for keyword in ['config', 'chunker', 'main']):
                            score += 6  # Boost for configuration files
                
                # Language-specific scoring
                if language:
                    if any(word in language.lower() for word in query_words):
                        score += 2
                    # Boost for common code files
                    if language in ['python', 'javascript', 'typescript']:
                        score += 1
                
                # File type priority
                if file_path.endswith('.md'):  # Documentation files
                    score += 4
                elif file_path.endswith(('.py', '.js', '.ts')):  # Code files
                    score += 2
                elif file_path.endswith(('.txt', '.json', '.yaml', '.yml')):  # Config files
                    score += 1
                
                # Special file names that are often relevant
                special_files = ['readme', 'config', 'main', 'index', 'chunker', 'indexer', 'crawler']
                for special in special_files:
                    if special in file_path.lower():
                        score += 2
                
                # Add content-based scoring if file content is available
                content_score = self._calculate_content_relevance(file_info, query_words)
                score += content_score
                
                # Only include files with meaningful scores
                if score > 0:
                    relevant_files.append((file_info, score))
            
            # Sort by score and take top files
            relevant_files.sort(key=lambda x: x[1], reverse=True)
            top_files = relevant_files[:3]  # Top 3 most relevant files to reduce context
            
            # Read content from the most relevant files
            retrieved_content = []
            sources = []
            
            for file_info, score in top_files:
                file_path = file_info.get('file_path', '')
                
                repo_path = Path("./storage/repositories/web-rag-service")
                full_path = repo_path / file_path
                
                if full_path.exists():
                    try:
                        # Read file content
                        content = full_path.read_text(encoding='utf-8')
                        
                        # Take first 500 characters to avoid context window issues
                        content_preview = content[:500]
                        if len(content) > 500:
                            content_preview += "\n... (truncated)"
                        
                        retrieved_content.append(f"File: {file_path}\n{content_preview}")
                        
                        # Normalize score to 0-1 range (max possible score is around 30)
                        normalized_score = min(score / 30.0, 1.0)
                        
                        sources.append(SourceReference(
                            file=file_path,
                            content=content_preview,
                            score=normalized_score,
                            type="code" if file_path.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.rs', '.go', '.rb', '.php', '.swift', '.kt', '.scala', '.sh', '.bash')) else "doc"
                        ))
                    except Exception as e:
                        print(f"Error reading file {file_path}: {e}")
                        continue
            
            return retrieved_content, sources
            
        except Exception as e:
            print(f"Error retrieving content: {e}")
            return [], []

    def _validate_response(self, response: str, context: List[str]) -> str:
        """
        Validate and clean the generated response for accuracy.
        
        Args:
            response: Generated response text
            context: Retrieved context for validation
            
        Returns:
            Cleaned and validated response
        """
        # Remove common artifacts
        response = response.replace("<|endoftext|>", "")
        response = response.replace("</s>", "")
        response = response.replace("[INST]", "")
        
        # Remove incomplete sentences at the end
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.endswith(('```', '```python', '```json')):
                cleaned_lines.append(line)
        
        # Join lines and clean up
        cleaned_response = '\n'.join(cleaned_lines)
        
        # Remove trailing incomplete sentences
        sentences = cleaned_response.split('. ')
        if len(sentences) > 1 and len(sentences[-1]) < 20:
            cleaned_response = '. '.join(sentences[:-1]) + '.'
        
        return cleaned_response.strip()

    def _calculate_content_relevance(self, file_info: dict, query_words: set) -> int:
        """
        Calculate content-based relevance score by reading file content.
        
        Args:
            file_info: File metadata information
            query_words: Set of query words
            
        Returns:
            Content relevance score
        """
        try:
            file_path = file_info.get('file_path', '')
            repo_path = Path("./storage/repositories/web-rag-service")
            full_path = repo_path / file_path
            
            if not full_path.exists():
                return 0
            
            # Read first 1000 characters for content analysis
            content = full_path.read_text(encoding='utf-8')[:1000].lower()
            
            score = 0
            
            # Check for exact keyword matches in content
            for word in query_words:
                if word in content:
                    score += 3
                    
            # Check for related terms
            related_terms = {
                'embedding': ['sentence', 'transformer', 'model', 'vector', 'embedding'],
                'config': ['config', 'configuration', 'setting', 'default', 'parameter'],
                'chunking': ['chunk', 'chunking', 'split', 'segment', 'token'],
                'model': ['model', 'llm', 'transformer', 'neural', 'ai']
            }
            
            for query_word in query_words:
                if query_word in related_terms:
                    for term in related_terms[query_word]:
                        if term in content:
                            score += 2
            
            # Boost for class/function definitions
            if any(word in content for word in ['class ', 'def ', 'function ']):
                score += 1
                
            # Boost for configuration sections
            if any(section in content for section in ['config', 'settings', 'default', 'parameter']):
                score += 2
                
            return min(score, 10)  # Cap at 10 points
            
        except Exception as e:
            print(f"Error calculating content relevance for {file_path}: {e}")
            return 0

    def _fact_check_response(self, response: str, context: List[SourceReference], query: str) -> str:
        """
        Fact-check the response against source content to improve accuracy.
        
        Args:
            response: Generated response text
            context: Retrieved source references
            query: Original user query
            
        Returns:
            Fact-checked and corrected response
        """
        try:
            # Common fact-checking patterns
            corrections = []
            
            # Check for embedding model references
            if 'embedding' in query.lower() and 'model' in query.lower():
                # Look for actual model names in context
                actual_models = []
                for src in context:
                    if hasattr(src, 'content'):
                        content = src.content.lower()
                        if 'all-minilm' in content:
                            actual_models.append('all-MiniLM-L6-v2')
                        elif 'sentence' in content and 'transformer' in content:
                            actual_models.append('sentence-transformers')
                
                # If response mentions wrong model, add correction
                if actual_models and not any(model.lower() in response.lower() for model in actual_models):
                    corrections.append(f"\n\nNote: Based on the source code, the actual embedding model appears to be: {', '.join(set(actual_models))}")
            
            # Check for configuration file references
            if 'config' in query.lower():
                config_files = [src.file for src in context if 'config' in src.file.lower()]
                if config_files and not any(f in response for f in config_files):
                    corrections.append(f"\n\nConfiguration is found in: {', '.join(config_files)}")
            
            # Check for default values
            if 'default' in query.lower():
                # Look for default values in context
                default_values = []
                for src in context:
                    if hasattr(src, 'content'):
                        content = src.content
                        # Look for common default patterns
                        import re
                        defaults = re.findall(r'default[:\s=]+["\']?([^"\'\s,]+)["\']?', content, re.IGNORECASE)
                        default_values.extend(defaults)
                
                if default_values:
                    unique_defaults = list(set(default_values))[:3]  # Top 3 unique defaults
                    corrections.append(f"\n\nDefault values found in source: {', '.join(unique_defaults)}")
            
            # Add corrections to response if any found
            if corrections:
                response += ''.join(corrections)
            
            return response
            
        except Exception as e:
            print(f"Error in fact-checking: {e}")
            return response


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service(
    vector_store_path: Optional[str] = None,
    model_path: Optional[str] = None,
) -> RAGService:
    """
    Get or create RAG service instance.

    Args:
        vector_store_path: Path to vector store
        model_path: Path to LLM model

    Returns:
        RAGService instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(vector_store_path, model_path)
    return _rag_service
