# Draft Generation Troubleshooting Guide

## Problem Summary

Draft generation is returning a fallback template with:
- ❌ No actual content (only intro and conclusion)
- ❌ Voice profile not used (`voice_profile_used: false`)
- ❌ No trends detected (`no_trends: true`, `fallback: true`)
- ❌ Topic count is 0

## Root Cause

The draft generator couldn't find any trends because there's **no content in the `source_content_cache` table**.

### Why No Content?

From your crawl response, all sources show `"items_new": 0`, which means:
1. ✅ Sources were crawled successfully
2. ❌ But no new content was stored
3. **Reason**: Content likely already exists in the database from previous crawls

The RSS crawler checks for existing content before inserting:
```python
# Check if content already exists
existing = self.supabase.table("source_content_cache").select("id").eq(
    "source_id", source_id
).eq("url", entry.link).execute()

if existing.data:
    continue  # Skip existing content
```

## Diagnostic Steps

### Step 1: Check Content Status

Use the new debug endpoint:

```bash
GET http://localhost:8000/api/drafts/debug/content-status
Authorization: Bearer YOUR_TOKEN
```

**Expected Response:**
```json
{
  "sources": {
    "total": 7,
    "active": 7,
    "by_type": {
      "rss": 4,
      "youtube": 1,
      "reddit": 1,
      "github": 1
    }
  },
  "content_items": 0,  // ← This should be > 0
  "trends_detected": 0,
  "voice_samples": 0,
  "can_generate_draft": false
}
```

### Step 2: Check Database Directly

Run in Supabase SQL Editor:

```sql
-- Check content for your sources
SELECT 
    s.name,
    s.source_type,
    COUNT(scc.id) as content_count,
    MAX(scc.created_at) as latest_content
FROM sources s
LEFT JOIN source_content_cache scc ON s.id = scc.source_id
WHERE s.user_id = 'd2f68956-7190-451c-a2a5-44f35d58d414'
GROUP BY s.id, s.name, s.source_type;
```

## Solutions

### Solution 1: Clear Old Content and Re-Crawl (Recommended)

```sql
-- Delete existing content to force fresh crawl
DELETE FROM source_content_cache
WHERE source_id IN (
    SELECT id FROM sources 
    WHERE user_id = 'd2f68956-7190-451c-a2a5-44f35d58d414'
);
```

Then trigger a new crawl:
```bash
POST http://localhost:8000/api/crawl/trigger
Authorization: Bearer YOUR_TOKEN
```

### Solution 2: Lower Trend Detection Threshold

If content exists but trends aren't detected, lower the minimum score.

**File**: `backend/app/services/draft_generator.py` (line 60-65)

```python
# Change from:
trends = await trend_detector.detect_trends(
    user_id=user_id,
    days_back=days_back,
    min_score=0.3,  # Too high?
    max_trends=topic_count
)

# To:
trends = await trend_detector.detect_trends(
    user_id=user_id,
    days_back=days_back,
    min_score=0.1,  # Lower threshold
    max_trends=topic_count
)
```

### Solution 3: Manually Trigger Trend Detection

```bash
POST http://localhost:8000/api/trends/detect
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "days_back": 7,
  "min_score": 0.2,
  "max_trends": 10
}
```

### Solution 4: Add Voice Profile

The voice profile requires uploaded newsletter samples:

```bash
POST http://localhost:8000/api/voice/upload
Authorization: Bearer YOUR_TOKEN
Content-Type: multipart/form-data

# Upload a sample newsletter file
```

## Testing Workflow

### 1. Check Current State
```bash
# Check content status
curl http://localhost:8000/api/drafts/debug/content-status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Clear and Re-Crawl
```sql
-- In Supabase SQL Editor
DELETE FROM source_content_cache
WHERE source_id IN (
    SELECT id FROM sources 
    WHERE user_id = 'YOUR_USER_ID'
);
```

```bash
# Trigger crawl
curl -X POST http://localhost:8000/api/crawl/trigger \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Verify Content Was Stored
```bash
# Check content status again
curl http://localhost:8000/api/drafts/debug/content-status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should now show content_items > 0
```

### 4. Detect Trends
```bash
curl -X POST http://localhost:8000/api/trends/detect \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days_back": 7, "min_score": 0.2}'
```

### 5. Generate Draft
```bash
curl -X POST http://localhost:8000/api/drafts/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_count": 5,
    "days_back": 7,
    "use_voice_profile": false,
    "force_regenerate": true
  }'
```

## Expected Successful Response

```json
{
  "draft_id": "...",
  "status": "ready",
  "message": "Draft generated successfully",
  "draft": {
    "title": "AI Trends This Week - October 16, 2025",
    "sections": [
      {
        "id": "intro",
        "type": "intro",
        "content": "Welcome to this week's newsletter..."
      },
      {
        "id": "topic-1",
        "type": "topic",
        "title": "GPT-5 Release Announcement",
        "content": "OpenAI announced the release of GPT-5..."
      },
      {
        "id": "topic-2",
        "type": "topic",
        "title": "New AI Regulations in EU",
        "content": "The European Union has passed..."
      }
      // ... more topics
    ],
    "metadata": {
      "fallback": false,  // ← Should be false
      "no_trends": false,  // ← Should be false
      "voice_profile_used": false,  // true if samples uploaded
      "topic_count": 5,  // ← Should match request
      "trends_used": ["GPT-5", "AI Regulations", ...],
      "model_used": "openai/gpt-oss-20b"
    }
  }
}
```

## Common Issues & Fixes

### Issue 1: `content_items: 0`
**Cause**: No content in database  
**Fix**: Clear old content and re-crawl (Solution 1)

### Issue 2: `trends_detected: 0` but `content_items > 0`
**Cause**: Trend detection threshold too high or Groq API issue  
**Fix**: Lower `min_score` to 0.1-0.2 (Solution 2)

### Issue 3: `voice_profile_used: false`
**Cause**: No newsletter samples uploaded  
**Fix**: Upload samples via `/api/voice/upload` (Solution 4)

### Issue 4: Crawl shows `items_new: 0`
**Cause**: Content already exists (duplicate check)  
**Fix**: Delete old content first (Solution 1)

### Issue 5: Fallback draft generated
**Cause**: No trends detected  
**Fix**: Follow Solutions 1-3 in order

## Files Modified

1. **`backend/app/api/routes/drafts.py`**
   - Added `/debug/content-status` endpoint
   - Helps diagnose content availability issues

## Quick Fix Commands

```bash
# 1. Check status
curl http://localhost:8000/api/drafts/debug/content-status \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. If content_items is 0, clear and re-crawl
# (Run SQL DELETE in Supabase first)

# 3. Trigger crawl
curl -X POST http://localhost:8000/api/crawl/trigger \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Wait 30 seconds, then detect trends
curl -X POST http://localhost:8000/api/trends/detect \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days_back": 7, "min_score": 0.2}'

# 5. Generate draft
curl -X POST http://localhost:8000/api/drafts/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic_count": 5, "days_back": 7, "use_voice_profile": false, "force_regenerate": true}'
```

## Next Steps

1. ✅ Use the debug endpoint to check current state
2. ✅ Clear old content if needed
3. ✅ Re-crawl sources
4. ✅ Verify content was stored
5. ✅ Detect trends
6. ✅ Generate draft

---

**Status**: Diagnostic tools added  
**Action Required**: Run debug endpoint and follow solutions based on results
