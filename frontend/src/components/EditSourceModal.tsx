import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from './ui/Dialog'
import { Button } from './ui/Button'
import { Input } from './ui/Input'
import { Loader2 } from 'lucide-react'
import sourcesService, { Source, UpdateSourceData } from '../services/sources.service'
import { CredentialInput } from './CredentialInput'

interface EditSourceModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  source: Source
  onSourceUpdated: () => void
}

export function EditSourceModal({ open, onOpenChange, source, onSourceUpdated }: EditSourceModalProps) {
  const [name, setName] = useState(source.name)
  const [url, setUrl] = useState(source.url || '')
  const [config, setConfig] = useState<Record<string, any>>(source.config || {})
  const [credentials, setCredentials] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setName(source.name)
      setUrl(source.url || '')
      setConfig(source.config || {})
      setCredentials({})
      setError(null)
    }
  }, [open, source])

  const handleClose = () => {
    setName(source.name)
    setUrl(source.url || '')
    setConfig(source.config || {})
    setCredentials({})
    setError(null)
    onOpenChange(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!name.trim()) {
      setError('Please enter a name for this source')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data: UpdateSourceData = {
        name: name.trim(),
        url: url.trim() || undefined,
        config: config,
      }

      // Only include credentials if any are provided
      const hasCredentials = Object.values(credentials).some(val => val)
      if (hasCredentials) {
        data.credentials = credentials
      }

      await sourcesService.updateSource(source.id, data)
      onSourceUpdated()
      handleClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update source. Please try again.')
      console.error('Failed to update source:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col p-0">
        <div className="px-6 pt-6 pb-4 border-b sticky top-0 bg-white z-10">
          <DialogHeader>
            <DialogTitle>Edit {source.source_type} Source</DialogTitle>
            <DialogDescription>
              Update the details for your {source.source_type.toLowerCase()} source
            </DialogDescription>
          </DialogHeader>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Source Name"
              placeholder={`My ${source.source_type} Source`}
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={loading}
            />

            {source.url !== undefined && (
              <Input
                label="URL"
                type="url"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
              />
            )}

            {/* Config Fields for YouTube */}
            {source.source_type === 'youtube' && (
              <>
                <Input
                  label="Channel ID or Handle *"
                  id="channel_id"
                  type="text"
                  value={config.channel_id || ''}
                  onChange={(e) => setConfig({ ...config, channel_id: e.target.value })}
                  placeholder="@channelhandle or UC_x5XG1OV2P6uZZ5FSM9Ttw"
                  required
                  disabled={loading}
                />
                <div>
                  <label htmlFor="fetch_type" className="block text-sm font-medium text-gray-700 mb-1">
                    Fetch Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="fetch_type"
                    value={config.fetch_type || ''}
                    onChange={(e) => setConfig({ ...config, fetch_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                    disabled={loading}
                  >
                    <option value="">Select Fetch Type</option>
                    <option value="uploads">Uploads</option>
                    <option value="liked">Liked</option>
                    <option value="subscriptions">Subscriptions</option>
                    <option value="playlist">Playlist</option>
                  </select>
                </div>
                <Input
                  label="Max Results (per crawl)"
                  id="max_results"
                  type="number"
                  value={config.max_results || '10'}
                  onChange={(e) => setConfig({ ...config, max_results: parseInt(e.target.value) || 10 })}
                  placeholder="10"
                  min="1"
                  max="50"
                  disabled={loading}
                />
              </>
            )}

            {/* Config Fields for GitHub */}
            {source.source_type === 'github' && (
              <>
                <Input
                  label="Repository *"
                  id="repository"
                  type="text"
                  value={config.repository || ''}
                  onChange={(e) => setConfig({ ...config, repository: e.target.value })}
                  placeholder="owner/repo (e.g., angular/angular)"
                  required
                  disabled={loading}
                />
                <div>
                  <label htmlFor="fetch_type" className="block text-sm font-medium text-gray-700 mb-1">
                    Fetch Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="fetch_type"
                    value={config.fetch_type || ''}
                    onChange={(e) => setConfig({ ...config, fetch_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                    disabled={loading}
                  >
                    <option value="">Select Fetch Type</option>
                    <option value="releases">Releases</option>
                    <option value="commits">Commits</option>
                    <option value="issues">Issues</option>
                    <option value="pull_requests">Pull Requests</option>
                  </select>
                </div>
                <Input
                  label="Max Results (per crawl)"
                  id="max_results"
                  type="number"
                  value={config.max_results || '10'}
                  onChange={(e) => setConfig({ ...config, max_results: parseInt(e.target.value) || 10 })}
                  placeholder="10"
                  min="1"
                  max="100"
                  disabled={loading}
                />
              </>
            )}

            {/* Config Fields for Reddit */}
            {source.source_type === 'reddit' && (
              <>
                <Input
                  label="Subreddit *"
                  id="subreddit"
                  type="text"
                  value={config.subreddit || ''}
                  onChange={(e) => setConfig({ ...config, subreddit: e.target.value })}
                  placeholder="Angular2 (without r/)"
                  required
                  disabled={loading}
                />
                <div>
                  <label htmlFor="fetch_type" className="block text-sm font-medium text-gray-700 mb-1">
                    Fetch Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="fetch_type"
                    value={config.fetch_type || ''}
                    onChange={(e) => setConfig({ ...config, fetch_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                    disabled={loading}
                  >
                    <option value="">Select Fetch Type</option>
                    <option value="hot">Hot</option>
                    <option value="new">New</option>
                    <option value="top">Top</option>
                    <option value="rising">Rising</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="time_filter" className="block text-sm font-medium text-gray-700 mb-1">
                    Time Filter (for "top" type)
                  </label>
                  <select
                    id="time_filter"
                    value={config.time_filter || 'week'}
                    onChange={(e) => setConfig({ ...config, time_filter: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loading}
                  >
                    <option value="hour">Hour</option>
                    <option value="day">Day</option>
                    <option value="week">Week</option>
                    <option value="month">Month</option>
                    <option value="year">Year</option>
                    <option value="all">All Time</option>
                  </select>
                </div>
                <Input
                  label="Max Results (per crawl)"
                  id="max_results"
                  type="number"
                  value={config.max_results || '20'}
                  onChange={(e) => setConfig({ ...config, max_results: parseInt(e.target.value) || 20 })}
                  placeholder="20"
                  min="1"
                  max="100"
                  disabled={loading}
                />
              </>
            )}

            {/* Config Fields for Twitter */}
            {source.source_type === 'twitter' && (
              <>
                <Input
                  label="Username *"
                  id="username"
                  type="text"
                  value={config.username || ''}
                  onChange={(e) => setConfig({ ...config, username: e.target.value })}
                  placeholder="elonmusk (without @)"
                  required
                  disabled={loading}
                />
                <div>
                  <label htmlFor="fetch_type" className="block text-sm font-medium text-gray-700 mb-1">
                    Fetch Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="fetch_type"
                    value={config.fetch_type || ''}
                    onChange={(e) => setConfig({ ...config, fetch_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                    disabled={loading}
                  >
                    <option value="">Select Fetch Type</option>
                    <option value="timeline">Timeline</option>
                    <option value="mentions">Mentions</option>
                    <option value="likes">Likes</option>
                    <option value="list">List</option>
                  </select>
                </div>
                <Input
                  label="Max Results (per crawl)"
                  id="max_results"
                  type="number"
                  value={config.max_results || '10'}
                  onChange={(e) => setConfig({ ...config, max_results: parseInt(e.target.value) || 10 })}
                  placeholder="10"
                  min="1"
                  max="100"
                  disabled={loading}
                />
              </>
            )}

            {/* Credential Input Component */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Update Credentials (Optional)</h3>
              <p className="text-xs text-gray-600 mb-3">
                Leave empty to keep existing credentials. Fill in to update.
              </p>
              <CredentialInput
                sourceType={source.source_type}
                credentials={credentials}
                onChange={setCredentials}
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
          </form>
        </div>

        <div className="px-6 py-4 border-t sticky bottom-0 bg-white">
          <DialogFooter>
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                'Update Source'
              )}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  )
}
