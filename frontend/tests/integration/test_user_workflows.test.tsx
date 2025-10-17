/**
 * Integration tests for complete user workflows
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { App } from '@/App'
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

describe('Complete User Workflows', () => {
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
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Repository Discovery and Indexing Workflow', () => {
    it('completes full workflow from search to indexing', async () => {
      // Mock API responses
      mockApiClient.searchRepositories.mockResolvedValue({
        repositories: [
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
        ],
        total_count: 1,
      })

      mockApiClient.startIndexing.mockResolvedValue({
        task_id: 'task-123',
        status: 'pending',
        message: 'Indexing started',
      })

      mockApiClient.getIndexStatus.mockResolvedValue({
        task_id: 'task-123',
        status: 'running',
        progress: {
          files_processed: 50,
          total_files: 100,
          percentage: 50.0,
        },
        percentage: 50.0,
        repository_url: 'https://github.com/owner/test-repo',
      })

      mockApiClient.getIndexStats.mockResolvedValue({
        is_indexed: true,
        repository_name: 'owner/test-repo',
        file_count: 100,
        total_size: 1024000,
        vector_count: 1000,
        last_updated: '2023-01-01T00:00:00Z',
      })

      render(<App />)

      // Step 1: Search for repositories
      const searchInput = screen.getByPlaceholderText(/search repositories/i)
      const searchButton = screen.getByRole('button', { name: /search/i })

      fireEvent.change(searchInput, { target: { value: 'test repository' } })
      fireEvent.click(searchButton)

      await waitFor(() => {
        expect(mockApiClient.searchRepositories).toHaveBeenCalledWith({
          query: 'test repository',
          limit: 10,
        })
      })

      // Step 2: Wait for search results
      await waitFor(() => {
        expect(screen.getByText('owner/test-repo')).toBeInTheDocument()
      })

      // Step 3: Select repository
      const selectButton = screen.getByRole('button', { name: /select/i })
      fireEvent.click(selectButton)

      // Step 4: Switch to indexing tab
      const indexTab = screen.getByText(/index/i).closest('button')
      fireEvent.click(indexTab!)

      // Step 5: Start indexing
      const startIndexingButton = screen.getByRole('button', { name: /start indexing/i })
      fireEvent.click(startIndexingButton)

      await waitFor(() => {
        expect(mockApiClient.startIndexing).toHaveBeenCalledWith({
          repository_url: 'https://github.com/owner/test-repo',
          branch: 'main',
        })
      })

      // Step 6: Check indexing progress
      await waitFor(() => {
        expect(screen.getByText('50.0%')).toBeInTheDocument()
      })

      // Step 7: Wait for completion
      mockApiClient.getIndexStats.mockResolvedValue({
        is_indexed: true,
        repository_name: 'owner/test-repo',
        file_count: 100,
        total_size: 1024000,
        vector_count: 1000,
        last_updated: '2023-01-01T00:00:00Z',
      })

      await waitFor(() => {
        expect(screen.getByText('100 files')).toBeInTheDocument()
      })
    })

    it('handles URL validation workflow', async () => {
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

      mockApiClient.startIndexing.mockResolvedValue({
        task_id: 'task-123',
        status: 'pending',
        message: 'Indexing started',
      })

      render(<App />)

      // Step 1: Enter repository URL
      const urlInput = screen.getByPlaceholderText(/github\.com\/owner\/repo/i)
      const validateButton = screen.getByRole('button', { name: /validate/i })

      fireEvent.change(urlInput, { target: { value: 'https://github.com/owner/test-repo' } })
      fireEvent.click(validateButton)

      await waitFor(() => {
        expect(mockApiClient.validateRepositoryUrl).toHaveBeenCalledWith({
          url: 'https://github.com/owner/test-repo',
        })
      })

      // Step 2: Wait for validation success
      await waitFor(() => {
        expect(screen.getByText('owner/test-repo')).toBeInTheDocument()
      })

      // Step 3: Select repository
      const selectButton = screen.getByRole('button', { name: /select/i })
      fireEvent.click(selectButton)

      // Step 4: Switch to indexing tab and start indexing
      const indexTab = screen.getByText(/index/i).closest('button')
      fireEvent.click(indexTab!)

      const startIndexingButton = screen.getByRole('button', { name: /start indexing/i })
      fireEvent.click(startIndexingButton)

      await waitFor(() => {
        expect(mockApiClient.startIndexing).toHaveBeenCalled()
      })
    })

    it('handles search error gracefully', async () => {
      mockApiClient.searchRepositories.mockRejectedValue(new Error('Search failed'))

      render(<App />)

      const searchInput = screen.getByPlaceholderText(/search repositories/i)
      const searchButton = screen.getByRole('button', { name: /search/i })

      fireEvent.change(searchInput, { target: { value: 'test' } })
      fireEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })

    it('handles indexing error gracefully', async () => {
      mockApiClient.searchRepositories.mockResolvedValue({
        repositories: [
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
        ],
        total_count: 1,
      })

      mockApiClient.startIndexing.mockRejectedValue(new Error('Indexing failed'))

      render(<App />)

      // Search and select repository
      const searchInput = screen.getByPlaceholderText(/search repositories/i)
      const searchButton = screen.getByRole('button', { name: /search/i })

      fireEvent.change(searchInput, { target: { value: 'test' } })
      fireEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('owner/test-repo')).toBeInTheDocument()
      })

      const selectButton = screen.getByRole('button', { name: /select/i })
      fireEvent.click(selectButton)

      // Switch to indexing tab
      const indexTab = screen.getByText(/index/i).closest('button')
      fireEvent.click(indexTab!)

      // Start indexing
      const startIndexingButton = screen.getByRole('button', { name: /start indexing/i })
      fireEvent.click(startIndexingButton)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })
  })

  describe('Chat and Query Workflow', () => {
    beforeEach(() => {
      // Set up indexed state
      useAppStore.setState({
        indexStats: {
          is_indexed: true,
          repository_name: 'owner/test-repo',
          file_count: 100,
          total_size: 1024000,
          vector_count: 1000,
          last_updated: '2023-01-01T00:00:00Z',
        },
      })
    })

    it('completes full chat workflow', async () => {
      mockApiClient.chatQuery
        .mockResolvedValueOnce({
          response: 'This function calculates the sum of two numbers',
          sources: [
            {
              file_path: 'src/math.py',
              start_line: 10,
              end_line: 15,
              content: 'def add(a, b):\n    return a + b',
              score: 0.95,
            },
          ],
          conversation_id: 'conv-123',
          confidence: 0.85,
          processing_time: 1.5,
          model_used: 'codellama-7b',
        })
        .mockResolvedValueOnce({
          response: 'The function uses the + operator to add the two parameters',
          sources: [],
          conversation_id: 'conv-123',
          confidence: 0.90,
          processing_time: 1.2,
          model_used: 'codellama-7b',
        })

      mockApiClient.getChatHistory.mockResolvedValue({
        conversation_id: 'conv-123',
        messages: [
          {
            role: 'user',
            content: 'What does the add function do?',
            timestamp: '2023-01-01T00:00:00Z',
          },
          {
            role: 'assistant',
            content: 'This function calculates the sum of two numbers',
            timestamp: '2023-01-01T00:00:01Z',
            sources: [
              {
                file_path: 'src/math.py',
                start_line: 10,
                end_line: 15,
                content: 'def add(a, b):\n    return a + b',
                score: 0.95,
              },
            ],
          },
        ],
        total_messages: 2,
        created_at: '2023-01-01T00:00:00Z',
      })

      render(<App />)

      // Step 1: Switch to query tab
      const queryTab = screen.getByText(/query/i).closest('button')
      fireEvent.click(queryTab!)

      // Step 2: Ask first question
      const messageInput = screen.getByPlaceholderText(/ask about the code/i)
      const sendButton = screen.getByRole('button', { name: /send/i })

      fireEvent.change(messageInput, { target: { value: 'What does the add function do?' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(mockApiClient.chatQuery).toHaveBeenCalledWith({
          query: 'What does the add function do?',
          conversation_id: null,
        })
      })

      // Step 3: Wait for first response
      await waitFor(() => {
        expect(screen.getByText('This function calculates the sum of two numbers')).toBeInTheDocument()
      })

      // Step 4: Ask follow-up question
      fireEvent.change(messageInput, { target: { value: 'How does it work?' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(mockApiClient.chatQuery).toHaveBeenCalledWith({
          query: 'How does it work?',
          conversation_id: 'conv-123',
        })
      })

      // Step 5: Wait for second response
      await waitFor(() => {
        expect(screen.getByText('The function uses the + operator to add the two parameters')).toBeInTheDocument()
      })

      // Step 6: Check conversation history
      expect(screen.getByText('What does the add function do?')).toBeInTheDocument()
      expect(screen.getByText('This function calculates the sum of two numbers')).toBeInTheDocument()
    })

    it('handles chat error gracefully', async () => {
      mockApiClient.chatQuery.mockRejectedValue(new Error('Chat failed'))

      render(<App />)

      // Switch to query tab
      const queryTab = screen.getByText(/query/i).closest('button')
      fireEvent.click(queryTab!)

      // Ask question
      const messageInput = screen.getByPlaceholderText(/ask about the code/i)
      const sendButton = screen.getByRole('button', { name: /send/i })

      fireEvent.change(messageInput, { target: { value: 'What does this do?' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })

    it('prevents chat when not indexed', async () => {
      useAppStore.setState({
        indexStats: { is_indexed: false },
      })

      render(<App />)

      // Switch to query tab
      const queryTab = screen.getByText(/query/i).closest('button')
      fireEvent.click(queryTab!)

      // Check that input is disabled
      const messageInput = screen.getByPlaceholderText(/ask about the code/i)
      const sendButton = screen.getByRole('button', { name: /send/i })

      expect(messageInput).toBeDisabled()
      expect(sendButton).toBeDisabled()
    })

    it('handles empty message input', async () => {
      render(<App />)

      // Switch to query tab
      const queryTab = screen.getByText(/query/i).closest('button')
      fireEvent.click(queryTab!)

      // Try to send empty message
      const messageInput = screen.getByPlaceholderText(/ask about the code/i)
      const sendButton = screen.getByRole('button', { name: /send/i })

      fireEvent.change(messageInput, { target: { value: '' } })
      fireEvent.click(sendButton)

      // Should not call API
      expect(mockApiClient.chatQuery).not.toHaveBeenCalled()
    })
  })

  describe('Complete End-to-End Workflow', () => {
    it('completes full workflow from search to chat', async () => {
      // Mock all API responses
      mockApiClient.searchRepositories.mockResolvedValue({
        repositories: [
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
        ],
        total_count: 1,
      })

      mockApiClient.startIndexing.mockResolvedValue({
        task_id: 'task-123',
        status: 'pending',
        message: 'Indexing started',
      })

      mockApiClient.getIndexStatus.mockResolvedValue({
        task_id: 'task-123',
        status: 'completed',
        progress: {
          files_processed: 100,
          total_files: 100,
          percentage: 100.0,
        },
        percentage: 100.0,
        repository_url: 'https://github.com/owner/test-repo',
      })

      mockApiClient.getIndexStats.mockResolvedValue({
        is_indexed: true,
        repository_name: 'owner/test-repo',
        file_count: 100,
        total_size: 1024000,
        vector_count: 1000,
        last_updated: '2023-01-01T00:00:00Z',
      })

      mockApiClient.chatQuery.mockResolvedValue({
        response: 'This is a test repository with TypeScript code',
        sources: [],
        conversation_id: 'conv-123',
        confidence: 0.85,
        processing_time: 1.5,
        model_used: 'codellama-7b',
      })

      render(<App />)

      // Step 1: Search for repository
      const searchInput = screen.getByPlaceholderText(/search repositories/i)
      const searchButton = screen.getByRole('button', { name: /search/i })

      fireEvent.change(searchInput, { target: { value: 'test repository' } })
      fireEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('owner/test-repo')).toBeInTheDocument()
      })

      // Step 2: Select repository
      const selectButton = screen.getByRole('button', { name: /select/i })
      fireEvent.click(selectButton)

      // Step 3: Switch to indexing tab
      const indexTab = screen.getByText(/index/i).closest('button')
      fireEvent.click(indexTab!)

      // Step 4: Start indexing
      const startIndexingButton = screen.getByRole('button', { name: /start indexing/i })
      fireEvent.click(startIndexingButton)

      await waitFor(() => {
        expect(mockApiClient.startIndexing).toHaveBeenCalled()
      })

      // Step 5: Wait for indexing to complete
      await waitFor(() => {
        expect(screen.getByText('100 files')).toBeInTheDocument()
      })

      // Step 6: Switch to query tab
      const queryTab = screen.getByText(/query/i).closest('button')
      fireEvent.click(queryTab!)

      // Step 7: Ask question
      const messageInput = screen.getByPlaceholderText(/ask about the code/i)
      const sendButton = screen.getByRole('button', { name: /send/i })

      fireEvent.change(messageInput, { target: { value: 'What is this repository about?' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByText('This is a test repository with TypeScript code')).toBeInTheDocument()
      })

      // Verify all API calls were made
      expect(mockApiClient.searchRepositories).toHaveBeenCalled()
      expect(mockApiClient.startIndexing).toHaveBeenCalled()
      expect(mockApiClient.chatQuery).toHaveBeenCalled()
    })

    it('handles workflow with multiple repositories', async () => {
      // Mock search with multiple results
      mockApiClient.searchRepositories.mockResolvedValue({
        repositories: [
          {
            id: '1',
            name: 'repo1',
            full_name: 'owner/repo1',
            description: 'First repository',
            html_url: 'https://github.com/owner/repo1',
            stars: 100,
            language: 'TypeScript',
            owner: 'owner',
          },
          {
            id: '2',
            name: 'repo2',
            full_name: 'owner/repo2',
            description: 'Second repository',
            html_url: 'https://github.com/owner/repo2',
            stars: 200,
            language: 'Python',
            owner: 'owner',
          },
        ],
        total_count: 2,
      })

      render(<App />)

      // Search for repositories
      const searchInput = screen.getByPlaceholderText(/search repositories/i)
      const searchButton = screen.getByRole('button', { name: /search/i })

      fireEvent.change(searchInput, { target: { value: 'test' } })
      fireEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('owner/repo1')).toBeInTheDocument()
        expect(screen.getByText('owner/repo2')).toBeInTheDocument()
      })

      // Select first repository
      const selectButtons = screen.getAllByRole('button', { name: /select/i })
      fireEvent.click(selectButtons[0])

      // Verify first repository is selected
      expect(useAppStore.getState().selectedRepository?.name).toBe('repo1')

      // Select second repository
      fireEvent.click(selectButtons[1])

      // Verify second repository is selected
      expect(useAppStore.getState().selectedRepository?.name).toBe('repo2')
    })

    it('handles workflow with keyboard navigation', async () => {
      mockApiClient.searchRepositories.mockResolvedValue({
        repositories: [
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
        ],
        total_count: 1,
      })

      render(<App />)

      // Search with Enter key
      const searchInput = screen.getByPlaceholderText(/search repositories/i)
      fireEvent.change(searchInput, { target: { value: 'test' } })
      fireEvent.keyDown(searchInput, { key: 'Enter', code: 'Enter' })

      await waitFor(() => {
        expect(mockApiClient.searchRepositories).toHaveBeenCalled()
      })

      // Navigate tabs with keyboard
      const indexTab = screen.getByText(/index/i).closest('button')
      fireEvent.keyDown(indexTab!, { key: 'Enter', code: 'Enter' })

      expect(useAppStore.getState().activeTab).toBe('indexing')

      // Navigate back to search
      const searchTab = screen.getByText(/search/i).closest('button')
      fireEvent.keyDown(searchTab!, { key: 'Enter', code: 'Enter' })

      expect(useAppStore.getState().activeTab).toBe('search')
    })
  })

  describe('Error Recovery Workflows', () => {
    it('recovers from network errors', async () => {
      // First call fails, second succeeds
      mockApiClient.searchRepositories
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          repositories: [
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
          ],
          total_count: 1,
        })

      render(<App />)

      const searchInput = screen.getByPlaceholderText(/search repositories/i)
      const searchButton = screen.getByRole('button', { name: /search/i })

      // First attempt fails
      fireEvent.change(searchInput, { target: { value: 'test' } })
      fireEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })

      // Retry succeeds
      fireEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('owner/test-repo')).toBeInTheDocument()
      })
    })

    it('handles partial failures gracefully', async () => {
      mockApiClient.searchRepositories.mockResolvedValue({
        repositories: [
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
        ],
        total_count: 1,
      })

      mockApiClient.startIndexing.mockResolvedValue({
        task_id: 'task-123',
        status: 'pending',
        message: 'Indexing started',
      })

      mockApiClient.getIndexStatus.mockResolvedValue({
        task_id: 'task-123',
        status: 'failed',
        progress: {
          files_processed: 25,
          total_files: 100,
          percentage: 25.0,
        },
        percentage: 25.0,
        repository_url: 'https://github.com/owner/test-repo',
        error: 'Repository not found',
      })

      render(<App />)

      // Complete search and selection
      const searchInput = screen.getByPlaceholderText(/search repositories/i)
      const searchButton = screen.getByRole('button', { name: /search/i })

      fireEvent.change(searchInput, { target: { value: 'test' } })
      fireEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('owner/test-repo')).toBeInTheDocument()
      })

      const selectButton = screen.getByRole('button', { name: /select/i })
      fireEvent.click(selectButton)

      // Switch to indexing and start
      const indexTab = screen.getByText(/index/i).closest('button')
      fireEvent.click(indexTab!)

      const startIndexingButton = screen.getByRole('button', { name: /start indexing/i })
      fireEvent.click(startIndexingButton)

      // Wait for failure
      await waitFor(() => {
        expect(screen.getByText(/failed/i)).toBeInTheDocument()
      })

      // Should show error message
      expect(screen.getByText('Repository not found')).toBeInTheDocument()
    })
  })
})
