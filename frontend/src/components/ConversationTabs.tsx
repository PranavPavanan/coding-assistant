/**
 * Conversation tabs component for switching between chats
 */
import { Plus, X, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAppStore } from '@/store/appStore'

export function ConversationTabs() {
  const {
    conversations,
    currentConversation,
    switchToConversation,
    createNewConversation,
    updateConversation,
  } = useAppStore()

  const handleTabClick = (conversationId: string) => {
    switchToConversation(conversationId)
  }

  const handleNewChat = () => {
    createNewConversation()
  }

  const handleCloseTab = (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation()
    
    // Don't allow closing the last conversation
    if (conversations.length <= 1) {
      return
    }

    // If closing current conversation, switch to another one
    if (currentConversation?.id === conversationId) {
      const otherConversation = conversations.find(conv => conv.id !== conversationId)
      if (otherConversation) {
        switchToConversation(otherConversation.id)
      }
    }

    // Remove conversation from store
    const updatedConversations = conversations.filter(conv => conv.id !== conversationId)
    useAppStore.getState().setConversations(updatedConversations)
  }

  const generateConversationTitle = (conversation: typeof conversations[0]) => {
    if (conversation.title !== 'New Chat') {
      return conversation.title
    }

    // Generate title from first user message
    const firstUserMessage = conversation.messages.find(msg => msg.role === 'user')
    if (firstUserMessage) {
      const title = firstUserMessage.content.slice(0, 30)
      return title.length < firstUserMessage.content.length ? `${title}...` : title
    }

    return 'New Chat'
  }

  if (conversations.length === 0) {
    return null
  }

  return (
    <div className="flex items-center gap-1 p-2 bg-muted/50 border-b">
      <div className="flex items-center gap-1 overflow-x-auto scrollbar-thin">
        {conversations.map((conversation) => (
          <div
            key={conversation.id}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors
              min-w-0 flex-shrink-0
              ${
                currentConversation?.id === conversation.id
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-background hover:bg-muted'
              }
            `}
            onClick={() => handleTabClick(conversation.id)}
          >
            <MessageSquare className="h-4 w-4 flex-shrink-0" />
            <span className="text-sm font-medium truncate max-w-32">
              {generateConversationTitle(conversation)}
            </span>
            {conversations.length > 1 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-4 w-4 p-0 hover:bg-destructive hover:text-destructive-foreground"
                onClick={(e) => handleCloseTab(e, conversation.id)}
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>
        ))}
      </div>
      
      <Button
        variant="outline"
        size="sm"
        onClick={handleNewChat}
        className="flex-shrink-0"
      >
        <Plus className="h-4 w-4" />
        <span className="ml-1 hidden sm:inline">New Chat</span>
      </Button>
    </div>
  )
}

export default ConversationTabs
