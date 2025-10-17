/**
 * Comprehensive unit tests for React components
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { RepositorySearch } from '@/components/RepositorySearch'
import { IndexingProgress } from '@/components/IndexingProgress'
import { ChatInterface } from '@/components/ChatInterface'
import { TabNavigation } from '@/components/TabNavigation'
import { useAppStore } from '@/store/appStore'

// Mock the API client
const mockApiClient = {
  searchRepositories: vi.fn(),
  validateRepositoryUrl: vi.fn(),
  startIndexing: vi.fn(),
  getIndexStatus: vi.fn(),
  getIndexStats: vi.fn(),
  clearIndex: vi.fn(),
  chatQuery: vi.fn(),
  getChatHistory: vi.fn(),
  getChatContext: vi.fn(),
  clearChatHistory: vi.fn(),
}

vi.mock('@/services/api', () => ({
  apiClient: mockApiClient,
}))

// Mock WebSocket client
const mockWsClient = {
  connect: vi.fn(),
  disconnect: vi.fn(),
  onMessage: vi.fn(),
  removeMessageHandler: vi.fn(),
}

vi.mock('@/services/websocket', () => ({
  wsClient: mockWsClient,
}))

describe('RepositorySearch Component', () => {
  beforeEach(() => {
    useAppStore.setState({
      searchResults: [],
      isSearching: false,
      selectedRepository: null,
    })
    vi.clearAllMocks()
  })

  it('renders search input and button', () => {
    render(<RepositorySearch />)
    
    const searchInput = screen.getByPlaceholderText(/search repositories/i)
    const searchButton = screen.getByRole('button', { name: /search/i })
    
    expect(searchInput).toBeInTheDocument()
    expect(searchButton).toBeInTheDocument()
  })

  it('renders URL input and validate button', () => {
    render(<RepositorySearch />)
    
    const urlInput = screen.getByPlaceholderText(/github\.com\/owner\/repo/i)
    const validateButton = screen.getByRole('button', { name: /validate/i })
    
    expect(urlInput).toBeInTheDocument()
    expect(validateButton).toBeInTheDocument()
  })

  it('handles search input change', () => {
    render(<RepositorySearch />)
    
    const searchInput = screen.getByPlaceholderText(/search repositories/i)
    fireEvent.change(searchInput, { target: { value: 'python test' } })
    
    expect(searchInput).toHaveValue('python test')
  })

  it('handles URL input change', () => {
    render(<RepositorySearch />)
    
    const urlInput = screen.getByPlaceholderText(/github\.com\/owner\/repo/i)
    fireEvent.change(urlInput, { target: { value: 'https://github.com/owner/repo' } })
    
    expect(urlInput).toHaveValue('https://github.com/owner/repo')
  })

  it('calls search API on search button click', async () => {
    const mockResults = [
      {
        id: '1',
        name: 'test-repo',
        full_name: 'owner/test-repo',
        description: 'A test repository',
        html_url: 'https://github.com/owner/test-repo',
        stars: 100,
        language: 'TypeScript',
        owner: 'owner',
      },
    ]
    
    mockApiClient.searchRepositories.mockResolvedValue({
      repositories: mockResults,
      total_count: 1,
    })

    render(<RepositorySearch />)
    
    const searchInput = screen.getByPlaceholderText(/search repositories/i)
    const searchButton = screen.getByRole('button', { name: /search/i })
    
    fireEvent.change(searchInput, { target: { value: 'test' } })
    fireEvent.click(searchButton)
    
    await waitFor(() => {
      expect(mockApiClient.searchRepositories).toHaveBeenCalledWith({
        query: 'test',
        limit: 10,
      })
    })
  })

  it('calls validate API on validate button click', async () => {
    mockApiClient.validateRepositoryUrl.mockResolvedValue({
      is_valid: true,
      repository: {
        id: '1',
        name: 'test-repo',
        full_name: 'owner/test-repo',
        description: 'A test repository',
        html_url: 'https://github.com/owner/test-repo',
        stars: 100,
        language: 'TypeScript',
        owner: 'owner',
      },
    })

    render(<RepositorySearch />)
    
    const urlInput = screen.getByPlaceholderText(/github\.com\/owner\/repo/i)
    const validateButton = screen.getByRole('button', { name: /validate/i })
    
    fireEvent.change(urlInput, { target: { value: 'https://github.com/owner/test-repo' } })
    fireEvent.click(validateButton)
    
    await waitFor(() => {
      expect(mockApiClient.validateRepositoryUrl).toHaveBeenCalledWith({
        url: 'https://github.com/owner/test-repo',
      })
    })
  })

  it('displays loading state when searching', () => {
    useAppStore.setState({ isSearching: true })
    
    render(<RepositorySearch />)
    
    const loadingText = screen.getByText(/searching/i)
    expect(loadingText).toBeInTheDocument()
  })

  it('displays search results', () => {
    const mockResults = [
      {
        id: '1',
        name: 'test-repo',
        full_name: 'owner/test-repo',
        description: 'A test repository',
        html_url: 'https://github.com/owner/test-repo',
        stars: 100,
        language: 'TypeScript',
        owner: 'owner',
      },
    ]
    
    useAppStore.setState({ searchResults: mockResults })
    
    render(<RepositorySearch />)
    
    expect(screen.getByText('owner/test-repo')).toBeInTheDocument()
    expect(screen.getByText('A test repository')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
    expect(screen.getByText('TypeScript')).toBeInTheDocument()
  })

  it('handles repository selection', () => {
    const mockResults = [
      {
        id: '1',
        name: 'test-repo',
        full_name: 'owner/test-repo',
        description: 'A test repository',
        html_url: 'https://github.com/owner/test-repo',
        stars: 100,
        language: 'TypeScript',
        owner: 'owner',
      },
    ]
    
    useAppStore.setState({ searchResults: mockResults })
    
    render(<RepositorySearch />)
    
    const selectButton = screen.getByRole('button', { name: /select/i })
    fireEvent.click(selectButton)
    
    expect(useAppStore.getState().selectedRepository).toEqual(mockResults[0])
  })

  it('handles search error', async () => {
    mockApiClient.searchRepositories.mockRejectedValue(new Error('Search failed'))
    
    render(<RepositorySearch />)
    
    const searchInput = screen.getByPlaceholderText(/search repositories/i)
    const searchButton = screen.getByRole('button', { name: /search/i })
    
    fireEvent.change(searchInput, { target: { value: 'test' } })
    fireEvent.click(searchButton)
    
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('handles validation error', async () => {
    mockApiClient.validateRepositoryUrl.mockResolvedValue({
      is_valid: false,
      error: 'Repository not found',
    })
    
    render(<RepositorySearch />)
    
    const urlInput = screen.getByPlaceholderText(/github\.com\/owner\/repo/i)
    const validateButton = screen.getByRole('button', { name: /validate/i })
    
    fireEvent.change(urlInput, { target: { value: 'https://github.com/owner/nonexistent' } })
    fireEvent.click(validateButton)
    
    await waitFor(() => {
      expect(screen.getByText(/repository not found/i)).toBeInTheDocument()
    })
  })

  it('validates URL format', async () => {
    render(<RepositorySearch />)
    
    const urlInput = screen.getByPlaceholderText(/github\.com\/owner\/repo/i)
    const validateButton = screen.getByRole('button', { name: /validate/i })
    
    fireEvent.change(urlInput, { target: { value: 'not-a-url' } })
    fireEvent.click(validateButton)
    
    await waitFor(() => {
      expect(screen.getByText(/invalid url/i)).toBeInTheDocument()
    })
  })
})

describe('IndexingProgress Component', () => {
  beforeEach(() => {
    useAppStore.setState({
      selectedRepository: null,
      currentIndexingTask: null,
      isIndexing: false,
      indexStats: null,
    })
    vi.clearAllMocks()
  })

  it('renders repository indexing title', () => {
    render(<IndexingProgress />)
    
    const title = screen.getByText(/repository indexing/i)
    expect(title).toBeInTheDocument()
  })

  it('displays selected repository', () => {
    const mockRepo = {
      id: '1',
      name: 'test-repo',
      full_name: 'owner/test-repo',
      description: 'A test repository',
      html_url: 'https://github.com/owner/test-repo',
      stars: 100,
      language: 'TypeScript',
      owner: 'owner',
    }
    
    useAppStore.setState({ selectedRepository: mockRepo })
    
    render(<IndexingProgress />)
    
    expect(screen.getByText('owner/test-repo')).toBeInTheDocument()
    expect(screen.getByText('A test repository')).toBeInTheDocument()
  })

  it('shows start indexing button when repository is selected', () => {
    const mockRepo = {
      id: '1',
      name: 'test-repo',
      full_name: 'owner/test-repo',
      description: 'A test repository',
      html_url: 'https://github.com/owner/test-repo',
      stars: 100,
      language: 'TypeScript',
      owner: 'owner',
    }
    
    useAppStore.setState({ selectedRepository: mockRepo })
    
    render(<IndexingProgress />)
    
    const startButton = screen.getByRole('button', { name: /start indexing/i })
    expect(startButton).toBeInTheDocument()
  })

  it('disables start button when indexing', () => {
    useAppStore.setState({ isIndexing: true })
    
    render(<IndexingProgress />)
    
    const startButton = screen.getByRole('button', { name: /start indexing/i })
    expect(startButton).toBeDisabled()
  })

  it('calls start indexing API on button click', async () => {
    const mockRepo = {
      id: '1',
      name: 'test-repo',
      full_name: 'owner/test-repo',
      description: 'A test repository',
      html_url: 'https://github.com/owner/test-repo',
      stars: 100,
      language: 'TypeScript',
      owner: 'owner',
    }
    
    useAppStore.setState({ selectedRepository: mockRepo })
    mockApiClient.startIndexing.mockResolvedValue({
      task_id: 'task-123',
      status: 'pending',
      message: 'Indexing started',
    })
    
    render(<IndexingProgress />)
    
    const startButton = screen.getByRole('button', { name: /start indexing/i })
    fireEvent.click(startButton)
    
    await waitFor(() => {
      expect(mockApiClient.startIndexing).toHaveBeenCalledWith({
        repository_url: 'https://github.com/owner/test-repo',
        branch: 'main',
      })
    })
  })

  it('displays indexing progress', () => {
    const mockTask = {
      task_id: 'task-123',
      status: 'running',
      progress: {
        files_processed: 50,
        total_files: 100,
        percentage: 50.0,
      },
      repository_url: 'https://github.com/owner/test-repo',
    }
    
    useAppStore.setState({ currentIndexingTask: mockTask })
    
    render(<IndexingProgress />)
    
    expect(screen.getByText('50.0%')).toBeInTheDocument()
    expect(screen.getByText('50 / 100 files')).toBeInTheDocument()
  })

  it('displays completed indexing', () => {
    const mockTask = {
      task_id: 'task-123',
      status: 'completed',
      progress: {
        files_processed: 100,
        total_files: 100,
        percentage: 100.0,
      },
      repository_url: 'https://github.com/owner/test-repo',
    }
    
    useAppStore.setState({ currentIndexingTask: mockTask })
    
    render(<IndexingProgress />)
    
    expect(screen.getByText('100.0%')).toBeInTheDocument()
    expect(screen.getByText(/completed/i)).toBeInTheDocument()
  })

  it('displays failed indexing', () => {
    const mockTask = {
      task_id: 'task-123',
      status: 'failed',
      progress: {
        files_processed: 25,
        total_files: 100,
        percentage: 25.0,
      },
      repository_url: 'https://github.com/owner/test-repo',
      error: 'Repository not found',
    }
    
    useAppStore.setState({ currentIndexingTask: mockTask })
    
    render(<IndexingProgress />)
    
    expect(screen.getByText(/failed/i)).toBeInTheDocument()
    expect(screen.getByText('Repository not found')).toBeInTheDocument()
  })

  it('displays index stats when available', () => {
    const mockStats = {
      is_indexed: true,
      repository_name: 'owner/test-repo',
      file_count: 100,
      total_size: 1024000,
      vector_count: 1000,
      last_updated: '2023-01-01T00:00:00Z',
    }
    
    useAppStore.setState({ indexStats: mockStats })
    
    render(<IndexingProgress />)
    
    expect(screen.getByText('100 files')).toBeInTheDocument()
    expect(screen.getByText('1.0 MB')).toBeInTheDocument()
    expect(screen.getByText('1000 vectors')).toBeInTheDocument()
  })

  it('handles indexing error', async () => {
    const mockRepo = {
      id: '1',
      name: 'test-repo',
      full_name: 'owner/test-repo',
      description: 'A test repository',
      html_url: 'https://github.com/owner/test-repo',
      stars: 100,
      language: 'TypeScript',
      owner: 'owner',
    }
    
    useAppStore.setState({ selectedRepository: mockRepo })
    mockApiClient.startIndexing.mockRejectedValue(new Error('Indexing failed'))
    
    render(<IndexingProgress />)
    
    const startButton = screen.getByRole('button', { name: /start indexing/i })
    fireEvent.click(startButton)
    
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })
})

describe('ChatInterface Component', () => {
  beforeEach(() => {
    useAppStore.setState({
      messages: [],
      conversationId: null,
      isQuerying: false,
      indexStats: { is_indexed: true },
    })
    vi.clearAllMocks()
  })

  it('renders chat interface title', () => {
    render(<ChatInterface />)
    
    const title = screen.getByText(/code query/i)
    expect(title).toBeInTheDocument()
  })

  it('renders message input and send button', () => {
    render(<ChatInterface />)
    
    const messageInput = screen.getByPlaceholderText(/ask about the code/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    expect(messageInput).toBeInTheDocument()
    expect(sendButton).toBeInTheDocument()
  })

  it('disables input when not indexed', () => {
    useAppStore.setState({ indexStats: { is_indexed: false } })
    
    render(<ChatInterface />)
    
    const messageInput = screen.getByPlaceholderText(/ask about the code/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    expect(messageInput).toBeDisabled()
    expect(sendButton).toBeDisabled()
  })

  it('handles message input change', () => {
    render(<ChatInterface />)
    
    const messageInput = screen.getByPlaceholderText(/ask about the code/i)
    fireEvent.change(messageInput, { target: { value: 'What does this do?' } })
    
    expect(messageInput).toHaveValue('What does this do?')
  })

  it('calls chat API on send button click', async () => {
    mockApiClient.chatQuery.mockResolvedValue({
      response: 'This function does X',
      sources: [],
      conversation_id: 'conv-123',
      confidence: 0.85,
      processing_time: 1.5,
      model_used: 'codellama-7b',
    })
    
    render(<ChatInterface />)
    
    const messageInput = screen.getByPlaceholderText(/ask about the code/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(messageInput, { target: { value: 'What does this do?' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(mockApiClient.chatQuery).toHaveBeenCalledWith({
        query: 'What does this do?',
        conversation_id: null,
      })
    })
  })

  it('calls chat API with existing conversation ID', async () => {
    useAppStore.setState({ conversationId: 'conv-123' })
    mockApiClient.chatQuery.mockResolvedValue({
      response: 'This function does Y',
      sources: [],
      conversation_id: 'conv-123',
      confidence: 0.85,
      processing_time: 1.5,
      model_used: 'codellama-7b',
    })
    
    render(<ChatInterface />)
    
    const messageInput = screen.getByPlaceholderText(/ask about the code/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(messageInput, { target: { value: 'What else does it do?' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(mockApiClient.chatQuery).toHaveBeenCalledWith({
        query: 'What else does it do?',
        conversation_id: 'conv-123',
      })
    })
  })

  it('handles send on Enter key press', async () => {
    mockApiClient.chatQuery.mockResolvedValue({
      response: 'This function does X',
      sources: [],
      conversation_id: 'conv-123',
      confidence: 0.85,
      processing_time: 1.5,
      model_used: 'codellama-7b',
    })
    
    render(<ChatInterface />)
    
    const messageInput = screen.getByPlaceholderText(/ask about the code/i)
    
    fireEvent.change(messageInput, { target: { value: 'What does this do?' } })
    fireEvent.keyDown(messageInput, { key: 'Enter', code: 'Enter' })
    
    await waitFor(() => {
      expect(mockApiClient.chatQuery).toHaveBeenCalled()
    })
  })

  it('displays chat messages', () => {
    const mockMessages = [
      {
        role: 'user',
        content: 'What does this do?',
        timestamp: '2023-01-01T00:00:00Z',
      },
      {
        role: 'assistant',
        content: 'This function does X',
        timestamp: '2023-01-01T00:00:01Z',
      },
    ]
    
    useAppStore.setState({ messages: mockMessages })
    
    render(<ChatInterface />)
    
    expect(screen.getByText('What does this do?')).toBeInTheDocument()
    expect(screen.getByText('This function does X')).toBeInTheDocument()
  })

  it('displays loading state when querying', () => {
    useAppStore.setState({ isQuerying: true })
    
    render(<ChatInterface />)
    
    const loadingIndicator = screen.getByText(/processing/i)
    expect(loadingIndicator).toBeInTheDocument()
  })

  it('disables send button when querying', () => {
    useAppStore.setState({ isQuerying: true })
    
    render(<ChatInterface />)
    
    const sendButton = screen.getByRole('button', { name: /send/i })
    expect(sendButton).toBeDisabled()
  })

  it('clears input after sending message', async () => {
    mockApiClient.chatQuery.mockResolvedValue({
      response: 'This function does X',
      sources: [],
      conversation_id: 'conv-123',
      confidence: 0.85,
      processing_time: 1.5,
      model_used: 'codellama-7b',
    })
    
    render(<ChatInterface />)
    
    const messageInput = screen.getByPlaceholderText(/ask about the code/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(messageInput, { target: { value: 'What does this do?' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(messageInput).toHaveValue('')
    })
  })

  it('handles chat error', async () => {
    mockApiClient.chatQuery.mockRejectedValue(new Error('Chat failed'))
    
    render(<ChatInterface />)
    
    const messageInput = screen.getByPlaceholderText(/ask about the code/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(messageInput, { target: { value: 'What does this do?' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('displays source references', () => {
    const mockMessages = [
      {
        role: 'assistant',
        content: 'This function does X',
        timestamp: '2023-01-01T00:00:01Z',
        sources: [
          {
            file_path: 'src/test.py',
            start_line: 10,
            end_line: 15,
            content: 'def test():\n    pass',
            score: 0.95,
          },
        ],
      },
    ]
    
    useAppStore.setState({ messages: mockMessages })
    
    render(<ChatInterface />)
    
    expect(screen.getByText('src/test.py')).toBeInTheDocument()
    expect(screen.getByText('lines 10-15')).toBeInTheDocument()
  })

  it('handles empty message', () => {
    render(<ChatInterface />)
    
    const messageInput = screen.getByPlaceholderText(/ask about the code/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(messageInput, { target: { value: '' } })
    fireEvent.click(sendButton)
    
    expect(mockApiClient.chatQuery).not.toHaveBeenCalled()
  })

  it('handles whitespace-only message', () => {
    render(<ChatInterface />)
    
    const messageInput = screen.getByPlaceholderText(/ask about the code/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(messageInput, { target: { value: '   ' } })
    fireEvent.click(sendButton)
    
    expect(mockApiClient.chatQuery).not.toHaveBeenCalled()
  })
})

describe('TabNavigation Component', () => {
  beforeEach(() => {
    useAppStore.setState({
      activeTab: 'search',
      indexStats: null,
    })
    vi.clearAllMocks()
  })

  it('renders all three tabs', () => {
    render(<TabNavigation />)
    
    expect(screen.getByText(/search/i)).toBeInTheDocument()
    expect(screen.getByText(/index/i)).toBeInTheDocument()
    expect(screen.getByText(/query/i)).toBeInTheDocument()
  })

  it('highlights active tab', () => {
    useAppStore.setState({ activeTab: 'search' })
    
    render(<TabNavigation />)
    
    const searchTab = screen.getByText(/search/i).closest('button')
    expect(searchTab).toHaveClass('border-primary')
  })

  it('changes active tab on click', () => {
    render(<TabNavigation />)
    
    const indexTab = screen.getByText(/index/i).closest('button')
    fireEvent.click(indexTab!)
    
    expect(useAppStore.getState().activeTab).toBe('indexing')
  })

  it('disables query tab when not indexed', () => {
    useAppStore.setState({ indexStats: { is_indexed: false } })
    
    render(<TabNavigation />)
    
    const queryTab = screen.getByText(/query/i).closest('button')
    expect(queryTab).toBeDisabled()
  })

  it('enables query tab when indexed', () => {
    useAppStore.setState({
      indexStats: {
        is_indexed: true,
        repository_name: 'test/repo',
        file_count: 10,
        vector_count: 100,
        last_updated: '2023-01-01T00:00:00Z',
      },
    })
    
    render(<TabNavigation />)
    
    const queryTab = screen.getByText(/query/i).closest('button')
    expect(queryTab).not.toBeDisabled()
  })

  it('shows index status in index tab', () => {
    useAppStore.setState({
      indexStats: {
        is_indexed: true,
        repository_name: 'test/repo',
        file_count: 10,
        vector_count: 100,
        last_updated: '2023-01-01T00:00:00Z',
      },
    })
    
    render(<TabNavigation />)
    
    expect(screen.getByText('test/repo')).toBeInTheDocument()
    expect(screen.getByText('10 files')).toBeInTheDocument()
  })

  it('shows not indexed status', () => {
    useAppStore.setState({ indexStats: { is_indexed: false } })
    
    render(<TabNavigation />)
    
    expect(screen.getByText(/not indexed/i)).toBeInTheDocument()
  })

  it('handles tab click with keyboard navigation', () => {
    render(<TabNavigation />)
    
    const indexTab = screen.getByText(/index/i).closest('button')
    fireEvent.keyDown(indexTab!, { key: 'Enter', code: 'Enter' })
    
    expect(useAppStore.getState().activeTab).toBe('indexing')
  })

  it('handles tab click with space key', () => {
    render(<TabNavigation />)
    
    const indexTab = screen.getByText(/index/i).closest('button')
    fireEvent.keyDown(indexTab!, { key: ' ', code: 'Space' })
    
    expect(useAppStore.getState().activeTab).toBe('indexing')
  })
})

describe('Zustand Store', () => {
  beforeEach(() => {
    useAppStore.setState({
      selectedRepository: null,
      searchResults: [],
      isSearching: false,
      currentIndexingTask: null,
      isIndexing: false,
      indexStats: null,
      messages: [],
      conversationId: null,
      isQuerying: false,
      activeTab: 'search',
    })
  })

  it('initializes with default state', () => {
    const state = useAppStore.getState()
    expect(state.activeTab).toBe('search')
    expect(state.isSearching).toBe(false)
    expect(state.messages).toEqual([])
    expect(state.selectedRepository).toBeNull()
  })

  it('sets selected repository', () => {
    const repo = {
      id: '1',
      name: 'test',
      full_name: 'owner/test',
      description: 'Test',
      html_url: 'https://github.com/owner/test',
      stars: 10,
      language: 'TypeScript',
      owner: 'owner',
    }
    
    useAppStore.getState().setSelectedRepository(repo)
    expect(useAppStore.getState().selectedRepository).toEqual(repo)
  })

  it('sets active tab', () => {
    useAppStore.getState().setActiveTab('indexing')
    expect(useAppStore.getState().activeTab).toBe('indexing')
  })

  it('adds message to chat', () => {
    const message = {
      role: 'user' as const,
      content: 'Test message',
      timestamp: '2023-01-01T00:00:00Z',
    }
    
    useAppStore.getState().addMessage(message)
    expect(useAppStore.getState().messages).toHaveLength(1)
    expect(useAppStore.getState().messages[0].content).toBe('Test message')
  })

  it('clears messages', () => {
    useAppStore.setState({
      messages: [
        {
          role: 'user',
          content: 'Test',
          timestamp: '2023-01-01T00:00:00Z',
        },
      ],
    })
    
    useAppStore.getState().clearMessages()
    expect(useAppStore.getState().messages).toHaveLength(0)
  })

  it('sets search results', () => {
    const results = [
      {
        id: '1',
        name: 'test-repo',
        full_name: 'owner/test-repo',
        description: 'Test',
        html_url: 'https://github.com/owner/test-repo',
        stars: 10,
        language: 'TypeScript',
        owner: 'owner',
      },
    ]
    
    useAppStore.getState().setSearchResults(results)
    expect(useAppStore.getState().searchResults).toEqual(results)
  })

  it('sets indexing task', () => {
    const task = {
      task_id: 'task-123',
      status: 'running',
      progress: {
        files_processed: 50,
        total_files: 100,
        percentage: 50.0,
      },
      repository_url: 'https://github.com/owner/test-repo',
    }
    
    useAppStore.getState().setCurrentIndexingTask(task)
    expect(useAppStore.getState().currentIndexingTask).toEqual(task)
  })

  it('sets index stats', () => {
    const stats = {
      is_indexed: true,
      repository_name: 'test/repo',
      file_count: 100,
      total_size: 1024000,
      vector_count: 1000,
      last_updated: '2023-01-01T00:00:00Z',
      created_at: '2023-01-01T00:00:00Z',
    }
    
    useAppStore.getState().setIndexStats(stats)
    expect(useAppStore.getState().indexStats).toEqual(stats)
  })

  it('sets conversation ID', () => {
    useAppStore.getState().setConversationId('conv-123')
    expect(useAppStore.getState().conversationId).toBe('conv-123')
  })

  it('sets querying state', () => {
    useAppStore.getState().setIsQuerying(true)
    expect(useAppStore.getState().isQuerying).toBe(true)
  })

  it('sets searching state', () => {
    useAppStore.getState().setIsSearching(true)
    expect(useAppStore.getState().isSearching).toBe(true)
  })

  it('sets indexing state', () => {
    useAppStore.getState().setIsIndexing(true)
    expect(useAppStore.getState().isIndexing).toBe(true)
  })
})
