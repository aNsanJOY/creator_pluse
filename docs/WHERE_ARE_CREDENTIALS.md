# Where Are Credentials in the UI?

## Updated Component: AddSourceModal.tsx

The credential input has been **integrated into your existing `AddSourceModal.tsx`** component.

## Visual Flow

### Step 1: Select Source Type
```
┌─────────────────────────────────────┐
│ Add Content Source                  │
├─────────────────────────────────────┤
│ Choose the type of content source   │
│                                     │
│ ┌──────────┐  ┌──────────┐         │
│ │ Twitter  │  │ YouTube  │         │
│ └──────────┘  └──────────┘         │
│                                     │
│ ┌──────────┐  ┌──────────┐         │
│ │ RSS Feed │  │ Substack │         │
│ └──────────┘  └──────────┘         │
│                                     │
│              [Cancel]               │
└─────────────────────────────────────┘
```

### Step 2: Configure Source (WITH CREDENTIALS!)

**For YouTube (optional credentials):**
```
┌─────────────────────────────────────┐
│ Configure YouTube Source            │
├─────────────────────────────────────┤
│ Source Name:                        │
│ [My Tech Channel_____________]      │
│                                     │
│ URL:                                │
│ [https://youtube.com/@tech___]      │
│                                     │
│ ┌─────────────────────────────────┐│
│ │ ▶ Advanced: Custom API Credentials││  ← NEW!
│ └─────────────────────────────────┘│
│                                     │
│ ℹ️ Note: This source will be crawled│
│    daily...                         │
│                                     │
│ [Back]              [Add Source]    │
└─────────────────────────────────────┘
```

**When expanded (user clicks the collapsible):**
```
┌─────────────────────────────────────┐
│ Configure YouTube Source            │
├─────────────────────────────────────┤
│ Source Name:                        │
│ [My Tech Channel_____________]      │
│                                     │
│ URL:                                │
│ [https://youtube.com/@tech___]      │
│                                     │
│ ┌─────────────────────────────────┐│
│ │ ▼ Advanced: Custom API Credentials││  ← Expanded
│ ├─────────────────────────────────┤│
│ │ ℹ️ Optional: Leave empty to use  ││
│ │    default credentials           ││
│ │                                  ││
│ │ YouTube API Key                  ││
│ │ [AIzaSy...____________] [👁️]     ││  ← Credential field
│ │ Optional: Leave empty to use     ││
│ │ default API key                  ││
│ └─────────────────────────────────┘│
│                                     │
│ ℹ️ Note: This source will be crawled│
│                                     │
│ [Back]              [Add Source]    │
└─────────────────────────────────────┘
```

**For LinkedIn (required credentials):**
```
┌─────────────────────────────────────┐
│ Configure LinkedIn Source           │
├─────────────────────────────────────┤
│ Source Name:                        │
│ [My LinkedIn Feed____________]      │
│                                     │
│ URL:                                │
│ [https://linkedin.com/in/user]      │
│                                     │
│ ℹ️ This source requires OAuth       │
│    [Connect via OAuth →]            │  ← OAuth button
│                                     │
│ LinkedIn Access Token *             │  ← Required field
│ [oauth_token_______________] [👁️]   │    (shown directly)
│ Required: Get this from LinkedIn    │
│ OAuth flow                          │
│                                     │
│ Refresh Token                       │
│ [refresh_token_____________] [👁️]   │
│ Optional: For automatic token       │
│ refresh                             │
│                                     │
│ [Back]              [Add Source]    │
└─────────────────────────────────────┘
```

## Code Location

### File: `frontend/src/components/AddSourceModal.tsx`

**Line 21**: Import CredentialInput component
```tsx
import { CredentialInput } from './CredentialInput'
```

**Line 94**: State for credentials
```tsx
const [credentials, setCredentials] = useState<Record<string, string>>({})
```

**Lines 237-242**: Credential input rendered in form
```tsx
{/* Credential Input Component */}
<CredentialInput
  sourceType={selectedType.type}
  credentials={credentials}
  onChange={setCredentials}
/>
```

**Lines 148-152**: Credentials sent to API
```tsx
// Only include credentials if any are provided
const hasCredentials = Object.values(credentials).some(val => val)
if (hasCredentials) {
  data.credentials = credentials
}
```

## What Happens When User Adds Source

### Without Credentials (Default)
```tsx
// User leaves credentials empty
POST /api/sources
{
  "source_type": "youtube",
  "name": "Tech Channel",
  "url": "https://youtube.com/@tech"
  // No credentials field
}

// Backend uses YOUTUBE_API_KEY from .env ✓
```

### With Custom Credentials
```tsx
// User fills in API key
POST /api/sources
{
  "source_type": "youtube",
  "name": "Tech Channel",
  "url": "https://youtube.com/@tech",
  "credentials": {
    "api_key": "AIzaSyCustomKey123"
  }
}

// Backend uses user's custom key ✓
```

## Testing the UI

1. **Start the frontend**:
```bash
cd frontend
npm run dev
```

2. **Navigate to Sources page**

3. **Click "Add Source" button**

4. **Select "YouTube"**

5. **Fill in basic details**:
   - Source Name: "Test Channel"
   - URL: "https://youtube.com/@test"

6. **Look for the collapsible section**:
   - Should see: "▶ Advanced: Custom API Credentials"

7. **Click to expand**:
   - Should see: YouTube API Key field
   - Should see: Help text explaining it's optional

8. **Leave empty and submit**:
   - Should create source successfully
   - Backend uses global YOUTUBE_API_KEY from .env

9. **Or fill in custom key**:
   - Enter your own API key
   - Submit
   - Backend uses your custom key

## Credential Behavior by Source Type

| Source | Credentials UI | Behavior |
|--------|---------------|----------|
| **RSS** | Hidden | No credentials needed |
| **Substack** | Hidden | No credentials needed |
| **Medium** | Hidden | No credentials needed |
| **YouTube** | Collapsible (optional) | Uses global key if empty, custom if provided |
| **Twitter** | Collapsible (optional) | Uses global keys if empty, custom if provided |
| **LinkedIn** | Direct (required) | Must provide OAuth token |

## Components Involved

1. **AddSourceModal.tsx** (Updated)
   - Main modal component
   - Handles source type selection
   - Integrates CredentialInput

2. **CredentialInput.tsx** (New)
   - Fetches credential schema from API
   - Renders appropriate input fields
   - Handles show/hide for passwords
   - Shows OAuth button if applicable

3. **Backend API**
   - `GET /api/sources/types/{type}/credentials`
   - Returns field definitions for the source type

## Summary

✅ **Credentials are in `AddSourceModal.tsx`**  
✅ **They appear in the "Configure" step**  
✅ **Optional credentials are in a collapsible section**  
✅ **Required credentials are shown directly**  
✅ **Password fields have show/hide toggle**  
✅ **OAuth sources have "Connect via OAuth" button**  

The credential input is **fully integrated** into your existing modal workflow!
