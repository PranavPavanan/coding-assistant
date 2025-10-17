/**
 * Indexing progress component
 */
import { useEffect, useState } from 'react'
import { Loader2, CheckCircle2, XCircle, AlertCircle, Play } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useAppStore, type IndexingTask } from '@/store/appStore'
import { apiClient } from '@/services/api'
import { wsClient } from '@/services/websocket'

export function IndexingProgress() {
  const [error, setError] = useState<string | null>(null)
  const [urlInput, setUrlInput] = useState('')

  const {
    selectedRepository,
    currentIndexingTask,
    isIndexing,
    indexStats,
    setCurrentIndexingTask,
    setIsIndexing,
    setIndexStats,
    setActiveTab,
  } = useAppStore()

  // Poll for indexing status
  useEffect(() => {
    if (!currentIndexingTask?.task_id) return

    const interval = setInterval(async () => {
      try {
        const status = await apiClient.getIndexStatus(currentIndexingTask.task_id)
        setCurrentIndexingTask(status)

        if (status.status === 'completed' || status.status === 'failed') {
          setIsIndexing(false)
          clearInterval(interval)

          // Refresh index stats
          const stats = await apiClient.getIndexStats()
          setIndexStats(stats)
        }
      } catch (err) {
        console.error('Failed to fetch indexing status:', err)
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentIndexingTask?.task_id])

  // WebSocket updates (optional, if backend implements)
  useEffect(() => {
    if (!currentIndexingTask?.task_id) return

    const handler = (data: unknown) => {
      if (
        data &&
        typeof data === 'object' &&
        'task_id' in data &&
        data.task_id === currentIndexingTask.task_id
      ) {
        setCurrentIndexingTask(data as IndexingTask)
      }
    }

    wsClient.onMessage(handler)
    wsClient.connect(currentIndexingTask.task_id)

    return () => {
      wsClient.removeMessageHandler(handler)
      wsClient.disconnect()
    }
  }, [currentIndexingTask?.task_id, setCurrentIndexingTask])

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleStartIndexing = async () => {
    const url = selectedRepository?.html_url || urlInput

    if (!url) {
      setError('Please select a repository or enter a URL')
      return
    }

    setError(null)
    setIsIndexing(true)

    try {
      const response = await apiClient.startIndexing(url)
      setCurrentIndexingTask(response)
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
          : 'Failed to start indexing'
      setError(errorDetail)
      setIsIndexing(false)
    }
  }

  const handleClearIndex = async () => {
    if (!confirm('Are you sure you want to clear the index?')) {
      return
    }

    try {
      await apiClient.clearIndex()
      setIndexStats(null)
      setCurrentIndexingTask(null)
      setError(null)
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
          : 'Failed to clear index'
      setError(errorDetail)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
      default:
        return <AlertCircle className="h-5 w-5 text-yellow-500" />
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Repository Indexing</CardTitle>
          <CardDescription>Index a repository to enable AI-powered code queries</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {selectedRepository ? (
            <div className="p-4 bg-muted rounded-md">
              <p className="text-sm font-medium">Selected Repository:</p>
              <p className="text-lg font-semibold">{selectedRepository.full_name}</p>
            </div>
          ) : (
            <div className="space-y-2">
              <label className="text-sm font-medium">Repository URL</label>
              <input
                type="text"
                placeholder="https://github.com/owner/repo"
                value={urlInput}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUrlInput(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                disabled={isIndexing}
              />
            </div>
          )}

          <Button
            onClick={handleStartIndexing}
            disabled={isIndexing || (!selectedRepository && !urlInput)}
            className="w-full"
          >
            {isIndexing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Indexing in Progress...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Start Indexing
              </>
            )}
          </Button>

          {error && (
            <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm">{error}</div>
          )}
        </CardContent>
      </Card>

      {currentIndexingTask && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                {getStatusIcon(currentIndexingTask.status)}
                Indexing Status
              </span>
              <span className="text-sm font-normal capitalize">{currentIndexingTask.status}</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Progress</span>
                <span>{currentIndexingTask.progress.percentage.toFixed(1)}%</span>
              </div>
              <Progress value={currentIndexingTask.progress.percentage} />
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Files Processed</p>
                <p className="font-semibold">{currentIndexingTask.progress.files_processed}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Total Files</p>
                <p className="font-semibold">{currentIndexingTask.progress.total_files}</p>
              </div>
            </div>

            {currentIndexingTask.error && (
              <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                {currentIndexingTask.error}
              </div>
            )}

            {currentIndexingTask.status === 'completed' && (
              <Button onClick={() => setActiveTab('chat')} className="w-full">
                Start Querying
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {indexStats?.is_indexed && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Current Index</span>
              <Button variant="destructive" size="sm" onClick={handleClearIndex}>
                Clear Index
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Repository</p>
                <p className="font-semibold">{indexStats.repository_name || 'Unknown'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Files Indexed</p>
                <p className="font-semibold">{indexStats.file_count}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Vectors</p>
                <p className="font-semibold">{indexStats.vector_count}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default IndexingProgress
