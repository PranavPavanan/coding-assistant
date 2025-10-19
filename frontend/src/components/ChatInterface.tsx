/**
 * Chat interface component for querying code
 */
import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Code, FileText, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAppStore } from '@/store/appStore'
import { apiClient } from '@/services/api'
import { ConversationTabs } from '@/components/ConversationTabs'

export function ChatInterface() {
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const {
    messages,
    conversationId,
    sessionId,
    currentConversation,
    conversations,
    isQuerying,
    indexStats,
    addMessage,
    setConversationId,
    setSessionId,
    setCurrentConversation,
    createNewConversation,
    updateConversation,
    setIsQuerying,
    clearMessages,
    setIndexStats,
  } = useAppStore()

  // Load index stats on mount
  useEffect(() => {
    const loadIndexStats = async () => {
      try {
        const stats = await apiClient.getIndexStats()
        setIndexStats(stats)
      } catch (err) {
        console.error('Failed to load index stats:', err)
      }
    }
    loadIndexStats()
  }, [setIndexStats])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim()) {
      return
    }

    if (!indexStats?.is_indexed) {
      setError('Please index a repository first')
      return
    }

    const userMessage = {
      role: 'user' as const,
      content: input,
      timestamp: new Date().toISOString(),
    }

    addMessage(userMessage)
    setInput('')
    setError(null)
    setIsQuerying(true)

    try {
      const response = await apiClient.chatQuery(
        input, 
        conversationId || undefined, 
        sessionId || undefined
      )

      // Handle session and conversation IDs
      if (!sessionId) {
        setSessionId(response.session_id)
      }
      
      if (!conversationId) {
        setConversationId(response.conversation_id)
        
        // Create new conversation if this is the first message
        if (!currentConversation) {
          const newConversation = {
            id: response.conversation_id,
            title: 'New Chat',
            messages: [userMessage],
            createdAt: new Date().toISOString(),
            lastActivity: new Date().toISOString()
          }
          setCurrentConversation(newConversation)
        }
      }

      const assistantMessage = {
        role: 'assistant' as const,
        content: response.answer || response.response,
        timestamp: new Date().toISOString(),
        sources: response.sources || response.references,
      }

      addMessage(assistantMessage)
      
      // Update conversation title based on first user message
      if (currentConversation && currentConversation.title === 'New Chat' && currentConversation.messages.length === 1) {
        const title = input.slice(0, 30)
        updateConversation(currentConversation.id, {
          title: title.length < input.length ? `${title}...` : title
        })
      }
    } catch (err: unknown) {
      const errorDetail =
        err &&
        typeof err === 'object' &&
        'response' in err &&
        err.response &&
        typeof err.response === 'object' &&
        'data' in err.response &&
        err.response.data &&
        typeof err.response.data === 'object' &&
        'detail' in err.response.data
          ? String(err.response.data.detail)
          : 'Failed to process query'
      setError(errorDetail)
      setIsQuerying(false)
    } finally {
      setIsQuerying(false)
    }
  }

  const handleClearChat = () => {
    if (confirm('Clear current conversation?')) {
      clearMessages()
      setError(null)
    }
  }

  const handleNewChat = () => {
    createNewConversation()
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      
      {/* Conversation Tabs */}
      {conversations.length > 0 && <ConversationTabs />}
      
      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>AI Code Assistant</CardTitle>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleNewChat}
            >
              <Plus className="h-4 w-4 mr-1" />
              New Chat
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearChat}
              disabled={messages.length === 0}
            >
              Clear Chat
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden flex flex-col p-0">
          {!indexStats?.is_indexed ? (
            <div className="flex-1 flex items-center justify-center p-6 text-center">
              <div className="space-y-2">
                <p className="text-muted-foreground">No repository indexed yet</p>
                <p className="text-sm text-muted-foreground">
                  Please search for and index a repository to start querying
                </p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex-1 flex items-center justify-center p-6 text-center">
              <div className="space-y-2">
                <p className="font-medium">Ask me anything about the code!</p>
                <p className="text-sm text-muted-foreground">
                  Examples: "How does authentication work?", "Explain the main function", "Where is
                  the database configured?"
                </p>
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${
                      message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>

                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border/50 space-y-2">
                        <p className="text-xs font-medium opacity-70">Sources:</p>
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="text-xs bg-background/50 rounded p-2 space-y-1">
                            <div className="flex items-center gap-2">
                              <FileText className="h-3 w-3" />
                              <span className="font-mono">{source.file_path}</span>
                              <span className="opacity-70">
                                (lines {source.start_line}-{source.end_line})
                              </span>
                            </div>
                            <pre className="text-xs bg-background/30 rounded p-2 overflow-x-auto">
                              <code>{source.content.substring(0, 200)}...</code>
                            </pre>
                          </div>
                        ))}
                      </div>
                    )}

                    <p className="text-xs opacity-50 mt-2">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}

              {isQuerying && (
                <div className="flex justify-start">
                  <div className="max-w-[80%] rounded-lg p-4 bg-muted">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}

          {error && (
            <div className="mx-6 mb-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
              {error}
            </div>
          )}

          {/* Repository name display above query input */}
          {indexStats?.is_indexed && indexStats.repository_name && (
            <div className="px-6 py-3 bg-muted/50 border-t">
              <div className="flex items-center gap-2 text-sm">
                <Code className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">What do you want to know about</span>
                <span className="font-semibold text-foreground">{indexStats.repository_name}</span>
                <span className="text-muted-foreground">?</span>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="p-6 border-t">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder={
                  indexStats?.is_indexed
                    ? `Ask a question about ${indexStats.repository_name || 'the code'}...`
                    : 'Index a repository first...'
                }
                value={input}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
                disabled={isQuerying || !indexStats?.is_indexed}
                className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
              <Button
                type="submit"
                disabled={isQuerying || !input.trim() || !indexStats?.is_indexed}
              >
                {isQuerying ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {indexStats?.is_indexed && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Code className="h-4 w-4" />
              <span>
                Querying:{' '}
                <span className="font-medium text-foreground">
                  {indexStats.repository_name || 'Unknown'}
                </span>
              </span>
              <span className="ml-auto">{indexStats.file_count} files indexed</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ChatInterface
