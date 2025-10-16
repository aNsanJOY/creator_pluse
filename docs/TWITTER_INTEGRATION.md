# Twitter Integration Guide

## Overview

The Twitter integration allows users to connect their Twitter accounts and automatically fetch tweets for newsletter content curation. This guide covers setup, usage, and troubleshooting.

## Features

- **OAuth 1.0a Authentication**: Secure Twitter account connection
- **Multiple Fetch Types**: Timeline, mentions, and liked tweets
- **Rate Limit Handling**: Automatic retry with exponential backoff
- **Delta Crawling**: Only fetch new tweets since last crawl
- **Background Processing**: Scheduled and on-demand crawling
- **Rich Metadata**: Engagement metrics, hashtags, mentions, and URLs

## Setup

### 1. Twitter Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app or use an existing one
3. Enable OAuth 1.0a authentication
4. Set callback URL to: `http://localhost:8000/api/twitter/oauth/callback` (for development)
5. Note down your API credentials:
   - API Key (Consumer Key)
   - API Secret (Consumer Secret)

### 2. Environment Configuration

Add the following to your `.env` file:

```env
# Twitter API Configuration
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here

# Application URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

### 3. Database Schema

The Twitter integration uses the following tables:

- **sources**: Stores Twitter connection details
- **source_content_cache**: Stores fetched tweets

Ensure your database schema is up to date by running migrations.

## API Endpoints

### Initialize OAuth Flow

**POST** `/api/twitter/oauth/init`

Starts the Twitter OAuth flow and returns an authorization URL.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "authorization_url": "https://api.twitter.com/oauth/authorize?oauth_token=...",
  "oauth_token": "temp_oauth_token"
}
```

### Complete OAuth Flow

**POST** `/api/twitter/oauth/callback`

Completes the OAuth flow after user authorization.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "oauth_token": "temp_oauth_token",
  "oauth_verifier": "verifier_from_twitter"
}
```

**Response:**
```json
{
  "source_id": "uuid",
  "username": "twitter_handle",
  "status": "active"
}
```

### Trigger Manual Crawl

**POST** `/api/sources/{source_id}/crawl`

Manually trigger a crawl for a Twitter source.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "message": "Crawl started",
  "source_id": "uuid",
  "source_name": "Twitter - @username"
}
```

### Disconnect Twitter

**DELETE** `/api/twitter/{source_id}`

Disconnect a Twitter source.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "message": "Twitter source disconnected successfully"
}
```

## Usage Flow

### Frontend Integration

1. **Initiate OAuth:**
   ```javascript
   const response = await fetch('/api/twitter/oauth/init', {
     method: 'POST',
     headers: {
       'Authorization': `Bearer ${token}`
     }
   });
   const { authorization_url } = await response.json();
   
   // Redirect user to authorization URL
   window.location.href = authorization_url;
   ```

2. **Handle Callback:**
   ```javascript
   // Twitter redirects to: /sources/twitter/callback?oauth_token=...&oauth_verifier=...
   const params = new URLSearchParams(window.location.search);
   const oauth_token = params.get('oauth_token');
   const oauth_verifier = params.get('oauth_verifier');
   
   // Complete OAuth
   await fetch('/api/twitter/oauth/callback', {
     method: 'POST',
     headers: {
       'Authorization': `Bearer ${token}`,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({ oauth_token, oauth_verifier })
   });
   ```

## Configuration Options

When creating a Twitter source, you can configure:

```json
{
  "config": {
    "username": "twitter_handle",
    "fetch_type": "timeline",  // Options: "timeline", "mentions", "likes"
    "max_results": 100         // Max tweets per crawl (1-100)
  }
}
```

### Fetch Types

- **timeline**: User's own tweets (excludes retweets and replies)
- **mentions**: Tweets mentioning the user
- **likes**: Tweets liked by the user

## Crawling

### Scheduled Crawling

The system automatically crawls Twitter sources:
- **Daily**: 2:00 AM UTC (all sources)
- **Hourly**: Every hour (high-priority sources)

### Manual Crawling

Trigger a manual crawl via API:
```bash
curl -X POST http://localhost:8000/api/sources/{source_id}/crawl \
  -H "Authorization: Bearer <token>"
```

### Delta Crawling

The crawler only fetches tweets published after the last successful crawl:
- First crawl: Fetches tweets from last 7 days
- Subsequent crawls: Fetches only new tweets since `last_crawled_at`

## Rate Limiting

Twitter API has the following rate limits:

### API v2 Endpoints
- **User tweets**: 1,500 requests per 15 minutes
- **User mentions**: 450 requests per 15 minutes
- **Liked tweets**: 75 requests per 15 minutes

### Handling
The connector automatically:
1. Waits when rate limit is hit (15 minutes default)
2. Uses Tweepy's built-in `wait_on_rate_limit=True`
3. Logs rate limit events

## Stored Data

Each tweet is stored with:

```json
{
  "title": "Tweet by @username",
  "content": "Tweet text content...",
  "url": "https://twitter.com/username/status/123456",
  "published_at": "2024-01-01T12:00:00Z",
  "metadata": {
    "tweet_id": "123456",
    "author": "username",
    "engagement": {
      "likes": 100,
      "retweets": 50,
      "replies": 25,
      "quotes": 10
    },
    "hashtags": ["tech", "ai"],
    "mentions": ["other_user"],
    "urls": ["https://example.com"]
  }
}
```

## Troubleshooting

### OAuth Errors

**Error**: "Invalid or expired OAuth token"
- **Solution**: The OAuth flow timed out. Restart the connection process.

**Error**: "Twitter authentication failed"
- **Solution**: Check your API credentials in `.env` file.

### Crawling Errors

**Error**: "Connection validation failed"
- **Solution**: Re-authenticate your Twitter account. Tokens may have expired.

**Error**: "Rate limit reached"
- **Solution**: Wait 15 minutes or reduce crawl frequency.

**Error**: "User not found"
- **Solution**: Verify the Twitter username in source config is correct.

### Common Issues

1. **No tweets fetched**
   - Check if the user has posted tweets in the last 7 days
   - Verify `fetch_type` is set correctly
   - Check source status: `GET /api/sources/{source_id}/status`

2. **Duplicate tweets**
   - The system automatically deduplicates by URL
   - Check `source_content_cache` table for duplicates

3. **Missing engagement data**
   - Ensure you're using Twitter API v2 (client-based, not API v1.1)
   - Check `tweet_fields` includes `public_metrics`

## Security

- **Credentials Storage**: OAuth tokens are encrypted in the database
- **Token Refresh**: Tokens don't expire but can be revoked by user
- **Scope**: Only read access to public tweets
- **Rate Limiting**: Prevents API abuse

## Best Practices

1. **Crawl Frequency**: Don't crawl more than once per hour for most users
2. **Error Handling**: Monitor source status and error messages
3. **Data Retention**: Clean up old cached content (90 days recommended)
4. **User Privacy**: Only fetch public tweets, respect user privacy settings

## Future Enhancements

- [ ] Support for Twitter Lists
- [ ] Search-based content fetching
- [ ] Tweet thread detection and grouping
- [ ] Media attachment handling (images, videos)
- [ ] Automatic token refresh
- [ ] Webhook support for real-time updates
- [ ] Advanced filtering (by hashtag, keyword, etc.)

## References

- [Twitter API Documentation](https://developer.twitter.com/en/docs)
- [Tweepy Documentation](https://docs.tweepy.org/)
- [OAuth 1.0a Specification](https://oauth.net/core/1.0a/)
