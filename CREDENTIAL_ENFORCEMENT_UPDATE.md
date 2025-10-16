# Credential Enforcement & Source Edit Feature Update

## Summary
Removed all default/fallback API keys from the codebase and enforced user-provided credentials for all sources. Added edit functionality to source cards with improved error messaging.

## Changes Made

### 1. Backend - Removed Fallback Keys

#### Modified Connectors
All source connectors now require user-provided credentials with no fallback to environment variables:

**Twitter Connector** (`backend/app/services/sources/twitter_connector.py`)
- Removed fallback to `settings.TWITTER_API_KEY`, `TWITTER_API_SECRET`, etc.
- Updated `get_required_credentials()` to return required fields: `["api_key", "api_secret", "access_token", "access_token_secret"]`
- Changed error message to clearly indicate credentials must be provided

**YouTube Connector** (`backend/app/services/sources/youtube_connector.py`)
- Removed fallback to `settings.YOUTUBE_API_KEY`
- Updated `get_required_credentials()` to return `["api_key"]`
- Changed error message to indicate API key is required

**GitHub Connector** (`backend/app/services/sources/github_connector.py`)
- Removed fallback to `settings.GITHUB_TOKEN`
- Removed unauthenticated client initialization
- Updated `get_required_credentials()` to return `["github_token"]`
- Changed error message to indicate token is required

**Reddit Connector** (`backend/app/services/sources/reddit_connector.py`)
- Removed fallback to `settings.REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`
- Updated `get_required_credentials()` to return `["reddit_client_id", "reddit_client_secret"]`
- Changed error message to indicate credentials are required

#### Updated Credential Schemas
Modified `backend/app/schemas/credentials.py`:
- Set all credential fields to `required=True` for Twitter, YouTube, GitHub, and Reddit
- Changed `supports_global=False` for all sources (no global credentials)
- Updated help text to indicate credentials are required and provide links to credential sources

### 2. Frontend - Edit Functionality

#### New Component: EditSourceModal
Created `frontend/src/components/EditSourceModal.tsx`:
- Modal dialog for editing existing sources
- Supports updating name, URL, config, and credentials
- Pre-fills form with existing source data
- Allows optional credential updates (leave empty to keep existing)
- Includes all source-specific config fields (YouTube, GitHub, Reddit, Twitter)

#### Updated SourceCard Component
Modified `frontend/src/components/SourceCard.tsx`:
- Added Edit button next to Delete button in card header
- Improved error display with:
  - Alert icon and "Error Details:" label
  - Better formatting of error messages
  - Two action buttons: "Edit Source" and "Retry"
- Added `onUpdate` callback prop to refresh sources after edit
- Integrated EditSourceModal component

#### Updated Sources Service
Modified `frontend/src/services/sources.service.ts`:
- Added `UpdateSourceData` interface
- Added `updateSource(id, data)` method to call PUT `/api/sources/{id}`

#### Updated Sources Page
Modified `frontend/src/pages/Sources.tsx`:
- Passed `onUpdate={loadSources}` to SourceCard components
- Sources list refreshes after any edit

### 3. Error Messaging Improvements

**Source Cards Now Display:**
- Detailed error messages from the backend
- Clear visual indicators (alert icon, red border)
- Actionable buttons (Edit Source, Retry)
- Helpful context about what went wrong

**Backend Error Messages:**
- Connectors now provide specific error messages when credentials are missing
- Validation errors clearly indicate which credentials are required
- Error messages include links to credential sources (Twitter Developer Portal, GitHub Settings, etc.)

## Impact

### For Users
1. **Must provide credentials** when adding sources (no more default keys)
2. **Can edit sources** to update credentials or configuration
3. **Better error messages** help diagnose and fix issues quickly
4. **More secure** - each user uses their own API keys

### For Developers
1. **No more .env fallbacks** - cleaner separation of concerns
2. **Consistent credential handling** across all sources
3. **Better error tracking** - know exactly which source failed and why

## Testing Recommendations

1. **Add New Sources:**
   - Try adding Twitter, YouTube, GitHub, Reddit sources without credentials (should fail with clear error)
   - Add sources with valid credentials (should succeed)
   - Verify error messages are helpful

2. **Edit Existing Sources:**
   - Edit source name and config (should update successfully)
   - Edit credentials (should update and re-validate)
   - Cancel edit (should not change source)

3. **Error Handling:**
   - Create source with invalid credentials
   - Verify error message appears in source card
   - Click "Edit Source" button (should open edit modal)
   - Update credentials and save (should clear error)

4. **Crawling:**
   - Verify sources only use user-provided credentials during crawls
   - Check that sources with missing credentials fail gracefully
   - Confirm error messages are stored in `error_message` field

## Files Modified

### Backend
- `backend/app/services/sources/twitter_connector.py`
- `backend/app/services/sources/youtube_connector.py`
- `backend/app/services/sources/github_connector.py`
- `backend/app/services/sources/reddit_connector.py`
- `backend/app/schemas/credentials.py`

### Frontend
- `frontend/src/components/SourceCard.tsx`
- `frontend/src/components/EditSourceModal.tsx` (new file)
- `frontend/src/services/sources.service.ts`
- `frontend/src/pages/Sources.tsx`

## Migration Notes

**For Existing Installations:**
1. Existing sources using global credentials will continue to work until next crawl
2. Users should edit sources to add their own credentials
3. Consider adding a migration script to notify users about credential requirements
4. Update documentation to reflect new credential requirements

## Security Improvements

1. **No shared credentials** - each user has their own API keys
2. **Better audit trail** - know which user's credentials were used
3. **Reduced risk** - compromised credentials only affect one user
4. **Compliance** - better aligns with API provider terms of service

## Future Enhancements

1. **Credential validation** - validate credentials before saving
2. **Credential encryption** - encrypt credentials at rest
3. **OAuth flows** - implement OAuth for Twitter, YouTube, LinkedIn
4. **Credential rotation** - notify users when credentials need renewal
5. **Bulk edit** - edit multiple sources at once
