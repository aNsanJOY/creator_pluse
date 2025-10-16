# Draft Generation Debug Guide

## Issue
Draft generation is returning a fallback template with no content because:
1. No trends are being detected
2. Voice profile is not being used
3. Content appears empty

## Root Cause Analysis

### 1. No Content in Database
The response shows `"items_new": 0` for all sources, meaning:
- RSS feeds were crawled successfully
- But no new content was stored (likely already exists)
- Trend detector needs content in `source_content_cache` table

### 2. Check if Content Exists

Run this query in Supabase SQL Editor:
```sql
-- Check if content exists for your sources
SELECT 
    s.name as source_name,
    s.source_type,
    COUNT(scc.id) as content_count,
    MAX(scc.created_at) as latest_content
FROM sources s
LEFT JOIN source_content_cache scc ON s.id = scc.source_id
WHERE s.user_id = 'd2f68956-7190-451c-a2a5-44f35d58d414'
GROUP BY s.id, s.name, s.source_type
ORDER BY content_count DESC;
```

### 3. Check Trends Detection

```sql
-- Check if trends exist
SELECT * FROM trends 
WHERE user_id = 'd2f68956-7190-451c-a2a5-44f35d58d414'
ORDER BY detected_at DESC
LIMIT 10;
```

## Solutions

### Solution 1: Force Fresh Crawl (Delete Existing Content)

If content exists but is old, delete it to force a fresh crawl:

```sql
-- Delete old content for your sources
DELETE FROM source_content_cache
WHERE source_id IN (
    SELECT id FROM sources 
    WHERE user_id = 'd2f68956-7190-451c-a2a5-44f35d58d414'
);
```

Then trigger a new crawl:
```bash
POST http://localhost:8000/api/crawl/trigger
```

### Solution 2: Manually Trigger Trend Detection

If content exists but trends aren't detected:

```bash
POST http://localhost:8000/api/trends/detect
Content-Type: application/json

{
  "days_back": 7,
  "min_score": 0.3,
  "max_trends": 10
}
```

### Solution 3: Lower Trend Detection Threshold

The draft generator uses `min_score=0.3` but trend detector might need lower threshold:

**File**: `backend/app/services/draft_generator.py` line 63

Change:
```python
trends = await trend_detector.detect_trends(
    user_id=user_id,
    days_back=days_back,
    min_score=0.3,  # Try 0.1 or 0.2
    max_trends=topic_count
)
```

### Solution 4: Check Voice Profile

```sql
-- Check if voice profile exists
SELECT * FROM newsletter_samples
WHERE user_id = 'd2f68956-7190-451c-a2a5-44f35d58d414';
```

If no samples exist, the voice profile can't be used. Upload sample newsletters first.

## Testing Steps

### Step 1: Verify Content Exists
```bash
# Check content count
curl http://localhost:8000/api/sources \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 2: Check Crawl Logs
```bash
# View recent crawl logs
curl "http://localhost:8000/api/crawl/logs?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 3: Manually Detect Trends
```bash
POST http://localhost:8000/api/trends/detect
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "days_back": 7,
  "min_score": 0.2
}
```

### Step 4: Generate Draft Again
```bash
POST http://localhost:8000/api/drafts/generate
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "topic_count": 5,
  "days_back": 7,
  "use_voice_profile": true
}
```

## Expected Behavior

### Successful Draft Generation
```json
{
  "draft_id": "...",
  "status": "ready",
  "draft": {
    "title": "AI Trends Weekly - October 16, 2025",
    "sections": [
      {
        "id": "intro",
        "type": "intro",
        "content": "Here are this week's top AI trends..."
      },
      {
        "id": "topic-1",
        "type": "topic",
        "title": "GPT-5 Release Announcement",
        "content": "OpenAI announced..."
      },
      // ... more topics
    ],
    "metadata": {
      "fallback": false,
      "voice_profile_used": true,
      "topic_count": 5,
      "trends_used": ["GPT-5", "AI Regulation", ...]
    }
  }
}
```

## Common Issues

### Issue 1: "No content found"
**Cause**: `source_content_cache` table is empty
**Fix**: Run a fresh crawl or check if sources are active

### Issue 2: "No trends detected"
**Cause**: Content exists but Groq API failed to extract topics
**Fix**: Check Groq API key, check logs for errors

### Issue 3: "Voice profile not used"
**Cause**: No newsletter samples uploaded
**Fix**: Upload sample newsletters via `/api/voice/upload`

### Issue 4: Fallback draft generated
**Cause**: Trend detection returned empty
**Fix**: Lower `min_score` threshold or add more content

## Quick Fix Script

Create a test script to populate content:

```python
# test_populate_content.py
import requests

BASE_URL = "http://localhost:8000"
TOKEN = "your_token_here"

headers = {"Authorization": f"Bearer {TOKEN}"}

# 1. Trigger crawl
response = requests.post(f"{BASE_URL}/api/crawl/trigger", headers=headers)
print("Crawl:", response.json())

# 2. Detect trends
response = requests.post(
    f"{BASE_URL}/api/trends/detect",
    headers=headers,
    json={"days_back": 7, "min_score": 0.2}
)
print("Trends:", response.json())

# 3. Generate draft
response = requests.post(
    f"{BASE_URL}/api/drafts/generate",
    headers=headers,
    json={"topic_count": 5, "days_back": 7, "use_voice_profile": False}
)
print("Draft:", response.json())
```

## Next Steps

1. Run the SQL queries to check content and trends
2. If no content: Delete old content and re-crawl
3. If content exists but no trends: Lower threshold or check Groq API
4. If trends exist: Check draft generation logs for errors
5. Upload newsletter samples for voice profile

---

**Status**: Debugging required
**Priority**: High - Core feature not working
