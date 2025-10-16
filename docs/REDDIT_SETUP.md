# Reddit API Setup Guide

## Overview

The Reddit connector allows you to fetch posts from subreddits using the Reddit API. Reddit API is **completely free** with reasonable rate limits.

---

## Rate Limits

| Authentication | Requests per Minute | Cost |
|----------------|---------------------|------|
| **With App Credentials** | 60 | Free |

**Note:** Reddit requires app credentials (client ID and secret), but they're free and easy to create.

---

## Setup Instructions

### Step 1: Create a Reddit App

1. **Go to Reddit Apps Page**
   - Visit: https://www.reddit.com/prefs/apps
   - Or: Reddit → Preferences → Apps → "are you a developer? create an app..."

2. **Create App**
   - Click "create app" or "create another app"
   - Fill in the form:
     - **Name:** `CreatorPulse` (or any name)
     - **App type:** Select **"script"**
     - **Description:** `Content aggregation for newsletters` (optional)
     - **About URL:** Leave blank or use your website
     - **Redirect URI:** `http://localhost:8000` (required but not used)

3. **Get Credentials**
   - After creating, you'll see your app
   - **Client ID:** The string under your app name (looks like: `abc123XYZ456`)
   - **Client Secret:** The "secret" field (looks like: `xyz789ABC123-secretstring`)

### Step 2: Add Credentials to `.env`

Open `backend/.env` and add:

```env
# Reddit API (Optional - Free)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=CreatorPulse/1.0
```

**Important:** The `REDDIT_USER_AGENT` should be descriptive. Format: `AppName/Version`

### Step 3: Restart Backend

```bash
cd backend
python app/main.py
```

---

## Using the Reddit Connector

### Configuration Options

When adding a Reddit source, you need to configure:

```json
{
  "source_type": "reddit",
  "name": "Angular Subreddit",
  "config": {
    "subreddit": "Angular2",
    "fetch_type": "hot",
    "max_results": 20
  }
}
```

### Configuration Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `subreddit` | string | Yes | Subreddit name (without r/) | `"Angular2"` |
| `fetch_type` | string | Yes | Type of posts to fetch | `"hot"` |
| `max_results` | integer | No | Max posts to fetch (default: 10, max: 100) | `20` |
| `time_filter` | string | No | For 'top' type: time period | `"week"` |

### Supported Fetch Types

#### 1. **hot** - Hot Posts (Recommended)

Fetches currently trending/hot posts from the subreddit.

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "reddit",
    "name": "Angular Hot Posts",
    "config": {
      "subreddit": "Angular2",
      "fetch_type": "hot",
      "max_results": 20
    }
  }'
```

**Best for:** Current discussions and trending topics

#### 2. **new** - New Posts

Fetches newest posts from the subreddit.

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "reddit",
    "name": "Angular New Posts",
    "config": {
      "subreddit": "Angular2",
      "fetch_type": "new",
      "max_results": 20
    }
  }'
```

**Best for:** Latest discussions and fresh content

#### 3. **top** - Top Posts

Fetches top-rated posts from a specific time period.

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "reddit",
    "name": "Angular Top Weekly",
    "config": {
      "subreddit": "Angular2",
      "fetch_type": "top",
      "time_filter": "week",
      "max_results": 15
    }
  }'
```

**Time filter options:**
- `hour` - Top posts from last hour
- `day` - Top posts from last 24 hours
- `week` - Top posts from last week (recommended)
- `month` - Top posts from last month
- `year` - Top posts from last year
- `all` - Top posts of all time

**Best for:** High-quality, well-received content

#### 4. **rising** - Rising Posts

Fetches posts that are gaining traction.

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "reddit",
    "name": "Angular Rising",
    "config": {
      "subreddit": "Angular2",
      "fetch_type": "rising",
      "max_results": 15
    }
  }'
```

**Best for:** Emerging discussions and early trending content

---

## Popular Angular Subreddits

### Primary Angular Subreddits

```bash
# r/Angular2 - Main Angular community
{
  "subreddit": "Angular2",
  "fetch_type": "hot",
  "max_results": 20
}

# r/webdev - General web development (includes Angular)
{
  "subreddit": "webdev",
  "fetch_type": "hot",
  "max_results": 15
}

# r/javascript - JavaScript community (includes Angular)
{
  "subreddit": "javascript",
  "fetch_type": "hot",
  "max_results": 15
}

# r/Frontend - Frontend development
{
  "subreddit": "Frontend",
  "fetch_type": "hot",
  "max_results": 10
}

# r/typescript - TypeScript (used by Angular)
{
  "subreddit": "typescript",
  "fetch_type": "hot",
  "max_results": 10
}
```

---

## Content Metadata

Each Reddit post includes rich metadata:

```json
{
  "post_id": "abc123",
  "subreddit": "Angular2",
  "author": "username",
  "post_type": "text",
  "score": 42,
  "upvote_ratio": 0.95,
  "num_comments": 15,
  "awards": 2,
  "is_original_content": false,
  "flair": "Discussion",
  "nsfw": false,
  "spoiler": false,
  "stickied": false,
  "locked": false,
  "permalink": "https://reddit.com/r/Angular2/comments/...",
  "external_url": "https://example.com"
}
```

### Post Types

- **text** - Text-only self posts
- **link** - External link posts
- **image** - Image posts (i.redd.it, imgur)
- **video** - Video posts (v.redd.it, YouTube)

---

## Delta Crawling

The Reddit connector supports delta crawling:

- **First crawl:** Fetches posts from last 7 days
- **Subsequent crawls:** Only fetches posts since last crawl
- **Efficient:** Reduces API calls and stays within rate limits

---

## Rate Limit Handling

The connector automatically handles rate limits:

1. **Detects rate limit exceeded**
2. **Waits 60 seconds** (Reddit's rate limit window)
3. **Retries automatically**
4. **Logs rate limit events**

### Best Practices for Rate Limits

- Don't fetch from too many subreddits simultaneously
- Use reasonable `max_results` values (10-20)
- Implement crawl scheduling (every 30-60 minutes)
- Monitor logs for rate limit warnings

---

## Troubleshooting

### Common Issues

#### 1. **401 Unauthorized**

**Cause:** Invalid credentials

**Solution:**
- Verify `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in `.env`
- Ensure no extra spaces or quotes
- Recreate Reddit app if needed
- Restart backend

#### 2. **404 Not Found**

**Cause:** Subreddit doesn't exist

**Solution:**
- Verify subreddit name (without r/ prefix)
- Check subreddit exists on reddit.com
- Try: `Angular2` not `r/Angular2`

#### 3. **403 Forbidden**

**Cause:** Subreddit is private, banned, or quarantined

**Solution:**
- Verify subreddit is public
- Check if subreddit is quarantined
- Try a different subreddit

#### 4. **PRAW Not Installed**

**Cause:** Missing dependency

**Solution:**
```bash
pip install praw==7.7.1
```

#### 5. **Too Many Requests**

**Cause:** Rate limit exceeded (60 requests/minute)

**Solution:**
- Wait 60 seconds
- Reduce `max_results`
- Reduce crawl frequency
- Don't crawl multiple subreddits simultaneously

---

## Testing

### Test Reddit Connection

Create `test_reddit.py`:

```python
import praw
import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')
user_agent = os.getenv('REDDIT_USER_AGENT', 'CreatorPulse/1.0')

try:
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    reddit.read_only = True
    
    print(f"✅ Connected! Read-only mode: {reddit.read_only}")
    
    # Test subreddit access
    subreddit = reddit.subreddit("Angular2")
    print(f"✅ Subreddit found: r/{subreddit.display_name}")
    print(f"   Subscribers: {subreddit.subscribers:,}")
    print(f"   Description: {subreddit.public_description[:100]}...")
    
    # Fetch a few posts
    print("\n📝 Recent posts:")
    for post in subreddit.hot(limit=3):
        print(f"   - {post.title[:60]}... ({post.score} points)")
    
except Exception as e:
    print(f"❌ Error: {e}")
```

Run:
```bash
cd backend
python test_reddit.py
```

---

## Best Practices

### 1. **Choose the Right Fetch Type**
- **hot:** Current discussions and trending (recommended)
- **new:** Latest posts and fresh content
- **top:** High-quality, well-received content
- **rising:** Emerging discussions

### 2. **Set Appropriate max_results**
- **Active subreddits (r/Angular2):** 15-20 posts
- **Large subreddits (r/webdev):** 10-15 posts
- **Niche subreddits:** 5-10 posts

### 3. **Use Time Filters for Top Posts**
- **Daily newsletter:** `time_filter: "day"`
- **Weekly newsletter:** `time_filter: "week"`
- **Monthly newsletter:** `time_filter: "month"`

### 4. **Monitor Content Quality**
- Filter by score (upvotes)
- Check upvote_ratio (quality indicator)
- Look at num_comments (engagement)
- Consider post flair (categorization)

### 5. **Security**
- ✅ Store credentials in `.env` file
- ✅ Never commit credentials to git
- ✅ Use descriptive user agent
- ✅ Respect Reddit's API terms

---

## Content Filtering

You can filter Reddit posts in your application logic:

```python
# Filter by score (minimum upvotes)
if post.metadata['score'] >= 10:
    # Include post

# Filter by upvote ratio (quality)
if post.metadata['upvote_ratio'] >= 0.8:
    # High quality post

# Filter by comments (engagement)
if post.metadata['num_comments'] >= 5:
    # Active discussion

# Filter by flair
if post.metadata['flair'] in ['Discussion', 'Tutorial', 'News']:
    # Relevant content

# Exclude NSFW
if not post.metadata['nsfw']:
    # Safe content
```

---

## API Reference

### Reddit API Documentation

- **Official API Docs:** https://www.reddit.com/dev/api
- **PRAW Documentation:** https://praw.readthedocs.io/
- **Create Reddit App:** https://www.reddit.com/prefs/apps
- **API Rules:** https://github.com/reddit-archive/reddit/wiki/API

---

## Summary

### Key Features

✅ **Completely Free** - No cost, 60 requests/minute  
✅ **Multiple Fetch Types** - Hot, new, top, rising  
✅ **Rich Metadata** - Score, comments, awards, flair  
✅ **Delta Crawling** - Only fetch new posts  
✅ **Rate Limit Handling** - Automatic retry  
✅ **Content Filtering** - By score, ratio, comments  

### Quick Start

1. Create Reddit app at https://www.reddit.com/prefs/apps
2. Add credentials to `.env`
3. Restart backend
4. Add Reddit source with subreddit and fetch_type
5. Start crawling!

### Recommended Setup for Angular

```bash
# Add r/Angular2 hot posts
{
  "subreddit": "Angular2",
  "fetch_type": "hot",
  "max_results": 20
}

# Add r/Angular2 top weekly posts
{
  "subreddit": "Angular2",
  "fetch_type": "top",
  "time_filter": "week",
  "max_results": 10
}
```

---

**Cost:** Free  
**Rate Limit:** 60 requests/minute  
**Best For:** Community discussions, Q&A, tutorials  
**Setup Time:** 3 minutes
