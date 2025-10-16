import React, { useState, useEffect } from 'react';
import { Input } from './ui/Input';
import { Button } from './ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Loader2, Plus, AlertCircle } from 'lucide-react';
import { CredentialInput } from './CredentialInput';

interface SourceType {
  type: string;
  name: string;
  credential_schema: any;
}

interface AddSourceFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export const AddSourceForm: React.FC<AddSourceFormProps> = ({ onSuccess, onCancel }) => {
  const [sourceTypes, setSourceTypes] = useState<SourceType[]>([]);
  const [selectedType, setSelectedType] = useState<string>('');
  const [sourceName, setSourceName] = useState('');
  const [config, setConfig] = useState<Record<string, any>>({});
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchSourceTypes();
  }, []);

  const fetchSourceTypes = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/sources/types`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSourceTypes(data);
      }
    } catch (error) {
      console.error('Failed to fetch source types:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setErrors({});

    try {
      const token = localStorage.getItem('access_token');
      
      // Build request payload
      const payload: any = {
        source_type: selectedType,
        name: sourceName,
        config: config,
      };

      // Only include credentials if any are provided
      const hasCredentials = Object.values(credentials).some(val => val);
      if (hasCredentials) {
        payload.credentials = credentials;
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/sources`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        // Success!
        if (onSuccess) {
          onSuccess();
        }
        // Reset form
        setSourceName('');
        setConfig({});
        setCredentials({});
        setSelectedType('');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to add source');
      }
    } catch (error) {
      setError('An error occurred while adding the source');
      console.error('Error adding source:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderConfigFields = () => {
    if (!selectedType) return null;

    // Define config fields for each source type
    const configFields: Record<string, any[]> = {
      rss: [
        { name: 'feed_url', label: 'Feed URL', type: 'url', required: true, placeholder: 'https://example.com/feed' }
      ],
      youtube: [
        { name: 'channel_id', label: 'Channel ID or Handle', type: 'text', required: true, placeholder: '@channelhandle or UC_x5XG1OV2P6uZZ5FSM9Ttw' },
        { 
          name: 'fetch_type', 
          label: 'Fetch Type', 
          type: 'select', 
          required: true,
          options: ['uploads', 'liked', 'subscriptions', 'playlist']
        },
        { name: 'max_results', label: 'Max Results (per crawl)', type: 'number', required: false, placeholder: '10', min: 1, max: 50 }
      ],
      twitter: [
        { name: 'username', label: 'Username', type: 'text', required: true, placeholder: 'elonmusk (without @)' },
        { 
          name: 'fetch_type', 
          label: 'Fetch Type', 
          type: 'select', 
          required: true,
          options: ['timeline', 'mentions', 'likes', 'list']
        },
        { name: 'max_results', label: 'Max Results (per crawl)', type: 'number', required: false, placeholder: '10', min: 1, max: 100 }
      ],
      substack: [
        { name: 'publication_url', label: 'Publication URL', type: 'url', required: true, placeholder: 'https://example.substack.com' },
        { name: 'include_free_only', label: 'Free Posts Only', type: 'checkbox', required: false }
      ],
      medium: [
        { 
          name: 'feed_type', 
          label: 'Feed Type', 
          type: 'select', 
          required: true,
          options: ['user', 'publication', 'tag']
        },
        { name: 'identifier', label: 'Identifier', type: 'text', required: true, placeholder: 'username, publication, or tag' }
      ],
      linkedin: [
        { 
          name: 'profile_type', 
          label: 'Profile Type', 
          type: 'select', 
          required: true,
          options: ['personal', 'company']
        },
        { name: 'profile_id', label: 'Profile ID (URN)', type: 'text', required: true, placeholder: 'urn:li:person:ABC123' }
      ],
      github: [
        { name: 'repository', label: 'Repository', type: 'text', required: true, placeholder: 'owner/repo (e.g., angular/angular)' },
        { 
          name: 'fetch_type', 
          label: 'Fetch Type', 
          type: 'select', 
          required: true,
          options: ['releases', 'commits', 'issues', 'pull_requests']
        },
        { name: 'max_results', label: 'Max Results (per crawl)', type: 'number', required: false, placeholder: '10', min: 1, max: 100 }
      ],
      reddit: [
        { name: 'subreddit', label: 'Subreddit', type: 'text', required: true, placeholder: 'Angular2 (without r/)' },
        { 
          name: 'fetch_type', 
          label: 'Fetch Type', 
          type: 'select', 
          required: true,
          options: ['hot', 'new', 'top', 'rising']
        },
        { 
          name: 'time_filter', 
          label: 'Time Filter (for "top" type)', 
          type: 'select', 
          required: false,
          options: ['hour', 'day', 'week', 'month', 'year', 'all']
        },
        { name: 'max_results', label: 'Max Results (per crawl)', type: 'number', required: false, placeholder: '20', min: 1, max: 100 }
      ]
    };

    const fields = configFields[selectedType] || [];

    return (
      <div className="space-y-4">
        {fields.map((field) => (
          <div key={field.name} className="space-y-2">
            <label htmlFor={field.name} className="block text-sm font-medium text-gray-700">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            
            {field.type === 'select' ? (
              <select
                id={field.name}
                value={config[field.name] || ''}
                onChange={(e) => setConfig({ ...config, [field.name]: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required={field.required}
              >
                <option value="">Select {field.label}</option>
                {field.options.map((option: string) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            ) : field.type === 'checkbox' ? (
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={field.name}
                  checked={config[field.name] || false}
                  onChange={(e) => setConfig({ ...config, [field.name]: e.target.checked })}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor={field.name} className="text-sm text-gray-700">
                  {field.label}
                </label>
              </div>
            ) : (
              <Input
                id={field.name}
                type={field.type}
                value={config[field.name] || ''}
                onChange={(e) => setConfig({ ...config, [field.name]: e.target.value })}
                placeholder={field.placeholder}
                required={field.required}
              />
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add New Source</CardTitle>
        <p className="text-sm text-gray-500 mt-1">
          Connect a content source to include in your newsletters
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Source Type Selection */}
          <div className="space-y-2">
            <label htmlFor="source-type" className="block text-sm font-medium text-gray-700">
              Source Type <span className="text-red-500">*</span>
            </label>
            <select
              id="source-type"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">Select source type</option>
              {sourceTypes.map((type) => (
                <option key={type.type} value={type.type}>
                  {type.name}
                </option>
              ))}
            </select>
          </div>

          {/* Source Name */}
          {selectedType && (
            <>
              <div className="space-y-2">
                <label htmlFor="source-name" className="block text-sm font-medium text-gray-700">
                  Source Name <span className="text-red-500">*</span>
                </label>
                <Input
                  id="source-name"
                  type="text"
                  value={sourceName}
                  onChange={(e) => setSourceName(e.target.value)}
                  placeholder="e.g., TechCrunch, My Newsletter"
                  required
                />
              </div>

              {/* Config Fields */}
              {renderConfigFields()}

              {/* Credentials */}
              <CredentialInput
                sourceType={selectedType}
                credentials={credentials}
                onChange={setCredentials}
                errors={errors}
              />
            </>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start">
              <AlertCircle className="h-5 w-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button type="submit" disabled={loading || !selectedType || !sourceName}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Source
                </>
              )}
            </Button>
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
