/**
 * WebSocket client service for real-time updates
 */

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

type MessageHandler = (data: unknown) => void
type ErrorHandler = (error: Event) => void
type CloseHandler = () => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private messageHandlers: Set<MessageHandler> = new Set()
  private errorHandlers: Set<ErrorHandler> = new Set()
  private closeHandlers: Set<CloseHandler> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000 // 1 second
  private isConnecting = false

  connect(taskId?: string) {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return
    }

    this.isConnecting = true
    const url = taskId ? `${WS_BASE_URL}/${taskId}` : WS_BASE_URL

    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        this.isConnecting = false
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.messageHandlers.forEach((handler) => handler(data))
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.errorHandlers.forEach((handler) => handler(error))
      }

      this.ws.onclose = () => {
        console.warn('WebSocket connection closed')
        this.isConnecting = false
        this.closeHandlers.forEach((handler) => handler())
        this.reconnect()
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      this.isConnecting = false
      this.reconnect()
    }
  }

  private reconnect() {
    if (
      this.reconnectAttempts < this.maxReconnectAttempts &&
      !this.isConnecting &&
      this.ws?.readyState !== WebSocket.OPEN
    ) {
      this.reconnectAttempts++
      setTimeout(() => {
        this.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  onMessage(handler: MessageHandler) {
    this.messageHandlers.add(handler)
  }

  onError(handler: ErrorHandler) {
    this.errorHandlers.add(handler)
  }

  onClose(handler: CloseHandler) {
    this.closeHandlers.add(handler)
  }

  removeMessageHandler(handler: MessageHandler) {
    this.messageHandlers.delete(handler)
  }

  removeErrorHandler(handler: ErrorHandler) {
    this.errorHandlers.delete(handler)
  }

  removeCloseHandler(handler: CloseHandler) {
    this.closeHandlers.delete(handler)
  }
}

const wsClient = new WebSocketClient()
export { wsClient }
export default wsClient
