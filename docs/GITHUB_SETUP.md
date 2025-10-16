# GitHub API Setup Guide

## Overview

The GitHub connector allows you to fetch updates from GitHub repositories including releases, commits, issues, pull requests, and discussions. GitHub API is **completely free** with generous rate limits.

---

## Rate Limits

| Authentication | Requests per Hour | Cost |
|----------------|-------------------|------|
| **Unauthenticated** | 60 | Free |
| **Authenticated** | 5,000 | Free |

**Recommendation:** Use authentication (Personal Access Token) for 5,000 requests/hour.

---

## Setup Instructions

### Step 1: Create a GitHub Personal Access Token

1. **Go to GitHub Settings**
   - Visit: https://github.com/settings/tokens
   - Or: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Generate New Token**
   - Click "Generate new token (classic)"
   - Give it a descriptive name: "CreatorPulse API Access"

3. **Select Scopes**
   - For public repositories only: **No scopes needed** (leave all unchecked)
   - For private repositories: Check `repo` scope
   - For reading discussions: Check `read:discussion`

4. **Generate and Copy Token**
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again)
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: Add Token to `.env`

Open `backend/.env` and add:

```env
# GitHub API (Optional - Free with 5,000 requests/hour)
GITHUB_TOKEN=ghp_your_actual_token_here
```

### Step 3: Restart Backend

```bash
cd backend
python app/main.py
```

---

## Using the GitHub Connector

### Configuration Options

When adding a GitHub source, you need to configure:

```json
{
  "source_type": "github",
  "name": "Angular Repository",
  "config": {
    "repository": "angular/angular",
    "fetch_type": "releases",
    "max_results": 10
  }
}
```

### Configuration Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `repository` | string | Yes | Repository in `owner/repo` format | `"angular/angular"` |
| `fetch_type` | string | Yes | Type of content to fetch | `"releases"` |
| `max_results` | integer | No | Max items to fetch (default: 10, max: 100) | `20` |

### Supported Fetch Types

#### 1. **releases** - Repository Releases

Fetches official releases and tags.

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

**What you get:**
- Release title and tag name
- Release notes/changelog
- Release date
- Author
- Pre-release flag
- Asset count

#### 2. **commits** - Recent Commits

Fetches recent commits to the default branch.

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "github",
    "name": "Angular Commits",
    "config": {
      "repository": "angular/angular",
      "fetch_type": "commits",
      "max_results": 20
    }
  }'
```

**What you get:**
- Commit message
- Commit SHA
- Author name and email
- Commit date
- Code changes (additions/deletions)

#### 3. **issues** - Repository Issues

Fetches issues (excludes pull requests).

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "github",
    "name": "Angular Issues",
    "config": {
      "repository": "angular/angular",
      "fetch_type": "issues",
      "max_results": 15
    }
  }'
```

**What you get:**
- Issue title and number
- Issue description
- State (open/closed)
- Labels
- Comment count
- Author

#### 4. **pull_requests** - Pull Requests

Fetches pull requests.

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "github",
    "name": "Angular PRs",
    "config": {
      "repository": "angular/angular",
      "fetch_type": "pull_requests",
      "max_results": 10
    }
  }'
```

**What you get:**
- PR title and number
- PR description
- State (open/closed/merged)
- Merged status
- Labels
- Code changes
- Commit count

#### 5. **discussions** - Repository Discussions

Fetches GitHub Discussions (if enabled on the repository).

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "github",
    "name": "Angular Discussions",
    "config": {
      "repository": "angular/angular",
      "fetch_type": "discussions",
      "max_results": 10
    }
  }'
```

**Note:** Discussions require GraphQL API (not yet fully implemented).

---

## Popular Angular Repositories to Follow

### Official Angular Repositories

```bash
# Angular Framework
{
  "repository": "angular/angular",
  "fetch_type": "releases"
}

# Angular CLI
{
  "repository": "angular/angular-cli",
  "fetch_type": "releases"
}

# Angular Material
{
  "repository": "angular/components",
  "fetch_type": "releases"
}
```

### Community Projects

```bash
# NgRx (State Management)
{
  "repository": "ngrx/platform",
  "fetch_type": "releases"
}

# RxJS
{
  "repository": "ReactiveX/rxjs",
  "fetch_type": "releases"
}

# Nx (Monorepo Tools)
{
  "repository": "nrwl/nx",
  "fetch_type": "releases"
}

# AnalogJS (Meta-framework)
{
  "repository": "analogjs/analog",
  "fetch_type": "releases"
}
```

---

## Delta Crawling

The GitHub connector supports delta crawling to only fetch new content:

- **First crawl:** Fetches content from last 30 days
- **Subsequent crawls:** Only fetches content since last crawl
- **Efficient:** Reduces API calls and stays within rate limits

---

## Rate Limit Handling

The connector automatically handles rate limits:

1. **Detects rate limit exceeded**
2. **Calculates wait time** until reset
3. **Waits automatically** before retrying
4. **Logs rate limit info** for monitoring

### Check Your Rate Limit

```python
# In Python
from github import Github

g = Github("your_token")
rate_limit = g.get_rate_limit()
print(f"Remaining: {rate_limit.core.remaining}/{rate_limit.core.limit}")
print(f"Resets at: {rate_limit.core.reset}")
```

---

## Troubleshooting

### Common Issues

#### 1. **401 Unauthorized**

**Cause:** Invalid or expired token

**Solution:**
- Regenerate token at https://github.com/settings/tokens
- Update `GITHUB_TOKEN` in `.env`
- Restart backend

#### 2. **404 Not Found**

**Cause:** Repository doesn't exist or is private

**Solution:**
- Verify repository name format: `owner/repo`
- For private repos, ensure token has `repo` scope
- Check repository exists on GitHub

#### 3. **403 Forbidden**

**Cause:** Rate limit exceeded or insufficient permissions

**Solution:**
- Wait for rate limit to reset (check reset time)
- Use authentication token for higher limits
- Reduce `max_results` value

#### 4. **PyGithub Not Installed**

**Cause:** Missing dependency

**Solution:**
```bash
pip install PyGithub==2.1.1
```

---

## Testing

### Test GitHub Connection

Create `test_github.py`:

```python
from github import Github
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('GITHUB_TOKEN')

try:
    g = Github(token) if token else Github()
    
    # Test connection
    rate_limit = g.get_rate_limit()
    print(f"✅ Connected! Rate limit: {rate_limit.core.remaining}/{rate_limit.core.limit}")
    
    # Test repository access
    repo = g.get_repo("angular/angular")
    print(f"✅ Repository found: {repo.full_name}")
    print(f"   Stars: {repo.stargazers_count}")
    print(f"   Description: {repo.description}")
    
except Exception as e:
    print(f"❌ Error: {e}")
```

Run:
```bash
cd backend
python test_github.py
```

---

## Best Practices

### 1. **Use Authentication**
- ✅ Always use a Personal Access Token
- ✅ Gets you 5,000 requests/hour (vs 60 unauthenticated)
- ✅ Access to private repositories (if needed)

### 2. **Choose the Right Fetch Type**
- **Releases:** For version updates and changelogs
- **Commits:** For detailed development activity
- **Issues:** For bug reports and feature requests
- **Pull Requests:** For code contributions

### 3. **Set Appropriate max_results**
- **Releases:** 5-10 (releases are infrequent)
- **Commits:** 20-50 (commits are frequent)
- **Issues:** 10-20 (moderate frequency)
- **Pull Requests:** 10-15 (moderate frequency)

### 4. **Monitor Rate Limits**
- Check rate limit in logs
- Set up alerts if approaching limit
- Use delta crawling to reduce API calls

### 5. **Security**
- ✅ Store token in `.env` file
- ✅ Never commit token to git
- ✅ Use minimal scopes needed
- ✅ Rotate tokens periodically

---

## API Reference

### GitHub API Documentation

- **Official Docs:** https://docs.github.com/en/rest
- **PyGithub Docs:** https://pygithub.readthedocs.io/
- **Rate Limits:** https://docs.github.com/en/rest/rate-limit
- **Personal Access Tokens:** https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

---

## Summary

### Key Features

✅ **Completely Free** - No cost, 5,000 requests/hour with token  
✅ **Multiple Content Types** - Releases, commits, issues, PRs  
✅ **Delta Crawling** - Only fetch new content  
✅ **Rate Limit Handling** - Automatic retry with backoff  
✅ **Rich Metadata** - Detailed information for each item  

### Quick Start

1. Create Personal Access Token at https://github.com/settings/tokens
2. Add to `.env`: `GITHUB_TOKEN=your_token`
3. Restart backend
4. Add GitHub source with repository and fetch_type
5. Start crawling!

---

**Cost:** Free  
**Rate Limit:** 5,000 requests/hour (authenticated)  
**Best For:** Repository updates, releases, development activity  
**Setup Time:** 2 minutes
