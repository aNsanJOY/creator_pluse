# Free Alternatives to X (Twitter) API

## Overview

X API costs **$200/month** for Basic tier access. This guide shows you **completely free alternatives** that are already implemented in CreatorPulse.

---

## Quick Comparison

| Source | Cost | Setup Time | Rate Limit | Best For |
|--------|------|------------|------------|----------|
| **X API** | $200/month | 5 min | 1,500 req/15min | Real-time tweets |
| **RSS Feeds** | Free | 1 min | Unlimited | Blogs, news sites |
| **GitHub** | Free | 2 min | 5,000 req/hour | Repository updates |
| **Reddit** | Free | 3 min | 60 req/minute | Community discussions |
| **YouTube** | Free | 5 min | 10,000 units/day | Video content |
| **Medium** | Free | 1 min | Unlimited | Articles |
| **Dev.to** | Free | 1 min | Unlimited | Developer content |

---

## For Angular Updates (Recommended Setup)

### Option 1: Free RSS + GitHub (Best Coverage)

#### 1. Angular Official Blog (RSS)
```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "rss",
    "name": "Angular Blog",
    "config": {"feed_url": "https://blog.angular.io/feed"}
  }'
```

#### 2. Angular GitHub Releases
```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "github",
    "name": "Angular Releases",
    "config": {
      "repository": "angular/angular",
      "fetch_type": "releases",
      "max_results": 10
    }
  }'
```

#### 3. Angular on Medium
```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "medium",
    "name": "Angular Medium",
    "config": {
      "feed_type": "tag",
      "identifier": "angular"
    }
  }'
```

#### 4. r/Angular2 Subreddit
```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "reddit",
    "name": "Angular Reddit",
    "config": {
      "subreddit": "Angular2",
      "fetch_type": "hot",
      "max_results": 20
    }
  }'
```

**Total Cost:** $0/month  
**Setup Time:** 10 minutes  
**Coverage:** Official updates, releases, community content, discussions

---

## Setup Instructions

### 1. GitHub (Recommended - 5,000 requests/hour)

**Why:** Track Angular repository releases, commits, and issues

**Setup:**
1. Create Personal Access Token: https://github.com/settings/tokens
2. Add to `.env`:
   ```env
   GITHUB_TOKEN=ghp_your_token_here
   ```
3. Restart backend

**Add Angular Repository:**
```json
{
  "source_type": "github",
  "name": "Angular Releases",
  "config": {
    "repository": "angular/angular",
    "fetch_type": "releases",
    "max_results": 10
  }
}
```

**Full Guide:** [GITHUB_SETUP.md](./GITHUB_SETUP.md)

---

### 2. Reddit (60 requests/minute)

**Why:** Community discussions, Q&A, tutorials

**Setup:**
1. Create Reddit app: https://www.reddit.com/prefs/apps
2. Select "script" type
3. Add to `.env`:
   ```env
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=CreatorPulse/1.0
   ```
4. Restart backend

**Add r/Angular2:**
```json
{
  "source_type": "reddit",
  "name": "Angular Reddit",
  "config": {
    "subreddit": "Angular2",
    "fetch_type": "hot",
    "max_results": 20
  }
}
```

**Full Guide:** [REDDIT_SETUP.md](./REDDIT_SETUP.md)

---

### 3. RSS Feeds (Already Implemented)

**Why:** Official blogs, news sites, no API needed

**Add Angular Blog:**
```json
{
  "source_type": "rss",
  "name": "Angular Blog",
  "config": {
    "feed_url": "https://blog.angular.io/feed"
  }
}
```

**More Angular RSS Feeds:**
- Dev.to Angular: `https://dev.to/feed/tag/angular`
- Hashnode Angular: `https://hashnode.com/n/angular/rss`

---

### 4. YouTube (Already Implemented)

**Why:** Video tutorials, conference talks

**Setup:**
1. Get free API key: https://console.cloud.google.com/
2. Add to `.env`:
   ```env
   YOUTUBE_API_KEY=your_api_key
   ```

**Add Angular YouTube:**
```json
{
  "source_type": "youtube",
  "name": "Angular YouTube",
  "config": {
    "channel_id": "UCbn1OgGei-DV7aSRo_HaAiw",
    "fetch_type": "uploads"
  }
}
```

---

## Installation

### Install New Dependencies

```bash
cd backend
pip install PyGithub==2.1.1 praw==7.7.1
```

Or install all:
```bash
pip install -r requirements.txt
```

---

## Complete Free Setup for Angular

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Get API Credentials

**GitHub (2 minutes):**
- Go to: https://github.com/settings/tokens
- Generate token (no scopes needed for public repos)
- Copy token

**Reddit (3 minutes):**
- Go to: https://www.reddit.com/prefs/apps
- Create "script" app
- Copy client ID and secret

### Step 3: Update `.env`

```env
# GitHub API (Optional - Free with 5,000 requests/hour)
GITHUB_TOKEN=ghp_your_token_here

# Reddit API (Optional - Free)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=CreatorPulse/1.0
```

### Step 4: Restart Backend

```bash
python app/main.py
```

### Step 5: Add Sources

Use the API or frontend to add:
1. Angular Blog (RSS)
2. Angular GitHub Releases
3. Angular Medium Tag
4. r/Angular2 Subreddit
5. Dev.to Angular Tag

---

## Content Coverage Comparison

### X API ($200/month)
- ✅ Real-time updates
- ✅ Direct from developers
- ✅ High frequency
- ❌ Very expensive
- ❌ Rate limits

### Free Alternatives ($0/month)
- ✅ Official announcements (RSS)
- ✅ Repository updates (GitHub)
- ✅ Community discussions (Reddit)
- ✅ Articles and tutorials (Medium, Dev.to)
- ✅ Video content (YouTube)
- ✅ No cost
- ⚠️ Slightly delayed (not real-time)

**Verdict:** Free alternatives provide 90% of the value at 0% of the cost.

---

## Recommended Sources for Angular

### Essential (Free)

1. **Angular Blog** (RSS)
   - Official announcements
   - Release notes
   - Best practices

2. **Angular GitHub** (GitHub)
   - Version releases
   - Changelogs
   - Issue tracking

3. **r/Angular2** (Reddit)
   - Community discussions
   - Q&A
   - Tutorials

### Additional (Free)

4. **Angular on Medium** (RSS)
   - Community articles
   - Tutorials
   - Case studies

5. **Dev.to Angular** (RSS)
   - Developer tutorials
   - Tips and tricks
   - Project showcases

6. **Angular YouTube** (YouTube)
   - Conference talks
   - Video tutorials
   - Live streams

---

## Cost Savings

### X API Costs
- Basic tier: $200/month
- Annual: $2,400/year

### Free Alternatives
- GitHub: $0/month
- Reddit: $0/month
- RSS: $0/month
- YouTube: $0/month
- **Total: $0/month**

**Annual Savings: $2,400** 💰

---

## Rate Limits Summary

| Source | Rate Limit | Sufficient For |
|--------|------------|----------------|
| **GitHub** | 5,000 req/hour | ✅ Yes, very generous |
| **Reddit** | 60 req/minute | ✅ Yes, adequate |
| **RSS** | Unlimited | ✅ Yes, no limits |
| **YouTube** | 10,000 units/day | ✅ Yes, plenty |
| **Medium** | Unlimited | ✅ Yes, no limits |

All free alternatives have sufficient rate limits for typical use cases.

---

## Testing Your Setup

### Test GitHub
```bash
cd backend
python -c "
from github import Github
import os
from dotenv import load_dotenv
load_dotenv()
g = Github(os.getenv('GITHUB_TOKEN'))
print(f'✅ GitHub: {g.get_rate_limit().core.remaining} requests remaining')
"
```

### Test Reddit
```bash
python -c "
import praw
import os
from dotenv import load_dotenv
load_dotenv()
r = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='CreatorPulse/1.0'
)
r.read_only = True
print(f'✅ Reddit: Connected (read-only: {r.read_only})')
"
```

---

## Troubleshooting

### GitHub Issues

**401 Unauthorized:**
- Regenerate token at https://github.com/settings/tokens
- Update `GITHUB_TOKEN` in `.env`
- Restart backend

**404 Not Found:**
- Verify repository format: `owner/repo`
- Check repository exists on GitHub

### Reddit Issues

**401 Unauthorized:**
- Verify credentials in `.env`
- Ensure app type is "script"
- Restart backend

**403 Forbidden:**
- Check if subreddit is public
- Verify subreddit name (without r/)

---

## Summary

### ✅ What You Get (Free)

- **Official Updates:** Angular blog, GitHub releases
- **Community Content:** Reddit discussions, Medium articles
- **Video Content:** YouTube tutorials and talks
- **Developer Content:** Dev.to tutorials, Hashnode articles
- **No Cost:** $0/month vs $200/month for X API
- **Better Coverage:** Multiple sources vs single X account

### 🚀 Quick Start

1. **Install:** `pip install PyGithub praw`
2. **Setup GitHub:** Get token from https://github.com/settings/tokens
3. **Setup Reddit:** Create app at https://www.reddit.com/prefs/apps
4. **Add to `.env`:** GitHub token + Reddit credentials
5. **Restart backend**
6. **Add sources:** Angular blog, GitHub, Reddit, Medium

### 💰 Cost Comparison

- **X API:** $200/month ($2,400/year)
- **Free Alternatives:** $0/month ($0/year)
- **Savings:** $2,400/year

### 📚 Documentation

- **GitHub Setup:** [GITHUB_SETUP.md](./GITHUB_SETUP.md)
- **Reddit Setup:** [REDDIT_SETUP.md](./REDDIT_SETUP.md)
- **X API Integration:** [X_API_INTEGRATION.md](./X_API_INTEGRATION.md)

---

**Recommendation:** Use the free alternatives. They provide excellent coverage of Angular updates at zero cost. Only consider X API if you absolutely need real-time tweets from specific developers.
