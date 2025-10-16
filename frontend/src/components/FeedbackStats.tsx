import { useEffect, useState } from 'react'
import { ThumbsUp, ThumbsDown, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import apiClient from '../services/api'

interface FeedbackStatsData {
  total_feedback: number
  thumbs_up_count: number
  thumbs_down_count: number
  positive_rate: number
  recent_feedback: any[]
}

export function FeedbackStats() {
  const [stats, setStats] = useState<FeedbackStatsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/feedback/stats')
      setStats(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch feedback stats')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Feedback Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">Loading...</p>
        </CardContent>
      </Card>
    )
  }

  if (error || !stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Feedback Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-600">{error || 'No data available'}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp size={20} />
          Feedback Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600 flex items-center justify-center gap-1">
              <ThumbsUp size={20} />
              {stats.thumbs_up_count}
            </div>
            <p className="text-sm text-gray-600 mt-1">Positive</p>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-red-600 flex items-center justify-center gap-1">
              <ThumbsDown size={20} />
              {stats.thumbs_down_count}
            </div>
            <p className="text-sm text-gray-600 mt-1">Negative</p>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {stats.positive_rate.toFixed(0)}%
            </div>
            <p className="text-sm text-gray-600 mt-1">Positive Rate</p>
          </div>
        </div>

        {stats.total_feedback === 0 && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 text-center">
              No feedback yet. Start providing feedback on your drafts to help improve future generations!
            </p>
          </div>
        )}

        {stats.total_feedback > 0 && stats.total_feedback < 5 && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Tip:</strong> Provide feedback on at least 5 drafts to enable AI-powered style improvements.
            </p>
          </div>
        )}

        {stats.total_feedback >= 5 && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              ✓ Your feedback is being used to improve future drafts!
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
