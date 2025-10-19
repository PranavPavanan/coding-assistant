/**
 * Global state management with Zustand
 */
import { create } from 'zustand'

export interface Repository {
  id: string
  name: string
  full_name: string
  description: string | null
  html_url: string
  stars: number
  language: string | null
  owner: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: Array<{
    file_path: string
    start_line: number
    end_line: number
    content: string
    relevance_score: number
  }>
}

export interface Conversation {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: string
  lastActivity: string
}

export interface Session {
  id: string
  conversations: Conversation[]
  createdAt: string
  lastActivity: string
}

export interface IndexingTask {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: {
    files_processed: number
    total_files: number
    percentage: number
  }
  repository_url: string
  error?: string
}

interface AppState {
  // Repository state
  selectedRepository: Repository | null
  searchResults: Repository[]
  isSearching: boolean

  // Indexing state
  currentIndexingTask: IndexingTask | null
  isIndexing: boolean
  indexStats: {
    is_indexed: boolean
    repository_name: string | null
    file_count: number
    vector_count: number
  } | null

  // Chat state
  messages: ChatMessage[]
  conversationId: string | null
  sessionId: string | null
  currentConversation: Conversation | null
  conversations: Conversation[]
  isQuerying: boolean

  // UI state
  activeTab: 'search' | 'indexing' | 'chat'

  // Actions
  setSelectedRepository: (repo: Repository | null) => void
  setSearchResults: (results: Repository[]) => void
  setIsSearching: (isSearching: boolean) => void

  setCurrentIndexingTask: (task: IndexingTask | null) => void
  setIsIndexing: (isIndexing: boolean) => void
  setIndexStats: (stats: AppState['indexStats']) => void

  addMessage: (message: ChatMessage) => void
  setMessages: (messages: ChatMessage[]) => void
  setConversationId: (id: string | null) => void
  setSessionId: (id: string | null) => void
  setCurrentConversation: (conversation: Conversation | null) => void
  setConversations: (conversations: Conversation[]) => void
  addConversation: (conversation: Conversation) => void
  updateConversation: (id: string, updates: Partial<Conversation>) => void
  switchToConversation: (id: string) => void
  createNewConversation: () => void
  setIsQuerying: (isQuerying: boolean) => void
  clearMessages: () => void
  clearAllConversations: () => void

  setActiveTab: (tab: AppState['activeTab']) => void

  // Reset entire state
  reset: () => void
}

const initialState = {
  selectedRepository: null,
  searchResults: [],
  isSearching: false,
  currentIndexingTask: null,
  isIndexing: false,
  indexStats: null,
  messages: [],
  conversationId: null,
  sessionId: null,
  currentConversation: null,
  conversations: [],
  isQuerying: false,
  activeTab: 'search' as const,
}

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  // Repository actions
  setSelectedRepository: (repo) => set({ selectedRepository: repo }),
  setSearchResults: (results) => set({ searchResults: results }),
  setIsSearching: (isSearching) => set({ isSearching }),

  // Indexing actions
  setCurrentIndexingTask: (task) => set({ currentIndexingTask: task }),
  setIsIndexing: (isIndexing) => set({ isIndexing }),
  setIndexStats: (stats) => set({ indexStats: stats }),

  // Chat actions
  addMessage: (message) => set((state) => {
    const newMessages = [...state.messages, message]
    
    // Update current conversation if it exists
    if (state.currentConversation) {
      const updatedConversation = {
        ...state.currentConversation,
        messages: newMessages,
        lastActivity: new Date().toISOString()
      }
      
      const updatedConversations = state.conversations.map(conv =>
        conv.id === state.currentConversation!.id ? updatedConversation : conv
      )
      
      return {
        messages: newMessages,
        currentConversation: updatedConversation,
        conversations: updatedConversations
      }
    }
    
    return { messages: newMessages }
  }),
  
  setMessages: (messages) => set({ messages }),
  setConversationId: (id) => set({ conversationId: id }),
  setSessionId: (id) => set({ sessionId: id }),
  setCurrentConversation: (conversation) => set({ 
    currentConversation: conversation,
    messages: conversation?.messages || [],
    conversationId: conversation?.id || null
  }),
  setConversations: (conversations) => set({ conversations }),
  
  addConversation: (conversation) => set((state) => ({
    conversations: [...state.conversations, conversation],
    currentConversation: conversation,
    messages: conversation.messages,
    conversationId: conversation.id
  })),
  
  updateConversation: (id, updates) => set((state) => {
    const updatedConversations = state.conversations.map(conv =>
      conv.id === id ? { ...conv, ...updates } : conv
    )
    
    const updatedCurrent = state.currentConversation?.id === id 
      ? { ...state.currentConversation, ...updates }
      : state.currentConversation
    
    return {
      conversations: updatedConversations,
      currentConversation: updatedCurrent
    }
  }),
  
  switchToConversation: (id) => set((state) => {
    const conversation = state.conversations.find(conv => conv.id === id)
    if (conversation) {
      return {
        currentConversation: conversation,
        messages: conversation.messages,
        conversationId: conversation.id
      }
    }
    return state
  }),
  
  createNewConversation: () => set((state) => {
    const newConversation: Conversation = {
      id: `conv-${Date.now()}`,
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString(),
      lastActivity: new Date().toISOString()
    }
    
    return {
      conversations: [...state.conversations, newConversation],
      currentConversation: newConversation,
      messages: [],
      conversationId: newConversation.id
    }
  }),
  
  setIsQuerying: (isQuerying) => set({ isQuerying }),
  clearMessages: () => set({ messages: [], conversationId: null }),
  clearAllConversations: () => set({ 
    conversations: [], 
    currentConversation: null, 
    messages: [], 
    conversationId: null,
    sessionId: null
  }),

  // UI actions
  setActiveTab: (tab) => set({ activeTab: tab }),

  // Reset
  reset: () => set(initialState),
}))

export default useAppStore
