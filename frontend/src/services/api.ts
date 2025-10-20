/**
 * API client service for backend communication
 */
import axios from 'axios'
import type { AxiosInstance } from 'axios'

const API_BASE_URL = '/api'

console.log('🔍 DEBUG: VITE_API_URL from env:', import.meta.env.VITE_API_URL)
console.log('🔍 DEBUG: Final API_BASE_URL:', API_BASE_URL)

class ApiClient {
  private client: AxiosInstance

  constructor() {
    console.log('🔍 DEBUG: Creating ApiClient with baseURL:', API_BASE_URL)
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 120000, // increase from 30000
    })
    console.log('🔍 DEBUG: Axios client created with baseURL:', this.client.defaults.baseURL)

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error)
        return Promise.reject(error)
      }
    )
  }

  // Health check
  async healthCheck() {
    const response = await this.client.get('/health')
    return response.data
  }

  // Repository search
  async searchRepositories(query: string, language?: string, minStars?: number) {
    const response = await this.client.post('/search/repositories', {
      query,
      language,
      min_stars: minStars,
    })
    return response.data
  }

  // Validate repository URL
  async validateRepositoryUrl(url: string) {
    const response = await this.client.post('/validate/url', { url })
    return response.data
  }

  // Get repository details
  async getRepository(repoId: string) {
    const response = await this.client.get(`/repositories/${repoId}`)
    return response.data
  }

  // Start indexing
  async startIndexing(repositoryUrl: string, branch?: string) {
    const response = await this.client.post('/index/start', {
      repository_url: repositoryUrl,
      branch,
    })
    return response.data
  }

  // Get indexing status
  async getIndexStatus(taskId: string) {
    const response = await this.client.get(`/index/status/${taskId}`)
    return response.data
  }

  // Get index stats
  async getIndexStats() {
    console.log('🔍 DEBUG: API Base URL:', this.client.defaults.baseURL)
    console.log('🔍 DEBUG: Full URL will be:', this.client.defaults.baseURL + '/index/stats')
    console.log('🔍 DEBUG: Environment VITE_API_URL:', import.meta.env.VITE_API_URL)
    const response = await this.client.get('/index/stats')
    return response.data
  }

  // Clear index
  async clearIndex() {
    const response = await this.client.delete('/index/current')
    return response.data
  }

  // Chat query
  async chatQuery(query: string, conversationId?: string, sessionId?: string) {
    const response = await this.client.post('/chat/query', {
      query,
      conversation_id: conversationId,
      session_id: sessionId,
    })
    return response.data
  }

  // Get chat history
  async getChatHistory(conversationId: string, limit?: number) {
    const response = await this.client.get('/chat/history', {
      params: {
        conversation_id: conversationId,
        limit,
      },
    })
    return response.data
  }

  // Get chat context
  async getChatContext(conversationId: string) {
    const response = await this.client.get('/chat/context', {
      params: {
        conversation_id: conversationId,
      },
    })
    return response.data
  }

  // Clear chat history
  async clearChatHistory(conversationId?: string) {
    const response = await this.client.delete('/chat/history', {
      params: conversationId ? { conversation_id: conversationId } : {},
    })
    return response.data
  }

  // Session management
  async clearSession(sessionId: string, clearAll: boolean = false) {
    const response = await this.client.post('/chat/session/clear', {
      session_id: sessionId,
      clear_all: clearAll,
    })
    return response.data
  }

  async getSessionInfo(sessionId: string) {
    const response = await this.client.get(`/chat/session/${sessionId}`)
    return response.data
  }

  async getConversationInfo(conversationId: string) {
    const response = await this.client.get(`/chat/conversation/${conversationId}`)
    return response.data
  }

  async listConversationsInSession(sessionId: string) {
    const response = await this.client.get(`/chat/session/${sessionId}/conversations`)
    return response.data
  }

  async listSessions() {
    const response = await this.client.get('/chat/sessions')
    return response.data
  }
}

// Singleton instance
export const apiClient = new ApiClient()
export default apiClient
