import { useState } from 'react'
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
import {
  Twitter, 
  Youtube, 
  Rss, 
  FileText, 
  Globe,
  Loader2,
  Github,
  MessageSquare
} from 'lucide-react'
import sourcesService, { CreateSourceData } from '../services/sources.service'
import { CredentialInput } from './CredentialInput'

interface AddSourceModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSourceAdded: () => void
}

interface SourceTypeOption {
  type: string
  label: string
  icon: any
  description: string
  requiresUrl: boolean
  urlPlaceholder?: string
}

const sourceTypes: SourceTypeOption[] = [
  {
    type: 'twitter',
    label: 'Twitter',
    icon: Twitter,
    description: 'Follow Twitter accounts and hashtags',
    requiresUrl: true,
    urlPlaceholder: 'https://twitter.com/username or @username',
  },
  {
    type: 'youtube',
    label: 'YouTube',
    icon: Youtube,
    description: 'Track YouTube channels',
    requiresUrl: true,
    urlPlaceholder: 'https://youtube.com/@channelname or channel URL',
  },
  {
    type: 'rss',
    label: 'RSS Feed',
    icon: Rss,
    description: 'Subscribe to any RSS/Atom feed',
    requiresUrl: true,
    urlPlaceholder: 'https://example.com/feed.xml',
  },
  {
    type: 'substack',
    label: 'Substack',
    icon: FileText,
    description: 'Follow Substack newsletters',
    requiresUrl: true,
    urlPlaceholder: 'https://example.substack.com',
  },
  {
    type: 'medium',
    label: 'Medium',
    icon: FileText,
    description: 'Track Medium publications or authors',
    requiresUrl: true,
    urlPlaceholder: 'https://medium.com/@username',
  },
  {
    type: 'github',
    label: 'GitHub',
    icon: Github,
    description: 'Track repository releases, commits, and issues',
    requiresUrl: false,
  },
  {
    type: 'reddit',
    label: 'Reddit',
    icon: MessageSquare,
    description: 'Follow subreddit discussions',
    requiresUrl: false,
  },
  {
    type: 'custom',
    label: 'Custom',
    icon: Globe,
    description: 'Add any other web source',
    requiresUrl: true,
    urlPlaceholder: 'https://example.com',
  },
]

export function AddSourceModal({ open, onOpenChange, onSourceAdded }: AddSourceModalProps) {
  const [step, setStep] = useState<'select' | 'configure'>('select')
  const [selectedType, setSelectedType] = useState<SourceTypeOption | null>(null)
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [config, setConfig] = useState<Record<string, any>>({})
  const [credentials, setCredentials] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClose = () => {
    setStep('select')
    setSelectedType(null)
    setName('')
    setUrl('')
    setConfig({})
    setCredentials({})
    setError(null)
    onOpenChange(false)
  }

  const handleSelectType = (type: SourceTypeOption) => {
    setSelectedType(type)
    setStep('configure')
    setError(null)
  }

  const handleBack = () => {
    setStep('select')
    setSelectedType(null)
    setName('')
    setUrl('')
    setConfig({})
    setCredentials({})
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedType) return
    
    if (!name.trim()) {
      setError('Please enter a name for this source')
      return
    }

    if (selectedType.requiresUrl && !url.trim()) {
      setError('Please enter a URL for this source')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data: CreateSourceData = {
        source_type: selectedType.type,
        name: name.trim(),
        url: url.trim() || undefined,
        config: config,
      }

      // Only include credentials if any are provided
      const hasCredentials = Object.values(credentials).some(val => val)
      if (hasCredentials) {
        data.credentials = credentials
      }

      await sourcesService.createSource(data)
      onSourceAdded()
      handleClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add source. Please try again.')
      console.error('Failed to add source:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col p-0">
        {step === 'select' && (
          <>
            <div className="px-6 pt-6 pb-4 border-b sticky top-0 bg-white z-10">
              <DialogHeader>
                <DialogTitle>Add Content Source</DialogTitle>
                <DialogDescription>
                  Choose the type of content source you want to connect
                </DialogDescription>
              </DialogHeader>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4">
              <div className="grid grid-cols-2 gap-3">
                {sourceTypes.map((type) => {
                  const Icon = type.icon
                  return (
                    <button
                      key={type.type}
                      onClick={() => handleSelectType(type)}
                      className="flex items-start gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
                    >
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Icon className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-1">{type.label}</h4>
                        <p className="text-xs text-gray-600">{type.description}</p>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="px-6 py-4 border-t sticky bottom-0 bg-white">
              <DialogFooter>
                <Button variant="outline" onClick={handleClose}>
                  Cancel
                </Button>
              </DialogFooter>
            </div>
          </>
        )}

        {step === 'configure' && selectedType && (
          <>
            <div className="px-6 pt-6 pb-4 border-b sticky top-0 bg-white z-10">
              <DialogHeader>
                <DialogTitle>Configure {selectedType.label} Source</DialogTitle>
                <DialogDescription>
                  Enter the details for your {selectedType.label.toLowerCase()} source
                </DialogDescription>
              </DialogHeader>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4">
              <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Source Name"
                placeholder={`My ${selectedType.label} Source`}
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                disabled={loading}
              />

              {selectedType.requiresUrl && (
                <Input
                  label="URL"
                  type="url"
                  placeholder={selectedType.urlPlaceholder}
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                  disabled={loading}
                />
              )}

              {/* Config Fields for YouTube */}
              {selectedType.type === 'youtube' && (
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
              {selectedType.type === 'github' && (
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
              {selectedType.type === 'reddit' && (
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
              {selectedType.type === 'twitter' && (
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
                  <div>
                    <Input
                      label="Max Results (per crawl)"
                      id="max_results"
                      type="number"
                      value={config.max_results || '10'}
                      onChange={(e) => setConfig({ ...config, max_results: parseInt(e.target.value) || 10 })}
                      placeholder="10"
                      min="5"
                      max="100"
                      disabled={loading}
                    />
                    <p className="text-xs text-gray-500 mt-1">Twitter API requires minimum 5 results</p>
                  </div>
                </>
              )}

              {/* Credential Input Component */}
              <CredentialInput
                sourceType={selectedType.type}
                credentials={credentials}
                onChange={setCredentials}
              />

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> This source will be crawled daily to discover new content for your newsletter.
                  {selectedType.type === 'twitter' && ' Twitter requires either Bearer Token (OAuth 2.0) or full OAuth 1.0a credentials (API Key, API Secret, Access Token, Access Token Secret).'}
                  {selectedType.type === 'youtube' && ' OAuth authentication will be required for YouTube sources.'}
                </p>
              </div>
              </form>
            </div>

            <div className="px-6 py-4 border-t sticky bottom-0 bg-white">
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={handleBack}
                  disabled={loading}
                >
                  Back
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    'Add Source'
                  )}
                </Button>
              </DialogFooter>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
