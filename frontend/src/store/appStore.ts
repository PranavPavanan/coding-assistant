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
  setIsQuerying: (isQuerying: boolean) => void
  clearMessages: () => void

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
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setMessages: (messages) => set({ messages }),
  setConversationId: (id) => set({ conversationId: id }),
  setIsQuerying: (isQuerying) => set({ isQuerying }),
  clearMessages: () => set({ messages: [], conversationId: null }),

  // UI actions
  setActiveTab: (tab) => set({ activeTab: tab }),

  // Reset
  reset: () => set(initialState),
}))

export default useAppStore
