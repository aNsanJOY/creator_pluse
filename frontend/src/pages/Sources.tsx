import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Navigation } from '../components/Navigation'
import { Plus, AlertCircle, Loader2, RefreshCw } from 'lucide-react'
import sourcesService, { Source } from '../services/sources.service'
import { SourceCard } from '../components/SourceCard'
import { AddSourceModal } from '../components/AddSourceModal'
import apiClient from '../services/api'

export function Sources() {
  const navigate = useNavigate()
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [reactivatingAll, setReactivatingAll] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const loadSources = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await sourcesService.getSources()
      setSources(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load sources')
      console.error('Failed to load sources:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSources()
  }, [])

  const handleDeleteSource = async (id: string) => {
    try {
      await sourcesService.deleteSource(id)
      setSources(sources.filter(source => source.id !== id))
    } catch (err: any) {
      console.error('Failed to delete source:', err)
      alert(err.response?.data?.detail || 'Failed to delete source')
    }
  }

  const handleSourceAdded = () => {
    setIsAddModalOpen(false)
    loadSources()
  }

  const handleReactivate = () => {
    // Reload sources to reflect the status change
    loadSources()
    setSuccessMessage('Source reactivated successfully')
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  const handleReactivateAll = async () => {
    try {
      setReactivatingAll(true)
      setError(null)
      const response = await apiClient.post('/api/crawl/reactivate-all')
      setSuccessMessage(response.data.message)
      setTimeout(() => setSuccessMessage(null), 5000)
      loadSources()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reactivate sources')
    } finally {
      setReactivatingAll(false)
    }
  }

  const errorSourcesCount = sources.filter(s => s.status === 'error').length

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <Navigation currentPage="Sources" />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Content Sources
            </h2>
            <p className="text-gray-600">
              Connect your favorite sources to curate amazing newsletter content.
            </p>
          </div>
          <div className="flex gap-3">
            {errorSourcesCount > 0 && (
              <Button
                variant="outline"
                onClick={handleReactivateAll}
                disabled={reactivatingAll}
                className="flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${reactivatingAll ? 'animate-spin' : ''}`} />
                {reactivatingAll ? 'Reactivating...' : `Reactivate All (${errorSourcesCount})`}
              </Button>
            )}
            <Button
              onClick={() => setIsAddModalOpen(true)}
              className="flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Add Source
            </Button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <Card className="mb-6 border-l-4 border-red-500">
            <CardContent className="flex items-center gap-3 py-4">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <p className="text-red-700">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Success Message */}
        {successMessage && (
          <Card className="mb-6 border-l-4 border-green-500 bg-green-50">
            <CardContent className="flex items-center gap-3 py-4">
              <RefreshCw className="w-5 h-5 text-green-600" />
              <p className="text-green-700">{successMessage}</p>
            </CardContent>
          </Card>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
        )}

        {/* Empty State */}
        {!loading && sources.length === 0 && (
          <Card className="text-center py-12">
            <CardContent>
              <div className="max-w-md mx-auto">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Plus className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  No sources connected yet
                </h3>
                <p className="text-gray-600 mb-6">
                  Get started by connecting your first content source. You can add Twitter accounts, YouTube channels, RSS feeds, and more.
                </p>
                <Button onClick={() => setIsAddModalOpen(true)}>
                  <Plus className="w-5 h-5 mr-2" />
                  Add Your First Source
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Sources Grid */}
        {!loading && sources.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sources.map((source) => (
              <SourceCard
                key={source.id}
                source={source}
                onDelete={handleDeleteSource}
                onReactivate={handleReactivate}
                onUpdate={loadSources}
              />
            ))}
          </div>
        )}

        {/* Info Card */}
        {!loading && sources.length > 0 && (
          <Card className="mt-8 bg-blue-50 border border-blue-200">
            <CardHeader>
              <CardTitle className="text-blue-900">About Content Sources</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-blue-800">
                <li className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5"></div>
                  <span>Sources are crawled daily to discover trending content for your newsletter</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5"></div>
                  <span>You can connect multiple sources of the same type (e.g., multiple Twitter accounts)</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5"></div>
                  <span>Sources marked as "error" need to be reconnected or have invalid credentials</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        )}
      </main>

      {/* Add Source Modal */}
      <AddSourceModal
        open={isAddModalOpen}
        onOpenChange={setIsAddModalOpen}
        onSourceAdded={handleSourceAdded}
      />
    </div>
  )
}
