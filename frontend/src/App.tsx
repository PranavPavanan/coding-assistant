import { TabNavigation } from './components/TabNavigation'
import { RepositorySearch } from './components/RepositorySearch'
import { IndexingProgress } from './components/IndexingProgress'
import { ChatInterface } from './components/ChatInterface'
import { useAppStore } from './store/appStore'
import { Github, Sparkles } from 'lucide-react'

function App() {
  const { activeTab } = useAppStore()

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-purple-50 dark:from-gray-950 dark:via-purple-950/20 dark:to-gray-950">
      {/* Header with gradient */}
      <header className="border-b border-purple-200 dark:border-purple-900/50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-violet-600 text-white p-2.5 rounded-xl shadow-lg">
              <Github className="h-6 w-6" />
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-violet-600 bg-clip-text text-transparent">
                RAG GitHub Assistant
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                AI-powered code exploration and intelligent Q&A
              </p>
            </div>
          </div>
        </div>
      </header>

      <TabNavigation />

      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="animate-in fade-in duration-500">
          {activeTab === 'search' && <RepositorySearch />}
          {activeTab === 'indexing' && <IndexingProgress />}
          {activeTab === 'chat' && (
            <div className="h-[calc(100vh-280px)]">
              <ChatInterface />
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-purple-200 dark:border-purple-900/50 mt-auto">
        <div className="container mx-auto px-4 py-4 text-center text-sm text-muted-foreground">
          <p>Built with ❤️ using React, FastAPI, and CodeLlama</p>
        </div>
      </footer>
    </div>
  )
}

export default App
