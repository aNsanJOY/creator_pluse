# YouTube Integration Setup Guide

This guide explains how to set up YouTube OAuth integration for CreatorPulse.

## Prerequisites

- Google Cloud Platform account
- YouTube channel (the user connecting must have a YouTube channel)

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a Project" → "New Project"
3. Enter project name (e.g., "CreatorPulse")
4. Click "Create"

## Step 2: Enable YouTube Data API v3

1. In your Google Cloud project, go to **APIs & Services** → **Library**
2. Search for "YouTube Data API v3"
3. Click on it and press **Enable**

## Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External** (for testing) or **Internal** (for organization)
   - App name: **CreatorPulse**
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add the following scopes:
     - `https://www.googleapis.com/auth/youtube.readonly`
     - `https://www.googleapis.com/auth/youtube.force-ssl`
   - Test users: Add your email (for External apps in testing mode)
   - Save and continue

4. Back to **Create OAuth client ID**:
   - Application type: **Web application**
   - Name: **CreatorPulse Backend**
   - Authorized redirect URIs:
     - `http://localhost:8000/api/youtube/oauth/callback` (development)
     - `https://your-production-domain.com/api/youtube/oauth/callback` (production)
   - Click **Create**

5. Copy the **Client ID** and **Client Secret**

## Step 4: Create API Key (Optional but Recommended)

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **API key**
3. Copy the API key
4. Click **Restrict Key** (recommended):
   - API restrictions: Select "Restrict key"
   - Select APIs: Choose "YouTube Data API v3"
   - Save

## Step 5: Configure Environment Variables

Add the following to your `.env` file:

```env
# YouTube API Configuration
YOUTUBE_CLIENT_ID=your_client_id_here
YOUTUBE_CLIENT_SECRET=your_client_secret_here
YOUTUBE_API_KEY=your_api_key_here
```

## Step 6: Install Dependencies

Make sure you have the required Python packages:

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

## API Endpoints

### Initialize OAuth Flow

**POST** `/api/youtube/oauth/init`

**Headers:**
```
Authorization: Bearer <user_token>
```

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "random_state_string"
}
```

**Usage:**
1. Call this endpoint to get the authorization URL
2. Redirect user to the `authorization_url`
3. User approves the app on Google's consent screen
4. Google redirects back to your callback URL with `code` and `state`

### Complete OAuth Flow

**POST** `/api/youtube/oauth/callback`

**Headers:**
```
Authorization: Bearer <user_token>
```

**Body:**
```json
{
  "code": "authorization_code_from_google",
  "state": "state_from_init_response"
}
```

**Response:**
```json
{
  "source_id": "uuid",
  "channel_title": "Your Channel Name",
  "channel_id": "UC...",
  "status": "active"
}
```

### Get Channel Statistics

**GET** `/api/youtube/{source_id}/stats`

**Headers:**
```
Authorization: Bearer <user_token>
```

**Response:**
```json
{
  "channel_id": "UC...",
  "channel_title": "Your Channel Name",
  "subscriber_count": 1000,
  "video_count": 50,
  "view_count": 100000
}
```

### Disconnect YouTube Source

**DELETE** `/api/youtube/{source_id}`

**Headers:**
```
Authorization: Bearer <user_token>
```

**Response:**
```json
{
  "message": "YouTube source disconnected successfully"
}
```

## YouTube Connector Configuration

The YouTube connector supports the following configuration options:

```python
{
  "channel_id": "UC...",           # Required: YouTube channel ID
  "fetch_type": "uploads",         # Required: 'uploads', 'search', or 'playlist'
  "max_results": 50,               # Optional: Max videos per fetch (default: 50)
  "playlist_id": "PL..."           # Required only if fetch_type='playlist'
}
```

### Fetch Types

- **uploads**: Fetches videos from the channel's uploads playlist (all uploaded videos)
- **search**: Searches for videos in the channel (supports date filtering)
- **playlist**: Fetches videos from a specific playlist

## Rate Limits and Quotas

YouTube Data API v3 has quota limits:

- **Default quota**: 10,000 units per day
- **Read operations**: 1 unit per request
- **Search operations**: 100 units per request

### Cost per Operation

- List videos: ~3-5 units
- Search videos: ~100 units
- Get channel info: ~1 unit

**Recommendation**: Use `fetch_type: "uploads"` for regular crawling as it's more quota-efficient than search.

## Troubleshooting

### Error: "No YouTube channel found for this account"

**Solution**: Make sure the Google account has an associated YouTube channel. Create a channel if needed.

### Error: "Access blocked: This app's request is invalid"

**Solution**: 
1. Verify redirect URI in Google Cloud Console matches exactly
2. Check that YouTube Data API v3 is enabled
3. Ensure OAuth consent screen is configured

### Error: "The request is missing a required parameter: access_type"

**Solution**: This is handled automatically by the backend. If you see this, check the OAuth flow implementation.

### Error: "Quota exceeded"

**Solution**: 
1. Wait for quota reset (daily at midnight Pacific Time)
2. Request quota increase in Google Cloud Console
3. Optimize fetch frequency in scheduler

## Security Best Practices

1. **Never commit credentials**: Keep `.env` file out of version control
2. **Use HTTPS in production**: Ensure redirect URIs use HTTPS
3. **Rotate secrets regularly**: Update client secrets periodically
4. **Restrict API keys**: Apply API restrictions in Google Cloud Console
5. **Monitor quota usage**: Set up alerts in Google Cloud Console

## Testing

To test the YouTube integration:

1. Start the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Use the API documentation at `http://localhost:8000/docs`

3. Test the OAuth flow:
   - Call `/api/youtube/oauth/init`
   - Visit the authorization URL
   - Approve the app
   - Complete the callback with the code

4. Verify the source is created in the database

## Frontend Integration

Example frontend flow:

```javascript
// 1. Initialize OAuth
const response = await fetch('/api/youtube/oauth/init', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`
  }
});
const { authorization_url, state } = await response.json();

// 2. Redirect user to Google
window.location.href = authorization_url;

// 3. Handle callback (in callback page)
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
const state = urlParams.get('state');

// 4. Complete OAuth
const callbackResponse = await fetch('/api/youtube/oauth/callback', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ code, state })
});
const { source_id, channel_title } = await callbackResponse.json();
```

## Additional Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [API Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
