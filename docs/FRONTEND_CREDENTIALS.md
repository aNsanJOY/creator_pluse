# Frontend Credential Management

This guide explains how to use the credential input system in the frontend.

## Overview

The frontend now supports dynamic credential input for different source types. The system automatically:
- Fetches credential requirements from the backend
- Builds appropriate input forms
- Handles optional vs required credentials
- Shows/hides password fields
- Supports OAuth flows

## Components

### 1. CredentialInput Component

**Location**: `frontend/src/components/CredentialInput.tsx`

**Purpose**: Renders credential input fields based on source type

**Usage**:
```tsx
import { CredentialInput } from '@/components/CredentialInput';

function MyForm() {
  const [credentials, setCredentials] = useState({});

  return (
    <CredentialInput
      sourceType="youtube"
      credentials={credentials}
      onChange={setCredentials}
      errors={{}}
    />
  );
}
```

**Features**:
- Auto-fetches credential schema from API
- Shows optional credentials in collapsible section
- Shows required credentials directly
- Password visibility toggle
- OAuth button for OAuth-based sources
- Help text and validation

### 2. AddSourceForm Component

**Location**: `frontend/src/components/AddSourceForm.tsx`

**Purpose**: Complete form for adding a new source

**Usage**:
```tsx
import { AddSourceForm } from '@/components/AddSourceForm';

function SourcesPage() {
  return (
    <AddSourceForm
      onSuccess={() => {
        // Refresh sources list
        fetchSources();
      }}
      onCancel={() => {
        // Close modal
        setShowForm(false);
      }}
    />
  );
}
```

**Features**:
- Source type selection
- Dynamic config fields based on type
- Integrated credential input
- Form validation
- Error handling
- Loading states

## API Endpoints Used

### Get All Source Types
```
GET /api/sources/types

Response:
[
  {
    "type": "youtube",
    "name": "YouTube",
    "credential_schema": {
      "source_type": "youtube",
      "fields": [...],
      "supports_global": true,
      "oauth_url": null
    }
  },
  ...
]
```

### Get Credential Schema
```
GET /api/sources/types/{source_type}/credentials

Response:
{
  "source_type": "youtube",
  "fields": [
    {
      "name": "api_key",
      "label": "YouTube API Key",
      "type": "api_key",
      "required": false,
      "placeholder": "AIzaSy...",
      "help_text": "Optional: Leave empty to use default"
    }
  ],
  "supports_global": true,
  "oauth_url": null
}
```

## Credential Field Types

### 1. Text
```tsx
{
  name: "username",
  label: "Username",
  type: "text",
  required: true,
  placeholder: "Enter username"
}
```
Renders as: Regular text input

### 2. Password
```tsx
{
  name: "api_secret",
  label: "API Secret",
  type: "password",
  required: true,
  placeholder: "Enter secret"
}
```
Renders as: Password input with show/hide toggle

### 3. API Key
```tsx
{
  name: "api_key",
  label: "API Key",
  type: "api_key",
  required: false,
  placeholder: "AIzaSy..."
}
```
Renders as: Password input with show/hide toggle (same as password)

### 4. OAuth Token
```tsx
{
  name: "access_token",
  label: "Access Token",
  type: "oauth_token",
  required: true,
  placeholder: "OAuth token"
}
```
Renders as: Password input with show/hide toggle

## Source-Specific Examples

### RSS (No Credentials)
```tsx
// No credential input shown
<AddSourceForm />
// User only sees config fields (feed_url)
```

### YouTube (Optional Credentials)
```tsx
// Credentials shown in collapsible "Advanced" section
<AddSourceForm />
// User can optionally provide api_key
// If not provided, uses global YOUTUBE_API_KEY from .env
```

### LinkedIn (Required Credentials)
```tsx
// Credentials shown directly with OAuth button
<AddSourceForm />
// User must provide access_token
// OAuth button opens LinkedIn auth flow
```

## Styling

The components use shadcn/ui components:
- `Input` - Text inputs
- `Label` - Field labels
- `Button` - Buttons
- `Select` - Dropdowns
- `Alert` - Info/error messages
- `Collapsible` - Expandable sections
- `Card` - Container

## Customization

### Adding New Source Type

1. **Backend**: Add to `CREDENTIAL_SCHEMAS` in `backend/app/schemas/credentials.py`
```python
"newsource": SourceCredentialSchema(
    source_type="newsource",
    fields=[
        CredentialField(
            name="api_key",
            label="API Key",
            type=CredentialFieldType.API_KEY,
            required=True,
            placeholder="Enter your API key",
            help_text="Get this from the service dashboard"
        )
    ],
    supports_global=False
)
```

2. **Frontend**: Add config fields to `AddSourceForm.tsx`
```tsx
const configFields: Record<string, any[]> = {
  // ... existing
  newsource: [
    { 
      name: 'endpoint', 
      label: 'API Endpoint', 
      type: 'url', 
      required: true, 
      placeholder: 'https://api.example.com' 
    }
  ]
};
```

3. **Done!** The credential input will automatically render based on the schema.

## OAuth Flow

For OAuth-based sources (Twitter, LinkedIn):

1. **User clicks "Connect via OAuth"**
2. **Popup opens** with OAuth URL
3. **User authenticates** on external service
4. **Callback** returns tokens
5. **Tokens auto-fill** in form

### Implementing OAuth Callback

```tsx
// Listen for OAuth callback
useEffect(() => {
  const handleOAuthCallback = (event: MessageEvent) => {
    if (event.data.type === 'oauth_success') {
      setCredentials({
        access_token: event.data.access_token,
        refresh_token: event.data.refresh_token
      });
    }
  };

  window.addEventListener('message', handleOAuthCallback);
  return () => window.removeEventListener('message', handleOAuthCallback);
}, []);
```

## Validation

### Client-Side
```tsx
const validateCredentials = () => {
  const newErrors: Record<string, string> = {};
  
  schema.fields.forEach(field => {
    if (field.required && !credentials[field.name]) {
      newErrors[field.name] = `${field.label} is required`;
    }
  });
  
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};
```

### Server-Side
The backend validates credentials when creating the source and returns errors if invalid.

## Security

### Password Fields
- All sensitive fields (password, api_key, oauth_token) are masked by default
- Show/hide toggle available for user convenience
- Values never logged or exposed in URLs

### HTTPS Only
- Credentials only sent over HTTPS in production
- Use environment variables for API URLs

### Token Storage
- Access tokens stored in localStorage (encrypted in production)
- Refresh tokens handled server-side
- Credentials encrypted in database

## Testing

### Test Optional Credentials
```tsx
// Test YouTube with no credentials (uses global)
<AddSourceForm />
// Select YouTube
// Fill config only
// Submit
// Should succeed using YOUTUBE_API_KEY from .env
```

### Test Required Credentials
```tsx
// Test LinkedIn with credentials
<AddSourceForm />
// Select LinkedIn
// Fill config
// Fill access_token
// Submit
// Should succeed
```

### Test Validation
```tsx
// Test required field validation
<AddSourceForm />
// Select LinkedIn
// Leave access_token empty
// Submit
// Should show error
```

## Troubleshooting

### Credentials Not Showing
**Problem**: Credential fields don't appear

**Solution**:
1. Check API endpoint returns schema
2. Verify `sourceType` prop is correct
3. Check browser console for errors

### OAuth Popup Blocked
**Problem**: OAuth popup doesn't open

**Solution**:
1. Allow popups for your domain
2. Check OAuth URL is correct
3. Verify CORS settings

### Form Submission Fails
**Problem**: Source creation fails

**Solution**:
1. Check required fields are filled
2. Verify credentials format
3. Check backend logs for validation errors
4. Ensure API token is valid

## Example: Complete Flow

```tsx
import { useState } from 'react';
import { AddSourceForm } from '@/components/AddSourceForm';
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

function SourcesPage() {
  const [open, setOpen] = useState(false);
  const [sources, setSources] = useState([]);

  const fetchSources = async () => {
    const token = localStorage.getItem('access_token');
    const response = await fetch('/api/sources', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setSources(data);
  };

  return (
    <div>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Source
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-2xl">
          <AddSourceForm
            onSuccess={() => {
              setOpen(false);
              fetchSources();
            }}
            onCancel={() => setOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Sources list */}
      <div className="mt-6">
        {sources.map(source => (
          <div key={source.id}>{source.name}</div>
        ))}
      </div>
    </div>
  );
}
```

## Summary

The credential management system provides:
- ✅ Dynamic forms based on source type
- ✅ Optional vs required credential handling
- ✅ Password visibility toggles
- ✅ OAuth flow support
- ✅ Validation and error handling
- ✅ Help text and placeholders
- ✅ Secure credential handling

Users can now easily add sources with or without credentials directly from the UI!
