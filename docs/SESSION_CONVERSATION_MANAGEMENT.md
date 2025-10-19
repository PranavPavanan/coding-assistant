# Session & Conversation Management Feature

## Overview

The Session & Conversation Management feature provides a hierarchical chat system that allows users to manage multiple conversation threads within a single session. This enables contextual awareness within conversations while maintaining the ability to create new chat threads for different topics.

## Architecture

### Hierarchical Structure

```
Session (Root)
├── Conversation 1 (Chat Thread)
│   ├── Message 1
│   ├── Message 2
│   └── ...
├── Conversation 2 (Chat Thread)
│   ├── Message 1
│   ├── Message 2
│   └── ...
└── Conversation N (Chat Thread)
    └── ...
```

### Key Concepts

- **Session**: A container that groups related conversations together
- **Conversation**: An individual chat thread with its own message history
- **Contextual Awareness**: Each conversation maintains full context of its message history
- **Auto-ID Generation**: System automatically generates session and conversation IDs

## Backend Implementation

### Data Models

#### SessionInfo
```typescript
interface SessionInfo {
  session_id: string
  created_at: datetime
  last_activity: datetime
  conversation_count: number
  total_messages: number
}
```

#### ConversationInfo
```typescript
interface ConversationInfo {
  conversation_id: string
  session_id: string
  created_at: datetime
  last_activity: datetime
  message_count: number
}
```

#### QueryRequest (Enhanced)
```typescript
interface QueryRequest {
  query: string
  conversation_id?: string  // Auto-generated if not provided
  session_id?: string       // Auto-generated if not provided
  max_sources?: number
  temperature?: number
}
```

#### QueryResponse (Enhanced)
```typescript
interface QueryResponse {
  response: string
  sources: SourceReference[]
  conversation_id: string   // Always returned
  session_id: string        // Always returned
  timestamp: datetime
  model: string
  tokens_used?: number
}
```

### API Endpoints

#### Core Chat Endpoints

**POST /chat/query**
- Processes chat queries with automatic session/conversation management
- Auto-generates IDs if not provided
- Maintains contextual awareness within conversations

**GET /chat/history**
- Retrieves conversation history
- Parameters: `conversation_id`, `limit`

**GET /chat/context**
- Gets conversation context summary
- Parameters: `conversation_id`

**DELETE /chat/history**
- Clears specific conversation or all conversations
- Parameters: `conversation_id` (optional)

#### Session Management Endpoints

**POST /chat/session/clear**
- Clears session data and all associated conversations
- Body: `{ session_id: string, clear_all: boolean }`

**GET /chat/session/{session_id}**
- Retrieves session information
- Returns: `SessionInfo`

**GET /chat/session/{session_id}/conversations**
- Lists all conversations in a session
- Returns: `ConversationInfo[]`

**GET /chat/conversation/{conversation_id}**
- Gets conversation information
- Returns: `ConversationInfo`

**GET /chat/sessions**
- Lists all active sessions
- Returns: `SessionInfo[]`

### RAGService Enhancements

#### Session Management
```python
class RAGService:
    def __init__(self):
        self.sessions: dict[str, SessionInfo] = {}
        self.conversations: dict[str, list[ChatMessage]] = {}
        self.session_conversations: dict[str, set[str]] = {}
```

#### Key Methods
- `clear_session(request: SessionClearRequest) -> SessionClearResponse`
- `get_session_info(session_id: str) -> Optional[SessionInfo]`
- `get_conversation_info(conversation_id: str) -> Optional[ConversationInfo]`
- `list_sessions() -> list[SessionInfo]`
- `list_conversations_in_session(session_id: str) -> list[ConversationInfo]`

#### Context Awareness Fix
The system now properly builds conversation context and passes it to the LLM:

```python
# Build conversation context for contextual awareness
conversation_context = self._build_conversation_context(conversation_id)

# Generate response with full context
answer = self.generate_response(request.query, retrieved_content, conversation_context)
```

## Frontend Implementation

### State Management (Zustand Store)

#### Enhanced Interfaces
```typescript
interface Conversation {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: string
  lastActivity: string
}

interface Session {
  id: string
  conversations: Conversation[]
  createdAt: string
  lastActivity: string
}
```

#### Store Actions
- `createNewConversation()` - Creates new conversation in current session
- `switchToConversation(id: string)` - Switches to specific conversation
- `addConversation(conversation: Conversation)` - Adds conversation to store
- `updateConversation(id: string, updates: Partial<Conversation>)` - Updates conversation
- `clearAllConversations()` - Clears all conversations and session

### UI Components

#### ConversationTabs Component
- **Purpose**: Displays conversation tabs for switching between chats
- **Features**:
  - Tab switching with visual indicators
  - Close tabs (except last one)
  - Auto-generated conversation titles
  - Responsive horizontal scrolling
  - New Chat button

#### Enhanced ChatInterface
- **Conversation Management**: Integrated conversation tabs
- **New Chat Button**: Creates new conversations
- **Context Awareness**: Maintains conversation context
- **Auto-Title Generation**: Updates titles based on first message

### API Integration

#### Enhanced API Client
```typescript
class ApiClient {
  // Enhanced chat query with session support
  async chatQuery(query: string, conversationId?: string, sessionId?: string)
  
  // Session management
  async clearSession(sessionId: string, clearAll: boolean = false)
  async getSessionInfo(sessionId: string)
  async getConversationInfo(conversationId: string)
  async listConversationsInSession(sessionId: string)
  async listSessions()
}
```

## Usage Examples

### Backend API Usage

#### First Query (Auto-Generate Everything)
```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "what method is used for ranking?"}'
```

**Response:**
```json
{
  "response": "The ranking method used is...",
  "conversation_id": "uuid-1",
  "session_id": "uuid-2",
  "sources": [...],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Second Query (Context Aware)
```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "can you explain alternate methods?",
    "conversation_id": "uuid-1",
    "session_id": "uuid-2"
  }'
```

#### New Conversation (Same Session)
```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "what are the configuration options?",
    "session_id": "uuid-2"
  }'
```

#### Clear Session
```bash
curl -X POST http://localhost:8000/api/chat/session/clear \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid-2", "clear_all": false}'
```

### Frontend Usage

#### Creating a New Chat
```typescript
// User clicks "New Chat" button
const handleNewChat = () => {
  createNewConversation() // Creates new conversation in same session
}
```

#### Switching Conversations
```typescript
// User clicks on a conversation tab
const handleTabClick = (conversationId: string) => {
  switchToConversation(conversationId) // Switches to that conversation
}
```

#### Sending Messages
```typescript
// Enhanced message sending with session support
const response = await apiClient.chatQuery(
  input, 
  conversationId || undefined, 
  sessionId || undefined
)
```

## Key Benefits

### 1. **Contextual Awareness**
- Each conversation maintains full context of its message history
- LLM receives conversation context for better responses
- No context loss when switching between conversations

### 2. **Organized Chat Management**
- Multiple conversation threads for different topics
- Easy switching between conversations via tabs
- Clear visual separation of different chat topics

### 3. **Session Continuity**
- All conversations within a session share the same session_id
- Easy session management and cleanup
- Hierarchical organization of related conversations

### 4. **User Experience**
- Intuitive tab-based interface
- Auto-generated conversation titles
- One-click new chat creation
- Easy conversation switching and management

### 5. **Scalability**
- Support for unlimited conversations per session
- Efficient memory management
- Easy session cleanup and management

## Technical Implementation Details

### Context Building
The system builds conversation context by:
1. Retrieving last 5 messages from conversation history
2. Formatting them as "User: ..." and "Assistant: ..."
3. Passing context to LLM for contextual awareness

### Auto-ID Generation
- **Session ID**: Generated on first query if not provided
- **Conversation ID**: Generated on first query if not provided
- **Persistence**: IDs are returned in response for client storage

### Memory Management
- **In-memory storage**: Currently uses in-memory dictionaries
- **Production ready**: Designed for easy migration to database
- **Cleanup**: Session clearing removes all associated data

### Error Handling
- **Graceful degradation**: System works even if context building fails
- **Validation**: Proper validation of session and conversation IDs
- **Error responses**: Clear error messages for debugging

## Testing

### Backend Testing
- Test script: `backend/test_session_conversation.py`
- Tests complete session/conversation flow
- Validates API endpoints and responses

### Frontend Testing
- Demo file: `frontend/test_conversation_ui.html`
- Interactive demo of conversation management
- Visual demonstration of tab functionality

## Future Enhancements

### Planned Features
1. **Session TTL**: Automatic session cleanup after inactivity
2. **Database Storage**: Migration from in-memory to persistent storage
3. **Conversation Search**: Search within conversation history
4. **Export/Import**: Export conversations for backup
5. **Collaborative Sessions**: Share sessions between users

### Performance Optimizations
1. **Lazy Loading**: Load conversation history on demand
2. **Pagination**: Paginate long conversation histories
3. **Caching**: Cache frequently accessed conversations
4. **Compression**: Compress old conversation data

## Migration Guide

### From Single Conversation to Multi-Conversation

#### Backend Changes
1. Update API calls to include `session_id` parameter
2. Handle conversation context in response generation
3. Implement session management endpoints

#### Frontend Changes
1. Update state management to support multiple conversations
2. Add conversation tabs component
3. Update API client to support session management
4. Modify chat interface for conversation switching

### Breaking Changes
- `QueryResponse` now requires `session_id` field
- New required parameters in some API endpoints
- Updated state management structure

## Troubleshooting

### Common Issues

#### Context Not Working
- **Cause**: Conversation context not being passed to LLM
- **Solution**: Ensure `_build_conversation_context()` is called and passed to `generate_response()`

#### Session Not Persisting
- **Cause**: Session ID not being stored or passed correctly
- **Solution**: Check that `session_id` is being stored in client state and passed in API calls

#### Tabs Not Switching
- **Cause**: State not updating when switching conversations
- **Solution**: Verify `switchToConversation()` is properly updating state

#### New Chat Not Working
- **Cause**: `createNewConversation()` not creating proper conversation structure
- **Solution**: Check that new conversation has proper ID and is added to conversations array

### Debug Tips
1. Check browser console for JavaScript errors
2. Verify API responses include correct session/conversation IDs
3. Use browser dev tools to inspect state changes
4. Check backend logs for context building issues

## Conclusion

The Session & Conversation Management feature provides a robust, scalable solution for managing multiple chat conversations within a single session. It maintains contextual awareness while providing an intuitive user interface for conversation management. The hierarchical structure allows for organized chat management while preserving the ability to maintain context within individual conversations.

This feature significantly enhances the user experience by allowing users to:
- Organize different topics into separate conversations
- Maintain context within each conversation
- Easily switch between different chat threads
- Manage their chat history effectively

The implementation is production-ready and designed for easy extension and maintenance.
