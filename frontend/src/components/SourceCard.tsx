import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { Button } from './ui/Button'
import { 
  Twitter, 
  Youtube, 
  Rss, 
  FileText, 
  Trash2, 
  ExternalLink,
  CheckCircle,
  AlertCircle,
  Clock,
  Globe,
  RefreshCw,
  Edit
} from 'lucide-react'
import { Source } from '../services/sources.service'
import apiClient from '../services/api'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from './ui/Dialog'
import { EditSourceModal } from './EditSourceModal'

interface SourceCardProps {
  source: Source
  onDelete: (id: string) => void
  onReactivate?: (id: string) => void
  onUpdate?: () => void
}

const sourceIcons: Record<string, any> = {
  twitter: Twitter,
  youtube: Youtube,
  rss: Rss,
  substack: FileText,
  medium: FileText,
  linkedin: Globe,
  podcast: Rss,
  newsletter: FileText,
  custom: Globe,
}

const sourceColors: Record<string, string> = {
  twitter: 'text-blue-400 bg-blue-50',
  youtube: 'text-red-500 bg-red-50',
  rss: 'text-orange-500 bg-orange-50',
  substack: 'text-purple-500 bg-purple-50',
  medium: 'text-green-600 bg-green-50',
  linkedin: 'text-blue-700 bg-blue-50',
  podcast: 'text-indigo-500 bg-indigo-50',
  newsletter: 'text-pink-500 bg-pink-50',
  custom: 'text-gray-600 bg-gray-50',
}

export function SourceCard({ source, onDelete, onReactivate, onUpdate }: SourceCardProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [reactivating, setReactivating] = useState(false)
  const [crawling, setCrawling] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const Icon = sourceIcons[source.source_type.toLowerCase()] || Globe
  const colorClass = sourceColors[source.source_type.toLowerCase()] || 'text-gray-600 bg-gray-50'

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await onDelete(source.id)
      setShowDeleteDialog(false)
    } catch (error) {
      console.error('Delete failed:', error)
    } finally {
      setDeleting(false)
    }
  }

  const handleReactivate = async () => {
    setReactivating(true)
    setError('')
    try {
      await apiClient.post(`/api/crawl/reactivate/${source.id}`)
      if (onReactivate) {
        onReactivate(source.id)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reactivate source')
      console.error('Reactivate failed:', err)
    } finally {
      setReactivating(false)
    }
  }

  const handleCrawl = async () => {
    setCrawling(true)
    setError('')
    setSuccess('')
    try {
      await apiClient.post(`/api/sources/${source.id}/crawl`)
      setSuccess('Crawl triggered successfully!')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to trigger crawl')
      console.error('Crawl failed:', err)
    } finally {
      setCrawling(false)
    }
  }

  const handleSourceUpdated = () => {
    if (onUpdate) {
      onUpdate()
    }
  }

  const getStatusIcon = () => {
    switch (source.status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />
      default:
        return null
    }
  }

  const getStatusText = () => {
    switch (source.status) {
      case 'active':
        return 'Active'
      case 'error':
        return 'Error'
      case 'pending':
        return 'Pending'
      default:
        return source.status
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never'
    
    // Parse the date string properly (handles ISO 8601 with timezone)
    const date = new Date(dateString)
    
    // Check if date is valid
    if (isNaN(date.getTime())) return 'Invalid date'
    
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    // Handle future dates (clock skew or timezone issues)
    if (diffMs < -60000) { // More than 1 minute in the future
      return 'Scheduled'
    }

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  const getNextSyncTime = () => {
    if (!source.last_crawled_at) return 'Pending first sync'
    
    // Parse the last crawl date properly
    const lastCrawl = new Date(source.last_crawled_at)
    
    // Check if date is valid
    if (isNaN(lastCrawl.getTime())) return 'Unknown'
    
    // Calculate next sync as 24 hours from last crawl
    const nextSync = new Date(lastCrawl.getTime() + 24 * 60 * 60 * 1000)
    const now = new Date()
    
    // If next sync is in the past, it's due now
    if (nextSync <= now) return 'Due now'
    
    const diffMs = nextSync.getTime() - now.getTime()
    const diffHours = Math.floor(diffMs / 3600000)
    const diffMins = Math.floor((diffMs % 3600000) / 60000)
    
    // Show hours if more than 1 hour remaining
    if (diffHours >= 1) {
      return `In ~${diffHours}h`
    }
    // Show minutes if less than 1 hour
    if (diffMins > 0) {
      return `In ${diffMins}m`
    }
    return 'Due now'
  }

  return (
    <>
      <Card className="hover:shadow-xl transition-shadow">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClass}`}>
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <CardTitle className="text-lg">{source.name}</CardTitle>
                <p className="text-sm text-gray-500 capitalize">{source.source_type}</p>
              </div>
            </div>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowEditModal(true)}
                className="text-gray-400 hover:text-blue-600"
              >
                <Edit className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDeleteDialog(true)}
                className="text-gray-400 hover:text-red-600"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* URL or Config Info */}
          {source.url ? (
            <div className="flex items-center gap-2 text-sm">
              <ExternalLink className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline truncate"
              >
                {source.url}
              </a>
            </div>
          ) : source.config && (
            <div className="text-sm text-gray-600">
              {source.config.repository && (
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <span className="truncate">{source.config.repository}</span>
                </div>
              )}
              {source.config.subreddit && (
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <span className="truncate">r/{source.config.subreddit}</span>
                </div>
              )}
              {source.config.channel_id && (
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <span className="truncate">{source.config.channel_id}</span>
                </div>
              )}
            </div>
          )}

          {/* Status */}
          <div className="flex items-center justify-between pt-3 border-t border-gray-100">
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <span className="text-sm font-medium text-gray-700">{getStatusText()}</span>
            </div>
            <span className="text-xs text-gray-500">
              {formatDate(source.last_crawled_at)}
            </span>
          </div>

          {/* Sync Information */}
          <div className="bg-gray-50 rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Last Sync
              </span>
              <span className="font-medium text-gray-900">{formatDate(source.last_crawled_at)}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600 flex items-center gap-1">
                <RefreshCw className="w-3 h-3" />
                Next Sync
              </span>
              <span className="font-medium text-gray-900">{getNextSyncTime()}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCrawl}
              disabled={crawling || source.status === 'error'}
              className="w-full text-xs mt-2"
            >
              <RefreshCw className={`w-3 h-3 mr-2 ${crawling ? 'animate-spin' : ''}`} />
              {crawling ? 'Crawling...' : 'Sync Now'}
            </Button>
            {success && (
              <p className="text-xs text-green-600 text-center">{success}</p>
            )}
          </div>

          {/* Error message if status is error */}
          {source.status === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 space-y-2">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-xs font-medium text-red-800 mb-1">Error Details:</p>
                  <p className="text-xs text-red-700">
                    {source.error_message || 'This source encountered an error. Please check the credentials or configuration.'}
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowEditModal(true)}
                  className="flex-1 text-xs"
                >
                  <Edit className="w-3 h-3 mr-2" />
                  Edit Source
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleReactivate}
                  disabled={reactivating}
                  className="flex-1 text-xs"
                >
                  <RefreshCw className={`w-3 h-3 mr-2 ${reactivating ? 'animate-spin' : ''}`} />
                  {reactivating ? 'Reactivating...' : 'Retry'}
                </Button>
              </div>
              {error && (
                <p className="text-xs text-red-600">{error}</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Source Modal */}
      <EditSourceModal
        open={showEditModal}
        onOpenChange={setShowEditModal}
        source={source}
        onSourceUpdated={handleSourceUpdated}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Source</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{source.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
