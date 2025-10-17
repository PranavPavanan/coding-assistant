/**
 * Repository search component
 */
import { useState } from 'react'
import { Search, Loader2, ExternalLink, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAppStore, type Repository } from '@/store/appStore'
import { apiClient } from '@/services/api'

export function RepositorySearch() {
  const [query, setQuery] = useState('')
  const [error, setError] = useState<string | null>(null)

  const {
    searchResults,
    isSearching,
    selectedRepository,
    setSearchResults,
    setIsSearching,
    setSelectedRepository,
    setActiveTab,
  } = useAppStore()

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }

    setError(null)
    setIsSearching(true)

    try {
      const response = await apiClient.searchRepositories(query)
      setSearchResults(response.repositories || [])

      if (response.repositories?.length === 0) {
        setError('No repositories found')
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
          : 'Failed to search repositories'
      setError(errorDetail)
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  const handleSelectRepository = (repo: Repository) => {
    setSelectedRepository(repo)
    setActiveTab('indexing')
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Search GitHub Repositories</CardTitle>
          <CardDescription>Find a repository to analyze and query with AI</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search repositories (e.g., 'react', 'typescript orm', 'machine learning')"
                value={query}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
                className="pl-9"
                disabled={isSearching}
              />
            </div>
            <Button type="submit" disabled={isSearching}>
              {isSearching ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                'Search'
              )}
            </Button>
          </form>

          {error && (
            <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedRepository && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Selected Repository</span>
              <Button variant="ghost" size="sm" onClick={() => setSelectedRepository(null)}>
                Clear
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-lg">{selectedRepository.full_name}</h3>
                <a
                  href={selectedRepository.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline flex items-center gap-1"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
              {selectedRepository.description && (
                <p className="text-sm text-muted-foreground">{selectedRepository.description}</p>
              )}
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                {selectedRepository.language && (
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded-full bg-primary" />
                    {selectedRepository.language}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Star className="h-4 w-4" />
                  {selectedRepository.stars?.toLocaleString() || 0}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {searchResults.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold">Search Results ({searchResults.length})</h3>
          <div className="grid gap-3">
            {searchResults.map((repo) => (
              <Card
                key={repo.id}
                className="cursor-pointer hover:border-primary transition-colors"
                onClick={() => handleSelectRepository(repo)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold">{repo.full_name}</h4>
                        <a
                          href={repo.html_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-primary hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                      {repo.description && (
                        <p className="text-sm text-muted-foreground mt-1">{repo.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        {repo.language && (
                          <span className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-primary" />
                            {repo.language}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Star className="h-3 w-3" />
                          {repo.stars?.toLocaleString() || 0}
                        </span>
                      </div>
                    </div>
                    <Button size="sm">Select</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default RepositorySearch
