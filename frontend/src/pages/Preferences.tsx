import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { ArrowLeft, Save, RotateCcw, AlertCircle, CheckCircle } from 'lucide-react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Preferences {
  draft_schedule_time: string
  newsletter_frequency: string
  content_preferences: {
    topics_to_include: string[]
    topics_to_exclude: string[]
    min_content_age_hours: number
    max_content_age_days: number
    preferred_sources: string[]
  }
  tone_preferences: {
    formality: string
    enthusiasm: string
    use_emojis: boolean
    length_preference: string
  }
  notification_preferences: {
    email_on_draft_ready: boolean
    email_on_publish_success: boolean
    email_on_errors: boolean
    weekly_summary: boolean
  }
  email_preferences: {
    default_subject_template: string
    include_preview_text: boolean
    track_opens: boolean
    track_clicks: boolean
  }
}

export function Preferences() {
  const navigate = useNavigate()
  const [preferences, setPreferences] = useState<Preferences | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    fetchPreferences()
  }, [])

  const fetchPreferences = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      
      const response = await axios.get(`${API_URL}/api/preferences`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      setPreferences(response.data.preferences)
      setError(null)
    } catch (err: any) {
      console.error('Failed to fetch preferences:', err)
      setError('Failed to load preferences')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!preferences) return

    try {
      setSaving(true)
      setError(null)
      setSuccess(null)
      const token = localStorage.getItem('access_token')
      
      await axios.put(`${API_URL}/api/preferences`, preferences, {
        headers: { Authorization: `Bearer ${token}` }
      })

      setSuccess('Preferences saved successfully!')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: any) {
      console.error('Failed to save preferences:', err)
      setError(err.response?.data?.detail || 'Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset all preferences to defaults?')) {
      return
    }

    try {
      setSaving(true)
      setError(null)
      const token = localStorage.getItem('access_token')
      
      const response = await axios.post(`${API_URL}/api/preferences/reset`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })

      setPreferences(response.data.preferences)
      setSuccess('Preferences reset to defaults!')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: any) {
      console.error('Failed to reset preferences:', err)
      setError('Failed to reset preferences')
    } finally {
      setSaving(false)
    }
  }

  const updatePreference = (path: string, value: any) => {
    if (!preferences) return

    const keys = path.split('.')
    const newPreferences = { ...preferences }
    let current: any = newPreferences

    for (let i = 0; i < keys.length - 1; i++) {
      current[keys[i]] = { ...current[keys[i]] }
      current = current[keys[i]]
    }

    current[keys[keys.length - 1]] = value
    setPreferences(newPreferences)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-gray-600">Loading preferences...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            <h1 className="text-2xl font-bold text-gray-900">Preferences</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              disabled={saving}
              className="flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              Reset to Defaults
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 text-red-800">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 text-green-800">
              <CheckCircle className="w-5 h-5" />
              <span>{success}</span>
            </div>
          </div>
        )}

        <div className="space-y-6">
          {/* Draft Schedule */}
          <Card>
            <CardHeader>
              <CardTitle>Draft Schedule</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Daily Draft Generation Time
                </label>
                <input
                  type="time"
                  value={preferences?.draft_schedule_time || '08:00'}
                  onChange={(e) => updatePreference('draft_schedule_time', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-sm text-gray-600 mt-1">
                  Time when daily newsletter drafts will be generated
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Newsletter Frequency
                </label>
                <select
                  value={preferences?.newsletter_frequency || 'daily'}
                  onChange={(e) => updatePreference('newsletter_frequency', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Content Preferences */}
          <Card>
            <CardHeader>
              <CardTitle>Content Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Maximum Content Age (days)
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={preferences?.content_preferences.max_content_age_days || 7}
                  onChange={(e) => updatePreference('content_preferences.max_content_age_days', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-sm text-gray-600 mt-1">
                  Only include content from the last X days
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Tone Preferences */}
          <Card>
            <CardHeader>
              <CardTitle>Tone & Style</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Formality
                </label>
                <select
                  value={preferences?.tone_preferences.formality || 'balanced'}
                  onChange={(e) => updatePreference('tone_preferences.formality', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="casual">Casual</option>
                  <option value="balanced">Balanced</option>
                  <option value="formal">Formal</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enthusiasm
                </label>
                <select
                  value={preferences?.tone_preferences.enthusiasm || 'moderate'}
                  onChange={(e) => updatePreference('tone_preferences.enthusiasm', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">Low</option>
                  <option value="moderate">Moderate</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Length Preference
                </label>
                <select
                  value={preferences?.tone_preferences.length_preference || 'medium'}
                  onChange={(e) => updatePreference('tone_preferences.length_preference', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="short">Short</option>
                  <option value="medium">Medium</option>
                  <option value="long">Long</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="use_emojis"
                  checked={preferences?.tone_preferences.use_emojis || false}
                  onChange={(e) => updatePreference('tone_preferences.use_emojis', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="use_emojis" className="text-sm font-medium text-gray-700">
                  Use emojis in newsletters
                </label>
              </div>
            </CardContent>
          </Card>

          {/* Notification Preferences */}
          <Card>
            <CardHeader>
              <CardTitle>Notifications</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="email_on_draft_ready"
                  checked={preferences?.notification_preferences.email_on_draft_ready || false}
                  onChange={(e) => updatePreference('notification_preferences.email_on_draft_ready', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="email_on_draft_ready" className="text-sm font-medium text-gray-700">
                  Email me when a draft is ready
                </label>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="email_on_publish_success"
                  checked={preferences?.notification_preferences.email_on_publish_success || false}
                  onChange={(e) => updatePreference('notification_preferences.email_on_publish_success', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="email_on_publish_success" className="text-sm font-medium text-gray-700">
                  Email me when a newsletter is published
                </label>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="email_on_errors"
                  checked={preferences?.notification_preferences.email_on_errors || false}
                  onChange={(e) => updatePreference('notification_preferences.email_on_errors', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="email_on_errors" className="text-sm font-medium text-gray-700">
                  Email me about errors
                </label>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="weekly_summary"
                  checked={preferences?.notification_preferences.weekly_summary || false}
                  onChange={(e) => updatePreference('notification_preferences.weekly_summary', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="weekly_summary" className="text-sm font-medium text-gray-700">
                  Send weekly summary
                </label>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
