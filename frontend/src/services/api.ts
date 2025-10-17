/**
 * API client service for backend communication
 */
import axios from 'axios'
import type { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 seconds
    })

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
    const response = await this.client.get('/index/stats')
    return response.data
  }

  // Clear index
  async clearIndex() {
    const response = await this.client.delete('/index/current')
    return response.data
  }

  // Chat query
  async chatQuery(query: string, conversationId?: string) {
    const response = await this.client.post('/chat/query', {
      query,
      conversation_id: conversationId,
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
}

// Singleton instance
export const apiClient = new ApiClient()
export default apiClient
