# Twitter Credential Validation Update

## Overview
Updated Twitter/X source connector to support flexible authentication with conditional credential requirements. Users can now provide **either** Bearer Token (OAuth 2.0) **or** complete OAuth 1.0a credentials.

## Changes Made

### 1. Backend - Credential Schema (`backend/app/schemas/credentials.py`)
- **Added** `bearer_token` field as an authentication option
- **Changed** all credential fields from `required=True` to `required=False`
- **Updated** help text to clarify two authentication options:
  - **Option 1**: Bearer Token (OAuth 2.0) - simpler, read-only access
  - **Option 2**: OAuth 1.0a - all 4 fields (api_key, api_secret, access_token, access_token_secret)

### 2. Backend - Twitter Connector (`backend/app/services/sources/twitter_connector.py`)
- **Updated** `get_required_credentials()` to return empty list (credentials are conditionally required)
- **Added** `validate_credentials()` method with comprehensive validation logic:
  - Checks if bearer_token is provided
  - Checks if all OAuth 1.0a credentials are provided
  - Detects partial OAuth 1.0a credentials and provides helpful error messages
  - Returns clear validation errors indicating which fields are missing

### 3. Backend - Source Validator (`backend/app/utils/validators.py`)
- **Enhanced** Twitter validation in `validate_source()` method
- **Added** credential validation before source creation
- **Validates** that at least one complete authentication method is provided
- **Provides** specific error messages for missing credentials

### 4. Frontend - Source Card (`frontend/src/components/SourceCard.tsx`)
- **Added** display for Twitter `username` field with Twitter icon
- **Added** display for `fetch_type` (timeline/mentions/likes) next to username
- Shows format: `@username (fetch_type)`

### 5. Frontend - Add Source Modal (`frontend/src/components/AddSourceModal.tsx`)
- **Updated** Twitter authentication note to explain flexible credential options
- Informs users they can provide either Bearer Token OR OAuth 1.0a credentials

### 6. Frontend - Credential Input (`frontend/src/components/CredentialInput.tsx`)
- **Added** Twitter-specific guidance banner explaining authentication options
- Shows clear instructions: Option 1 (Bearer Token only) or Option 2 (All OAuth 1.0a fields)
- Dynamically fetches and renders credential fields from backend schema
- Automatically displays all 5 credential fields (bearer_token + 4 OAuth 1.0a fields)

## Authentication Options

### Option 1: Bearer Token (Recommended for Read-Only)
```json
{
  "credentials": {
    "bearer_token": "your_bearer_token_here"
  }
}
```

### Option 2: OAuth 1.0a (Full Access)
```json
{
  "credentials": {
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "access_token": "your_access_token",
    "access_token_secret": "your_access_token_secret"
  }
}
```

## Validation Logic

The validation ensures:
1. **At least one method** is provided (Bearer Token OR OAuth 1.0a)
2. **Complete credentials** - if using OAuth 1.0a, all 4 fields must be present
3. **Clear error messages** - users know exactly what's missing

### Error Messages
- No credentials: "X (Twitter) requires credentials. Provide either: (1) Bearer Token, or (2) All OAuth 1.0a credentials..."
- Partial OAuth 1.0a: "Incomplete OAuth 1.0a credentials. Missing: api_key, access_token. Either provide all OAuth 1.0a credentials or use Bearer Token instead."

## Benefits

1. **Flexibility**: Users can choose simpler Bearer Token or full OAuth 1.0a
2. **Clear Guidance**: Help text explains both options
3. **Better UX**: Specific error messages guide users to fix issues
4. **Backward Compatible**: Existing OAuth 1.0a implementations continue to work
5. **Validation at Multiple Levels**: Checked in connector, validator, and during source creation

## User Experience Flow

### When Adding a Twitter Source:

1. **User selects Twitter** from source types
2. **Fills in basic config**: Name, Username, Fetch Type
3. **Sees credential guidance banner** with two clear options:
   - Option 1: Provide only Bearer Token (simpler)
   - Option 2: Provide all 4 OAuth 1.0a fields (full access)
4. **Credential fields displayed**:
   - Bearer Token (OAuth 2.0) - Optional
   - API Key (Consumer Key) - Optional
   - API Secret (Consumer Secret) - Optional
   - Access Token - Optional
   - Access Token Secret - Optional
5. **Validation on submit**:
   - Backend checks if at least one complete method is provided
   - Clear error messages if validation fails
6. **Source card displays**: `@username (fetch_type)`

### Error Handling Examples:

**No credentials provided:**
```
"X (Twitter) requires credentials. Provide either: (1) Bearer Token, or (2) All OAuth 1.0a credentials..."
```

**Partial OAuth 1.0a credentials:**
```
"Incomplete OAuth 1.0a credentials. Missing: access_token, access_token_secret. Either provide all OAuth 1.0a credentials or use Bearer Token instead."
```

## Testing Recommendations

1. Test creating source with only Bearer Token
2. Test creating source with all OAuth 1.0a credentials
3. Test error handling with partial OAuth 1.0a credentials
4. Test error handling with no credentials
5. Verify frontend displays username and fetch_type correctly
6. Test editing existing Twitter sources with credential updates
7. Verify guidance banner displays correctly in Add Source modal
8. Test that credential fields are marked as optional (no red asterisk for individual fields)
