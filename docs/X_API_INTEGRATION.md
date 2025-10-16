# X (Twitter) API Integration Guide

## Overview

CreatorPulse integrates with X (formerly Twitter) API v2 to fetch user posts, mentions, and liked content. This document provides comprehensive information about the integration.

---

## Current Implementation Status

### ✅ Fully Implemented Features

1. **OAuth 1.0a Authentication** - User context with full access
2. **OAuth 2.0 Bearer Token** - App-only authentication (read-only)
3. **User Timeline Fetching** - Get user's posts
4. **Mentions Fetching** - Get mentions of a user
5. **Liked Posts Fetching** - Get posts liked by a user
6. **Rate Limit Handling** - Automatic retry with exponential backoff
7. **Delta Crawling** - Only fetch new content since last crawl
8. **Error Handling** - Comprehensive error messages with actionable guidance

### 📋 API Endpoints Used

| Endpoint | Method | Tier Required | Purpose |
|----------|--------|---------------|---------|
| `GET /2/users/by/username/:username` | User lookup | Free+ | Get user ID from username |
| `GET /2/users/:id/tweets` | Timeline | Basic+ | Fetch user's posts |
| `GET /2/users/:id/mentions` | Mentions | Basic+ | Fetch mentions |
| `GET /2/users/:id/liked_tweets` | Likes | Basic+ | Fetch liked posts |
| `GET /2/users/me` | Auth validation | Free+ | Validate credentials |

---

## X API Tier Structure (October 2024)

### Current Pricing

| Tier | Monthly Cost | Read Limit | Write Limit | Timeline Access |
|------|-------------|------------|-------------|-----------------|
| **Free** | $0 | 500 posts | 50 posts | ❌ No |
| **Basic** | **$200** | Higher | Higher | ✅ Yes |
| **Pro** | Higher | Professional | Professional | ✅ Yes |
| **Enterprise** | Custom | Custom | Custom | ✅ Yes |

### Important Changes (October 2024)

- **Basic tier price doubled** from $100 to $200/month
- **Free tier limits reduced** to 500 posts/month read
- **Annual subscriptions** now available at discounted rates
- **Timeline endpoints** now require at least Basic tier

### What This Means for CreatorPulse

⚠️ **Critical:** The Free tier (500 posts/month) is **insufficient** for CreatorPulse's use case. You **must** subscribe to:
- **Basic tier** ($200/month) - Minimum requirement
- **Pro tier** - For higher volume or multiple users

---

## Authentication Methods

### Method 1: OAuth 1.0a User Context (Recommended)

**Required Credentials:**
```env
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
```

**Advantages:**
- Full access to user timeline, mentions, likes
- Can perform actions on behalf of user
- Works with all endpoints

**Use Case:** When you need to access user-specific data

### Method 2: OAuth 2.0 Bearer Token

**Required Credentials:**
```env
TWITTER_BEARER_TOKEN=your_bearer_token
```

**Advantages:**
- Simpler authentication (single token)
- App-only access

**Limitations:**
- Read-only access
- Cannot access some user-specific endpoints
- Limited to public data

**Use Case:** When you only need public data and don't need user context

---

## Implementation Details

### Code Structure

```
backend/app/services/sources/
├── twitter_connector.py    # Main X API connector
└── base.py                 # Base connector interface
```

### Key Classes

#### `TwitterConnector`

**Inherits:** `BaseSourceConnector`

**Key Methods:**
- `_initialize_client()` - Set up Tweepy client with credentials
- `validate_connection()` - Test API credentials
- `fetch_content(since)` - Fetch posts with delta crawling
- `_transform_tweet()` - Convert X post to SourceContent
- `handle_rate_limit()` - Handle API rate limits

### Configuration Options

When adding an X source, you can configure:

```json
{
  "source_type": "twitter",
  "name": "My X Source",
  "config": {
    "username": "elonmusk",
    "fetch_type": "timeline",
    "max_results": 10
  }
}
```

**Config Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `username` | string | Yes | - | X username (without @) |
| `fetch_type` | string | Yes | - | `timeline`, `mentions`, or `likes` |
| `max_results` | integer | No | 10 | Number of posts to fetch (max 100) |

---

## Rate Limits

### X API v2 Rate Limits (Basic Tier)

| Endpoint | Requests per 15 min | Posts per request |
|----------|---------------------|-------------------|
| User lookup | 300 | 1 |
| User timeline | 1,500 | 100 |
| User mentions | 180 | 100 |
| Liked tweets | 75 | 100 |

### How CreatorPulse Handles Rate Limits

1. **Automatic Detection** - Catches `tweepy.TooManyRequests` exception
2. **Exponential Backoff** - Waits 15 minutes before retry
3. **Graceful Degradation** - Returns empty list instead of crashing
4. **Logging** - Logs rate limit events for monitoring

---

## Error Handling

### Common Errors and Solutions

#### 1. `401 Unauthorized`

**Causes:**
- Invalid API credentials
- Expired access tokens
- Insufficient API tier (Free tier trying to access timeline)
- Wrong permissions

**Solutions:**
- Verify all 4 credentials in `.env`
- Regenerate tokens in X Developer Portal
- Upgrade to Basic tier ($200/month)
- Check app has "Read" permissions

#### 2. `403 Forbidden`

**Causes:**
- Free tier accessing Basic-tier-only endpoints
- App doesn't have required permissions
- Trying to access protected/private content

**Solutions:**
- Upgrade to Basic or Pro tier
- Check app permissions in Developer Portal
- Ensure target user account is public

#### 3. `404 Not Found`

**Causes:**
- Username doesn't exist
- User account suspended/deleted
- Typo in username

**Solutions:**
- Verify username on x.com
- Remove @ symbol from username
- Check if account is active

#### 4. `429 Too Many Requests`

**Causes:**
- Exceeded rate limits
- Too many requests in short time

**Solutions:**
- Wait 15 minutes
- Reduce `max_results`
- Implement request throttling

---

## Delta Crawling

CreatorPulse implements delta crawling to only fetch new content:

### How It Works

1. **First Crawl:** Fetches posts from last 7 days
2. **Subsequent Crawls:** Only fetches posts since last crawl
3. **Timestamp Tracking:** Uses `start_time` parameter in API calls
4. **Format:** RFC 3339 format (e.g., `2024-10-14T18:30:00Z`)

### Benefits

- **Reduced API calls** - Only fetch new content
- **Lower costs** - Stay within rate limits
- **Faster processing** - Less data to process
- **Efficient** - Avoid duplicate content

### Implementation

```python
# Calculate start_time for delta crawl
if since:
    start_time = since.isoformat() + "Z"
else:
    # Default to last 7 days if no since parameter
    start_time = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"

# Fetch with start_time
tweets = client.get_users_tweets(
    id=user_id,
    start_time=start_time,
    ...
)
```

---

## Data Transformation

### X Post → SourceContent

CreatorPulse transforms X posts into a standardized `SourceContent` format:

```python
SourceContent(
    title=f"Post by @{username}",
    content=tweet.text,
    url=f"https://twitter.com/{username}/status/{tweet_id}",
    published_at=tweet.created_at,
    metadata={
        "tweet_id": str(tweet_id),
        "author": username,
        "engagement": {
            "likes": like_count,
            "retweets": retweet_count,
            "replies": reply_count,
            "quotes": quote_count
        },
        "hashtags": [...],
        "mentions": [...],
        "urls": [...]
    }
)
```

### Metadata Extracted

- **Engagement metrics** - Likes, retweets, replies, quotes
- **Hashtags** - All hashtags in the post
- **Mentions** - All @mentions
- **URLs** - Expanded URLs from the post
- **Post ID** - Unique identifier
- **Author** - Username

---

## Testing

### Diagnostic Tool

Run the credential test script:

```bash
cd backend
python test_twitter_credentials.py
```

**What it tests:**
1. ✅ Credentials loaded from `.env`
2. ✅ Tweepy client initialization
3. ✅ Authentication (get_me)
4. ✅ Fetching posts
5. ✅ Public user access

### Manual Testing

```bash
# Test adding X source
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "twitter",
    "name": "Test X Source",
    "config": {
      "username": "XDevelopers",
      "fetch_type": "timeline",
      "max_results": 5
    }
  }'

# Test crawling
curl -X POST http://localhost:8000/api/sources/{source_id}/crawl \
  -H "Authorization: Bearer $TOKEN"
```

---

## Migration from Twitter to X

### What Changed

1. **Branding:** Twitter → X
2. **Domain:** developer.twitter.com → developer.x.com
3. **Terminology:** Tweets → Posts
4. **Pricing:** Basic tier $100 → $200 (Oct 2024)
5. **Tiers:** Essential/Elevated → Free/Basic/Pro

### What Stayed the Same

1. **API endpoints** - Still use `/2/users/:id/tweets`
2. **Authentication** - OAuth 1.0a and 2.0 still work
3. **Tweepy library** - Still the recommended Python client
4. **Environment variables** - Still use `TWITTER_*` prefix
5. **Source type** - Still registered as "twitter" internally

### Backward Compatibility

- ✅ Old `developer.twitter.com` URLs redirect to `developer.x.com`
- ✅ Existing credentials continue to work
- ✅ No code changes required for rebranding
- ✅ Environment variable names unchanged

---

## Best Practices

### 1. Credential Management

- ✅ Store credentials in `.env` file
- ✅ Never commit `.env` to git
- ✅ Use separate credentials for dev/prod
- ✅ Rotate credentials every 90 days
- ✅ Revoke old credentials after rotation

### 2. Rate Limit Management

- ✅ Implement exponential backoff
- ✅ Monitor API usage in Developer Portal
- ✅ Set up alerts for rate limit warnings
- ✅ Use delta crawling to reduce API calls
- ✅ Batch requests when possible

### 3. Error Handling

- ✅ Log all API errors
- ✅ Provide actionable error messages
- ✅ Gracefully handle rate limits
- ✅ Retry transient errors
- ✅ Don't retry 4xx errors (except 429)

### 4. Cost Optimization

- ✅ Use delta crawling to minimize API calls
- ✅ Set appropriate `max_results` values
- ✅ Monitor monthly usage
- ✅ Consider caching frequently accessed data
- ✅ Implement request throttling

### 5. Security

- ✅ Use environment variables for credentials
- ✅ Enable HTTPS for all API calls
- ✅ Validate all user inputs
- ✅ Sanitize usernames before API calls
- ✅ Log security events

---

## Troubleshooting

### Quick Checklist

- [ ] All 4 credentials in `.env`
- [ ] No typos or extra spaces in credentials
- [ ] Basic tier subscription active ($200/month)
- [ ] App has "Read" permissions
- [ ] Backend restarted after `.env` changes
- [ ] X API status is operational

### Diagnostic Steps

1. **Run test script:** `python test_twitter_credentials.py`
2. **Check logs:** Look for initialization messages
3. **Verify tier:** Check Developer Portal for current tier
4. **Test credentials:** Try manual API call with curl
5. **Check status:** Visit https://api.twitterstat.us/

### Common Issues

| Issue | Quick Fix |
|-------|-----------|
| 401 Unauthorized | Upgrade to Basic tier |
| 403 Forbidden | Check app permissions |
| 404 Not Found | Verify username |
| 429 Rate Limit | Wait 15 minutes |
| No credentials | Add to `.env` |

---

## Resources

### Official Documentation

- **X API Docs:** https://docs.x.com/
- **X Developer Portal:** https://developer.x.com/en/portal/dashboard
- **API Products:** https://developer.x.com/en/products/twitter-api
- **Rate Limits:** https://docs.x.com/x-api/rate-limits

### Libraries & Tools

- **Tweepy:** https://docs.tweepy.org/
- **X API Status:** https://api.twitterstat.us/
- **Developer Community:** https://twittercommunity.com/

### CreatorPulse Documentation

- **Quick Fix Guide:** `../TWITTER_QUICK_FIX.md`
- **Troubleshooting Guide:** `./TWITTER_TROUBLESHOOTING.md`
- **API Credentials Guide:** `./API_CREDENTIALS_GUIDE.md`

---

## Summary

### Key Takeaways

1. **Basic tier required** - Free tier (500 posts/month) is insufficient
2. **$200/month cost** - Basic tier doubled in price (Oct 2024)
3. **OAuth 1.0a recommended** - Full access to all endpoints
4. **Delta crawling implemented** - Efficient content fetching
5. **Comprehensive error handling** - Actionable error messages
6. **Rate limit handling** - Automatic retry with backoff
7. **X rebranding complete** - Updated to developer.x.com URLs

### Next Steps

1. ✅ Ensure Basic tier subscription is active
2. ✅ Add credentials to `.env`
3. ✅ Run test script to validate
4. ✅ Add X source through UI
5. ✅ Monitor API usage in Developer Portal

---

**Last Updated:** October 2024  
**API Version:** X API v2  
**Tweepy Version:** 4.x+  
**Tier Pricing:** Basic $200/month
