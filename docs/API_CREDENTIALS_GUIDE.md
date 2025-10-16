# API Credentials Guide

This guide explains how API credentials work in CreatorPulse for different source types.

## Overview

CreatorPulse supports two credential models:

1. **Global Credentials** (Application-level) - Set in `.env`, shared by all users
2. **User Credentials** (User-level) - Stored per source, user-specific

## Credential Priority

The system follows this priority order:

```
User-provided credentials → Global credentials from .env → Error
```

## Source Types & Credentials

### 1. RSS Feeds
**Credentials Required:** None

RSS feeds are public and don't require authentication.

```bash
POST /api/sources
{
  "source_type": "rss",
  "name": "TechCrunch",
  "config": {
    "feed_url": "https://techcrunch.com/feed/"
  }
  // No credentials needed
}
```

### 2. YouTube

**Global Credentials (Recommended for MVP):**
```env
# .env file
YOUTUBE_API_KEY=your_youtube_api_key_here
```

**User Credentials (Optional):**
```bash
POST /api/sources
{
  "source_type": "youtube",
  "name": "Tech Channel",
  "config": {
    "channel_id": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
    "fetch_type": "uploads"
  },
  "credentials": {
    "api_key": "user_specific_youtube_key"  // Optional
  }
}
```

**How it works:**
- If user provides `api_key` in credentials → uses that
- If not → falls back to `YOUTUBE_API_KEY` from `.env`
- If neither → validation fails

### 3. Twitter/X

**Global Credentials (Recommended for MVP):**
```env
# .env file
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
```

**User Credentials (Optional):**
```bash
POST /api/sources
{
  "source_type": "twitter",
  "name": "Tech News",
  "config": {
    "username": "elonmusk",
    "fetch_type": "timeline"
  },
  "credentials": {
    "api_key": "user_api_key",           // Optional
    "api_secret": "user_api_secret",     // Optional
    "access_token": "user_token",        // Optional
    "access_token_secret": "user_secret" // Optional
  }
}
```

**How it works:**
- Tries user credentials first
- Falls back to global credentials from `.env`
- If neither → validation fails

### 4. Substack

**Credentials Required:** None

Substack uses public RSS feeds.

```bash
POST /api/sources
{
  "source_type": "substack",
  "name": "My Newsletter",
  "config": {
    "publication_url": "https://example.substack.com"
  }
  // No credentials needed
}
```

### 5. Medium

**Credentials Required:** None

Medium uses public RSS feeds.

```bash
POST /api/sources
{
  "source_type": "medium",
  "name": "AI Articles",
  "config": {
    "feed_type": "tag",
    "identifier": "artificial-intelligence"
  }
  // No credentials needed
}
```

### 6. LinkedIn

**User Credentials Required:**

LinkedIn requires OAuth tokens per user.

```bash
POST /api/sources
{
  "source_type": "linkedin",
  "name": "My LinkedIn",
  "config": {
    "profile_type": "personal",
    "profile_id": "urn:li:person:ABC123"
  },
  "credentials": {
    "access_token": "linkedin_oauth_token"  // Required
  }
}
```

**Note:** LinkedIn doesn't support global credentials due to OAuth requirements.

## Setting Up Global Credentials

### 1. Create/Update `.env` File

```env
# backend/.env

# YouTube API (Get from Google Cloud Console)
YOUTUBE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Twitter API (Get from Twitter Developer Portal)
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_secret_here
```

### 2. Restart Backend

```bash
cd backend
python app/main.py
```

### 3. Test Without User Credentials

```bash
# Add YouTube source without credentials
POST /api/sources
{
  "source_type": "youtube",
  "name": "Test Channel",
  "config": {
    "channel_id": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
    "fetch_type": "uploads"
  }
  // No credentials field - will use global YOUTUBE_API_KEY
}
```

## Getting API Keys

### YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "YouTube Data API v3"
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Copy the API key to `.env`

### Twitter API Keys

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app or select existing
3. Go to "Keys and tokens"
4. Generate API Key & Secret
5. Generate Access Token & Secret
6. Copy all four values to `.env`

## UI Considerations

### Current State (MVP)

The UI doesn't have credential input fields for YouTube/Twitter because:
- Global credentials are set in `.env`
- All users share the same API keys
- Simpler for MVP

### Adding Source in UI

```typescript
// Frontend form for YouTube
{
  source_type: "youtube",
  name: "Channel Name",
  config: {
    channel_id: "UC...",
    fetch_type: "uploads"
  }
  // No credentials field in UI
}
```

### Future Enhancement

For production, you might want to add credential fields:

```typescript
// Optional credential inputs
<Form>
  <Input name="channel_id" label="Channel ID" required />
  <Input name="fetch_type" label="Fetch Type" required />
  
  {/* Optional advanced section */}
  <Collapsible title="Advanced: Use Custom API Key">
    <Input 
      name="api_key" 
      label="Your YouTube API Key" 
      placeholder="Leave empty to use default"
    />
  </Collapsible>
</Form>
```

## Testing

### Test with Global Credentials

```bash
# 1. Set credentials in .env
YOUTUBE_API_KEY=your_key

# 2. Add source without credentials
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "youtube",
    "name": "Test",
    "config": {"channel_id": "UC_x5XG1OV2P6uZZ5FSM9Ttw", "fetch_type": "uploads"}
  }'

# 3. Trigger crawl
curl -X POST http://localhost:8000/api/sources/{source_id}/crawl \
  -H "Authorization: Bearer $TOKEN"

# 4. Check status
curl http://localhost:8000/api/sources/{source_id}/status \
  -H "Authorization: Bearer $TOKEN"
```

### Test with User Credentials

```bash
# Add source with user-specific credentials
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "youtube",
    "name": "Test",
    "config": {"channel_id": "UC...", "fetch_type": "uploads"},
    "credentials": {"api_key": "user_specific_key"}
  }'
```

## Troubleshooting

### Error: "Connection validation failed"

**Cause:** No API credentials available

**Solution:**
1. Check `.env` file has the required keys
2. Restart backend after updating `.env`
3. Verify API keys are valid

### Error: "Unsupported source type"

**Cause:** Connector not registered or import failed

**Solution:**
1. Check connector is imported in `__init__.py`
2. Check for import errors in logs
3. Install required dependencies

### YouTube/Twitter Not Working

**Debug steps:**

```python
# Check if settings loaded
from app.core.config import settings
print(settings.YOUTUBE_API_KEY)  # Should print your key
print(settings.TWITTER_API_KEY)  # Should print your key

# Check connector initialization
from app.services.sources import SourceRegistry
connector_class = SourceRegistry.get_connector('youtube')
connector = connector_class(
    source_id="test",
    config={"channel_id": "UC...", "fetch_type": "uploads"},
    credentials={}  # Empty - should use global
)
print(connector.youtube)  # Should be initialized
```

## Security Best Practices

### 1. Never Commit `.env`

```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

### 2. Use Environment-Specific Files

```
.env.development
.env.production
.env.example  # Template without real keys
```

### 3. Rotate Keys Regularly

- Change API keys every 90 days
- Revoke old keys after rotation
- Use different keys for dev/prod

### 4. Limit API Key Permissions

- YouTube: Only enable "YouTube Data API v3"
- Twitter: Use read-only permissions if possible

### 5. Monitor Usage

- Track API quota usage
- Set up alerts for unusual activity
- Review access logs regularly

## Summary

| Source | Global Credentials | User Credentials | Required |
|--------|-------------------|------------------|----------|
| RSS | ❌ | ❌ | No |
| YouTube | ✅ (from .env) | ✅ (optional) | One of them |
| Twitter | ✅ (from .env) | ✅ (optional) | One of them |
| Substack | ❌ | ❌ | No |
| Medium | ❌ | ❌ | No |
| LinkedIn | ❌ | ✅ (required) | Yes |

**For MVP:** Use global credentials in `.env` for YouTube and Twitter. This is simpler and works for all users.

**For Production:** Consider adding UI for user-specific credentials to avoid rate limit sharing.
