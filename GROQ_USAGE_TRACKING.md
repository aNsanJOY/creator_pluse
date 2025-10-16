# Groq API Usage Tracking

## Overview
Simplified tracking system focused **only on Groq API calls**. No tracking for sources (Twitter, YouTube, RSS, etc.).

## What's Tracked

### ✅ Groq API Calls Only
- Model used (llama-3.1-70b-versatile, etc.)
- Tokens consumed (total, prompt, completion)
- Request duration
- Success/error status
- Rate limit enforcement

### ❌ Not Tracked
- Twitter API calls
- YouTube API calls
- RSS fetches
- Other source crawls

## Database Schema

### `groq_usage_logs`
Logs every Groq API call:
```sql
- user_id
- endpoint (/v1/chat/completions)
- model (llama-3.1-70b-versatile, etc.)
- status_code
- tokens_used (total)
- prompt_tokens (input)
- completion_tokens (output)
- duration_ms
- error_message
- metadata (JSONB - temperature, max_tokens, etc.)
- created_at
```

### `groq_rate_limit_configs`
Global default rate limits:
```sql
- limit_type (minute, day)
- limit_value (30, 14400)
- description
```

**Defaults:**
- Per Minute: 30 requests
- Per Day: 14,400 requests

### `groq_rate_limits`
User-specific rate limits (can override defaults):
```sql
- user_id
- limit_type
- limit_value
- current_count
- reset_at
```

### `groq_usage_daily_summary`
Materialized view for fast analytics:
```sql
- user_id
- model
- usage_date
- total_calls
- total_tokens
- total_prompt_tokens
- total_completion_tokens
- avg_duration_ms
- error_count
```

## API Endpoints

All endpoints are under `/api/groq/usage`

### Check Groq Balance
```bash
GET /api/groq/usage/rate-limit/day

Response:
{
  "success": true,
  "can_call": true,
  "current_count": 1250,
  "limit_value": 14400,
  "remaining": 13150,
  "reset_at": "2025-10-17T00:00:00Z"
}
```

### Get Usage Summary
```bash
GET /api/groq/usage/summary

Response:
{
  "success": true,
  "summary": {
    "today": {
      "calls": 45,
      "tokens": 18000,
      "prompt_tokens": 12000,
      "completion_tokens": 6000
    },
    "this_month": {
      "calls": 1250,
      "tokens": 450000,
      "prompt_tokens": 300000,
      "completion_tokens": 150000
    },
    "rate_limits": {
      "per_minute": {
        "can_call": true,
        "current_count": 12,
        "remaining": 18
      },
      "per_day": {
        "can_call": true,
        "current_count": 1250,
        "remaining": 13150
      }
    }
  }
}
```

### Get Detailed Stats
```bash
GET /api/groq/usage/stats?days=30

Response:
{
  "success": true,
  "stats": {
    "total_calls": 1250,
    "total_tokens": 450000,
    "total_prompt_tokens": 300000,
    "total_completion_tokens": 150000,
    "by_model": {
      "llama-3.1-70b-versatile": {
        "calls": 800,
        "tokens": 350000,
        "prompt_tokens": 230000,
        "completion_tokens": 120000
      },
      "llama-3.1-8b-instant": {
        "calls": 450,
        "tokens": 100000,
        "prompt_tokens": 70000,
        "completion_tokens": 30000
      }
    },
    "by_day": [
      {
        "date": "2025-10-15",
        "calls": 45,
        "tokens": 18000,
        "prompt_tokens": 12000,
        "completion_tokens": 6000
      }
    ]
  }
}
```

### Get All Rate Limits
```bash
GET /api/groq/usage/rate-limits

Response:
{
  "success": true,
  "rate_limits": [
    {
      "limit_type": "minute",
      "current_count": 12,
      "limit_value": 30,
      "remaining": 18,
      "reset_at": "2025-10-16T14:05:00Z",
      "percentage_used": 40.0
    },
    {
      "limit_type": "day",
      "current_count": 1250,
      "limit_value": 14400,
      "remaining": 13150,
      "reset_at": "2025-10-17T00:00:00Z",
      "percentage_used": 8.68
    }
  ]
}
```

### Get Usage Logs
```bash
GET /api/groq/usage/logs?limit=50&offset=0

Response:
{
  "success": true,
  "logs": [
    {
      "id": "uuid",
      "model": "llama-3.1-70b-versatile",
      "endpoint": "/v1/chat/completions",
      "status_code": 200,
      "tokens_used": 450,
      "prompt_tokens": 300,
      "completion_tokens": 150,
      "duration_ms": 1250,
      "metadata": {
        "temperature": 0.7,
        "max_tokens": 500
      },
      "created_at": "2025-10-16T13:45:23Z"
    }
  ],
  "total": 1250,
  "limit": 50,
  "offset": 0
}
```

## Usage in Code

### Log Groq API Call

```python
from app.services.groq_usage_tracker import groq_usage_tracker

# After calling Groq API
response = groq_client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[...]
)

# Log the call
await groq_usage_tracker.log_groq_call(
    user_id=user_id,
    model="llama-3.1-70b-versatile",
    endpoint="/v1/chat/completions",
    status_code=200,
    tokens_used=response.usage.total_tokens,
    prompt_tokens=response.usage.prompt_tokens,
    completion_tokens=response.usage.completion_tokens,
    duration_ms=1250,
    metadata={
        "temperature": 0.7,
        "max_tokens": 500
    }
)
```

### Check Rate Limit Before Call

```python
from app.services.groq_usage_tracker import groq_usage_tracker
from fastapi import HTTPException

# Before making Groq API call
limit_info = await groq_usage_tracker.check_rate_limit(
    user_id=user_id,
    limit_type="minute"
)

if not limit_info["can_call"]:
    raise HTTPException(
        status_code=429,
        detail=f"Groq rate limit exceeded. Resets at {limit_info['reset_at']}"
    )

# Make Groq API call...
```

## Rate Limit Configuration

### Update Global Default
```sql
UPDATE groq_rate_limit_configs 
SET limit_value = 100 
WHERE limit_type = 'minute';
```

### Override for Specific User
```sql
-- Check if user limit exists
SELECT * FROM groq_rate_limits 
WHERE user_id = 'user-uuid' AND limit_type = 'minute';

-- Create or update
INSERT INTO groq_rate_limits (user_id, limit_type, limit_value, reset_at)
VALUES ('user-uuid', 'minute', 100, NOW() + INTERVAL '1 minute')
ON CONFLICT (user_id, limit_type) 
DO UPDATE SET limit_value = 100;
```

## Migration Steps

1. **Run Database Migration:**
   ```bash
   psql -h host -U postgres -d postgres \
     -f backend/database_migrations/005_api_usage_tracking.sql
   ```

2. **Verify Tables:**
   ```sql
   \dt groq_usage_logs
   \dt groq_rate_limit_configs
   \dt groq_rate_limits
   ```

3. **Check Default Configs:**
   ```sql
   SELECT * FROM groq_rate_limit_configs;
   -- Should show: minute=30, day=14400
   ```

4. **Test Endpoints:**
   - Visit http://localhost:8000/docs
   - Test `/api/groq/usage/summary`
   - Verify rate limits returned

5. **Integrate Logging:**
   - Add `groq_usage_tracker.log_groq_call()` after Groq API calls
   - Test with a few API calls
   - Verify logs appear in database

## Integration Example

### In Newsletter Generator Service

```python
from app.services.groq_usage_tracker import groq_usage_tracker
import time

async def generate_newsletter(user_id: str, content: str):
    # Check rate limit
    limit_info = await groq_usage_tracker.check_rate_limit(user_id, "minute")
    if not limit_info["can_call"]:
        raise HTTPException(429, "Rate limit exceeded")
    
    # Make Groq API call
    start_time = time.time()
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": content}],
            temperature=0.7
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log successful call
        await groq_usage_tracker.log_groq_call(
            user_id=user_id,
            model="llama-3.1-70b-versatile",
            status_code=200,
            tokens_used=response.usage.total_tokens,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            duration_ms=duration_ms,
            metadata={"temperature": 0.7}
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log failed call
        await groq_usage_tracker.log_groq_call(
            user_id=user_id,
            model="llama-3.1-70b-versatile",
            status_code=500,
            duration_ms=duration_ms,
            error_message=str(e)
        )
        raise
```

## Benefits

### ✅ Focused Tracking
- Only tracks what matters: Groq API usage
- No unnecessary data for source crawls
- Simpler database schema

### ✅ Detailed Token Tracking
- Separate prompt and completion tokens
- Track by model
- Understand usage patterns

### ✅ Flexible Rate Limits
- Global defaults for all users
- Per-user overrides for premium tiers
- Auto-resets when time window expires

### ✅ Easy Monitoring
- Quick summary endpoint
- Detailed stats by model and day
- Real-time rate limit status

## Maintenance

### Refresh Materialized View
Run daily via cron:
```sql
SELECT refresh_groq_usage_summary();
```

### Clean Old Logs
Archive logs older than 90 days:
```sql
DELETE FROM groq_usage_logs 
WHERE created_at < NOW() - INTERVAL '90 days';
```

### Monitor Usage
```sql
-- Top users by token usage (last 30 days)
SELECT 
    user_id,
    COUNT(*) as calls,
    SUM(tokens_used) as total_tokens
FROM groq_usage_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY user_id
ORDER BY total_tokens DESC
LIMIT 10;

-- Most used models
SELECT 
    model,
    COUNT(*) as calls,
    AVG(tokens_used) as avg_tokens
FROM groq_usage_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY model
ORDER BY calls DESC;
```

## Summary

✅ **Groq-only tracking** - No source crawl tracking  
✅ **Detailed token metrics** - Prompt + completion tokens  
✅ **Flexible rate limits** - Configurable per user  
✅ **Simple API** - Easy to integrate  
✅ **No cost estimation** - Just real usage data  

The system provides accurate Groq API usage tracking with rate limiting, focused only on what matters for LLM usage monitoring.
