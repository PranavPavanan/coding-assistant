/**
 * Tab navigation component
 */
import { Search, Database, MessageSquare } from 'lucide-react'
import { cn } from '@/utils/cn'
import { useAppStore } from '@/store/appStore'

export function TabNavigation() {
  const { activeTab, setActiveTab, indexStats } = useAppStore()

  const tabs = [
    {
      id: 'search' as const,
      label: 'Search',
      icon: Search,
      description: 'Find repositories',
    },
    {
      id: 'indexing' as const,
      label: 'Index',
      icon: Database,
      description: 'Index repository',
    },
    {
      id: 'chat' as const,
      label: 'Query',
      icon: MessageSquare,
      description: 'Ask questions',
      disabled: !indexStats?.is_indexed,
    },
  ]

  return (
    <div className="border-b">
      <div className="container mx-auto">
        <nav className="flex gap-1">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => !tab.disabled && setActiveTab(tab.id)}
                disabled={tab.disabled}
                className={cn(
                  'flex items-center gap-2 px-6 py-4 border-b-2 transition-colors',
                  activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground',
                  tab.disabled && 'opacity-50 cursor-not-allowed'
                )}
              >
                <Icon className="h-4 w-4" />
                <div className="text-left">
                  <div className="font-medium">{tab.label}</div>
                  <div className="text-xs opacity-70">{tab.description}</div>
                </div>
              </button>
            )
          })}
        </nav>
      </div>
    </div>
  )
}

export default TabNavigation
