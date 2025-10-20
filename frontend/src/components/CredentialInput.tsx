import React, { useState, useEffect } from 'react';
import { Input } from './ui/Input';
import { Button } from './ui/Button';
import { Eye, EyeOff, Info, ExternalLink } from 'lucide-react';

interface CredentialField {
  name: string;
  label: string;
  type: 'text' | 'password' | 'api_key' | 'oauth_token';
  required: boolean;
  placeholder?: string;
  help_text?: string;
}

interface CredentialSchema {
  source_type: string;
  fields: CredentialField[];
  supports_global: boolean;
  oauth_url?: string;
}

interface CredentialInputProps {
  sourceType: string;
  credentials: Record<string, string>;
  onChange: (credentials: Record<string, string>) => void;
  errors?: Record<string, string>;
}

export const CredentialInput: React.FC<CredentialInputProps> = ({
  sourceType,
  credentials,
  onChange,
  errors = {},
}) => {
  const [schema, setSchema] = useState<CredentialSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [showPassword, setShowPassword] = useState<Record<string, boolean>>({});
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    fetchCredentialSchema();
  }, [sourceType]);

  const fetchCredentialSchema = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${API_URL}/api/sources/types/${sourceType}/credentials`
      );
      
      if (response.ok) {
        const data = await response.json();
        setSchema(data);
        
        // Auto-open if credentials are required
        if (data.fields.length > 0 && !data.supports_global) {
          setIsOpen(true);
        }
      } else {
        console.error(`Failed to fetch credential schema: ${response.status} ${response.statusText}`);
        const errorText = await response.text();
        console.error('Error details:', errorText);
      }
    } catch (error) {
      console.error('Failed to fetch credential schema:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (fieldName: string, value: string) => {
    onChange({
      ...credentials,
      [fieldName]: value,
    });
  };

  const togglePasswordVisibility = (fieldName: string) => {
    setShowPassword({
      ...showPassword,
      [fieldName]: !showPassword[fieldName],
    });
  };

  const handleOAuthClick = () => {
    if (schema?.oauth_url) {
      // Open OAuth flow in popup
      const width = 600;
      const height = 700;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;
      
      window.open(
        schema.oauth_url,
        'OAuth',
        `width=${width},height=${height},left=${left},top=${top}`
      );
    }
  };

  if (loading) {
    return <div className="text-sm text-gray-500">Loading credential fields...</div>;
  }

  if (!schema || schema.fields.length === 0) {
    return null; // No credentials needed
  }

  const hasRequiredFields = schema.fields.some(field => field.required);

  return (
    <div className="space-y-4">
      {schema.supports_global && !hasRequiredFields ? (
        // Optional credentials - show in collapsible
        <div className="border border-gray-200 rounded-lg">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50"
          >
            <span className="font-medium text-sm">Advanced: Custom API Credentials</span>
            <Info className="h-4 w-4 text-gray-500" />
          </button>
          {isOpen && (
            <div className="p-4 pt-0 space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  <Info className="inline h-4 w-4 mr-1" />
                  Optional: Leave empty to use default credentials. Provide your own to avoid rate limit sharing.
                </p>
              </div>
              {renderCredentialFields()}
            </div>
          )}
        </div>
      ) : (
        // Required credentials - show directly
        <div className="space-y-4">
          {sourceType === 'twitter' && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-sm text-amber-900 font-medium mb-2">
                <Info className="inline h-4 w-4 mr-1" />
                Twitter Authentication Options
              </p>
              <p className="text-xs text-amber-800 mb-2">
                Choose one of the following authentication methods:
              </p>
              <ul className="text-xs text-amber-800 space-y-1 ml-4 list-disc">
                <li><strong>Option 1 (Simpler):</strong> Provide only the Bearer Token field</li>
                <li><strong>Option 2 (Full Access):</strong> Provide all 4 OAuth 1.0a fields (API Key, API Secret, Access Token, Access Token Secret)</li>
              </ul>
            </div>
          )}
          {schema.oauth_url && sourceType !== 'twitter' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <p className="text-sm text-blue-800">
                  <Info className="inline h-4 w-4 mr-1" />
                  This source requires OAuth authentication
                </p>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleOAuthClick}
                >
                  Connect via OAuth
                  <ExternalLink className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
          {renderCredentialFields()}
        </div>
      )}
    </div>
  );

  function renderCredentialFields() {
    return schema!.fields.map((field) => {
      const isPasswordType = field.type === 'password' || field.type === 'api_key' || field.type === 'oauth_token';
      const shouldShowPassword = showPassword[field.name];
      const inputType = isPasswordType && !shouldShowPassword ? 'password' : 'text';

      return (
        <div key={field.name} className="space-y-2">
          <label htmlFor={field.name} className="block text-sm font-medium text-gray-700">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          
          <div className="relative">
            <Input
              id={field.name}
              type={inputType}
              value={credentials[field.name] || ''}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              placeholder={field.placeholder}
              className={errors[field.name] ? 'border-red-500' : ''}
            />
            
            {isPasswordType && (
              <button
                type="button"
                onClick={() => togglePasswordVisibility(field.name)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {shouldShowPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            )}
          </div>

          {field.help_text && (
            <p className="text-sm text-gray-500">{field.help_text}</p>
          )}
          
          {errors[field.name] && (
            <p className="text-sm text-red-500">{errors[field.name]}</p>
          )}
        </div>
      );
    });
  }
};
