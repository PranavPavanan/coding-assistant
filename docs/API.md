# API Documentation

## Base URL

```
http://localhost:8000/api
```

## Authentication

Currently, no authentication is required for API endpoints. GitHub API access uses either anonymous requests or a GitHub token configured in the backend's environment variables.

## Endpoints

### Health Check

Check if the API is running and healthy.

**Endpoint:** `GET /api/health`

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "message": "Backend is running"
}
```

---

### Search Repositories

Search for GitHub repositories by keyword.

**Endpoint:** `POST /api/search/repositories`

**Request Body:**
```json
{
  "query": "string",      // Required: search query
  "limit": 10             // Optional: max results (default: 10)
}
```

**Response:** `200 OK`
```json
{
  "repositories": [
    {
      "id": "string",
      "name": "string",
      "full_name": "string",
      "description": "string | null",
      "html_url": "string",
      "stars": 0,
      "language": "string | null",
      "owner": "string"
    }
  ],
  "total_count": 0
}
```

**Error Responses:**
- `422 Unprocessable Entity`: Missing or invalid query parameter

---

### Validate Repository URL

Validate if a GitHub repository URL is accessible.

**Endpoint:** `POST /api/validate/url`

**Request Body:**
```json
{
  "url": "https://github.com/owner/repo"  // Required
}
```

**Response:** `200 OK`
```json
{
  "is_valid": true,
  "repository": {
    "id": "string",
    "name": "string",
    "full_name": "string",
    "description": "string | null",
    "html_url": "string",
    "stars": 0,
    "language": "string | null",
    "owner": "string"
  },
  "error": null
}
```

**Invalid URL Response:** `200 OK`
```json
{
  "is_valid": false,
  "repository": null,
  "error": "Repository not found or not accessible"
}
```

---

### Get Repository Details

Get detailed information about a specific repository.

**Endpoint:** `GET /api/repositories/{owner}/{repo}`

**Path Parameters:**
- `owner` (string): Repository owner username
- `repo` (string): Repository name

**Response:** `200 OK`
```json
{
  "id": "string",
  "name": "string",
  "full_name": "string",
  "description": "string | null",
  "html_url": "string",
  "stars": 0,
  "language": "string | null",
  "owner": "string"
}
```

**Error Responses:**
- `404 Not Found`: Repository doesn't exist or isn't accessible

---

### Start Indexing

Begin indexing a GitHub repository for semantic search.

**Endpoint:** `POST /api/index/start`

**Request Body:**
```json
{
  "repository_url": "https://github.com/owner/repo"  // Required
}
```

**Response:** `200 OK`
```json
{
  "task_id": "string",
  "status": "pending" | "running",
  "progress": {
    "files_processed": 0,
    "total_files": 0,
    "percentage": 0.0
  },
  "repository_url": "string",
  "error": null
}
```

**Error Responses:**
- `422 Unprocessable Entity`: Invalid or missing repository URL
- `400 Bad Request`: Repository already being indexed

---

### Get Indexing Status

Check the progress of an indexing task.

**Endpoint:** `GET /api/index/status/{task_id}`

**Path Parameters:**
- `task_id` (string): The task ID returned from start indexing

**Response:** `200 OK`
```json
{
  "task_id": "string",
  "status": "pending" | "running" | "completed" | "failed" | "cancelled",
  "progress": {
    "files_processed": 50,
    "total_files": 100,
    "percentage": 50.0
  },
  "repository_url": "string",
  "error": "string | null"
}
```

**Error Responses:**
- `404 Not Found`: Task ID doesn't exist

---

### Get Index Statistics

Get statistics about the currently indexed repository.

**Endpoint:** `GET /api/index/stats`

**Response:** `200 OK`
```json
{
  "is_indexed": true,
  "repository_name": "owner/repo",
  "file_count": 150,
  "vector_count": 1500,
  "last_updated": "2025-10-07T10:00:00Z"
}
```

**No Index Response:** `200 OK`
```json
{
  "is_indexed": false,
  "repository_name": null,
  "file_count": 0,
  "vector_count": 0,
  "last_updated": null
}
```

---

### Clear Index

Clear the currently indexed repository and all associated data.

**Endpoint:** `DELETE /api/index/current`

**Response:** `200 OK`
```json
{
  "message": "Index cleared successfully"
}
```

---

### Chat Query

Ask a question about the indexed repository code.

**Endpoint:** `POST /api/chat/query`

**Request Body:**
```json
{
  "query": "string",                    // Required: user's question
  "conversation_id": "string | null"    // Optional: for continuing a conversation
}
```

**Response:** `200 OK`
```json
{
  "answer": "string",                   // AI-generated answer
  "sources": [                          // Relevant code snippets
    {
      "file_path": "string",
      "start_line": 10,
      "end_line": 20,
      "content": "string",
      "relevance_score": 0.95
    }
  ],
  "conversation_id": "string"           // ID for this conversation
}
```

**Error Responses:**
- `400 Bad Request`: No repository indexed
- `422 Unprocessable Entity`: Missing query parameter

---

### Get Chat History

Retrieve the message history for a conversation.

**Endpoint:** `GET /api/chat/history`

**Query Parameters:**
- `conversation_id` (string, optional): Filter by conversation ID

**Response:** `200 OK`
```json
[
  {
    "role": "user" | "assistant",
    "content": "string",
    "timestamp": "2025-10-07T10:00:00Z",
    "sources": [...]  // Only present for assistant messages
  }
]
```

---

### Get Conversation Context

Get context information about a conversation.

**Endpoint:** `GET /api/chat/context`

**Query Parameters:**
- `conversation_id` (string, optional): The conversation to get context for

**Response:** `200 OK`
```json
{
  "conversation_id": "string | null",
  "message_count": 10,
  "is_indexed": true,
  "repository_name": "owner/repo"
}
```

---

### Clear Chat History

Delete all conversation history.

**Endpoint:** `DELETE /api/chat/history`

**Response:** `200 OK`
```json
{
  "message": "Chat history cleared successfully"
}
```

---

## WebSocket Endpoints

### General WebSocket Connection

Connect to receive system-wide notifications.

**Endpoint:** `WS ws://localhost:8000/ws`

**Messages:**
```json
{
  "type": "echo",
  "message": "..."
}
```

---

### Task-Specific WebSocket

Connect to receive real-time updates for a specific indexing task.

**Endpoint:** `WS ws://localhost:8000/ws/{task_id}`

**Messages:**
```json
{
  "type": "indexing_progress",
  "task_id": "string",
  "status": "running",
  "progress": {
    "files_processed": 50,
    "total_files": 100,
    "percentage": 50.0
  }
}
```

**Client Messages:**
```json
"ping"  // Sends heartbeat, receives {"type": "pong"}
```

---

## Error Responses

All endpoints may return these common error responses:

### 400 Bad Request
```json
{
  "detail": "Error description"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. GitHub API calls are subject to GitHub's rate limits:
- **Unauthenticated**: 60 requests/hour
- **Authenticated** (with token): 5,000 requests/hour

---

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide:
- Interactive API explorer
- Request/response examples
- Schema definitions
- Try-it-out functionality

---

## SDK / Client Libraries

### JavaScript/TypeScript

The frontend includes a complete API client in `frontend/src/services/api.ts`:

```typescript
import { apiClient } from '@/services/api'

// Search repositories
const results = await apiClient.searchRepositories('python web framework')

// Start indexing
const task = await apiClient.startIndexing('https://github.com/owner/repo')

// Query code
const response = await apiClient.chatQuery('What does main do?')
```

### Python

Use `requests` or `httpx`:

```python
import requests

# Search repositories
response = requests.post(
    'http://localhost:8000/api/search/repositories',
    json={'query': 'python web framework', 'limit': 10}
)
repositories = response.json()

# Start indexing
response = requests.post(
    'http://localhost:8000/api/index/start',
    json={'repository_url': 'https://github.com/owner/repo'}
)
task = response.json()
```

---

## Changelog

### Version 0.1.0 (2025-10-07)
- Initial API release
- All core endpoints implemented
- WebSocket support for real-time updates
- Swagger/ReDoc documentation
