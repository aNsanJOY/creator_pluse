import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../services/api'
import { Navigation } from '../components/Navigation'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { FeedbackStats } from '../components/FeedbackStats'
import { FileText, Plus, Calendar, Send, Loader2 } from 'lucide-react'

interface Draft {
  id: string
  title: string
  status: string
  generated_at: string
  published_at?: string
  email_sent: boolean
  metadata: {
    topic_count?: number
    estimated_read_time?: string
  }
}

export default function Drafts() {
  const navigate = useNavigate()
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchDrafts()
  }, [])

  const fetchDrafts = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/drafts')
      setDrafts(response.data.drafts)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch drafts')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateDraft = async () => {
    try {
      setGenerating(true)
      setError('')
      
      const response = await apiClient.post('/api/drafts/generate', {
        topic_count: 5,
        days_back: 7,
        use_voice_profile: true,
        force_regenerate: false
      })

      if (response.data.status === 'ready') {
        // Navigate to the new draft
        navigate(`/drafts/${response.data.draft_id}`)
      } else if (response.data.status === 'generating') {
        // Navigate to the draft page which will poll for completion
        navigate(`/drafts/${response.data.draft_id}`)
      } else if (response.data.error === 'recent_draft_exists') {
        // Navigate to existing draft
        navigate(`/drafts/${response.data.draft_id}`)
      } else {
        setError(response.data.message || 'Failed to generate draft')
        setGenerating(false)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate draft')
      setGenerating(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const colors = {
      ready: 'bg-green-100 text-green-800',
      editing: 'bg-blue-100 text-blue-800',
      published: 'bg-purple-100 text-purple-800',
      failed: 'bg-red-100 text-red-800',
      generating: 'bg-yellow-100 text-yellow-800'
    }
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Navigation currentPage="Drafts" />
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Newsletter Drafts</h1>
          <p className="text-gray-600 mt-2">
            Review, edit, and publish your AI-generated newsletter drafts
          </p>
        </div>
        <Button
          onClick={handleGenerateDraft}
          disabled={generating}
          className="bg-indigo-600 hover:bg-indigo-700"
        >
          {generating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Plus className="mr-2 h-4 w-4" />
              Generate New Draft
            </>
          )}
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Feedback Stats */}
      <div className="mb-6">
        <FeedbackStats />
      </div>

      {drafts.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileText className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No drafts yet</h3>
            <p className="text-gray-600 text-center mb-6 max-w-md">
              Generate your first newsletter draft based on your trending content sources.
            </p>
            <Button
              onClick={handleGenerateDraft}
              disabled={generating}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              {generating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  Generate First Draft
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {drafts.map((draft) => (
            <Card
              key={draft.id}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => navigate(`/drafts/${draft.id}`)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl mb-2">{draft.title}</CardTitle>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {formatDate(draft.generated_at)}
                      </span>
                      {draft.metadata.topic_count && (
                        <span>{draft.metadata.topic_count} topics</span>
                      )}
                      {draft.metadata.estimated_read_time && (
                        <span>{draft.metadata.estimated_read_time} read</span>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(
                        draft.status
                      )}`}
                    >
                      {draft.status}
                    </span>
                    {draft.email_sent && (
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <Send className="h-3 w-3" />
                        Sent
                      </span>
                    )}
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}
      </div>
    </div>
  )
}
