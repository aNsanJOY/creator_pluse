# API Usage Tracking - Summary

## ✅ Changes Made Based on Feedback

### 1. **Rate Limits are Now Configurable (Not Hardcoded)**

**Before:** Rate limits were hardcoded per user in the migration
**After:** Two-tier system with flexibility

#### New Structure:

**`service_rate_limit_configs` Table** (Global Defaults)
- Stores default rate limits per service
- Admins can update these defaults
- Example: Groq default = 30/minute, 14,400/day

**`api_rate_limits` Table** (User-Specific Overrides)
- Created dynamically when user first accesses a service
- Can override defaults for specific users
- Example: Premium user gets 100/minute instead of 30/minute

#### How to Update Rate Limits:

**Update Global Default:**
```sql
UPDATE service_rate_limit_configs 
SET limit_value = 100 
WHERE service_name = 'groq' AND limit_type = 'minute';
```

**Override for Specific User:**
```sql
INSERT INTO api_rate_limits (user_id, service_name, limit_type, limit_value, reset_at)
VALUES ('user-uuid', 'groq', 'minute', 100, NOW() + INTERVAL '1 minute')
ON CONFLICT (user_id, service_name, limit_type) 
DO UPDATE SET limit_value = 100;
```

**Via API (Future Enhancement):**
```bash
POST /api/admin/rate-limits
{
  "user_id": "uuid",
  "service_name": "groq",
  "limit_type": "minute",
  "limit_value": 100
}
```

### 2. **Cost Estimation Removed**

**Removed:**
- ❌ `cost_usd` column from `api_usage_logs`
- ❌ Cost calculation logic in `api_usage_tracker.py`
- ❌ Cost pricing dictionary
- ❌ Cost totals from API responses

**Why:** Cost estimation without real billing data is inaccurate and misleading.

**What's Tracked Instead:**
- ✅ Number of API calls
- ✅ Tokens used (for LLM services)
- ✅ Request duration
- ✅ Success/error rates

**If You Need Cost Tracking:**
- Integrate with actual billing APIs (Groq, OpenAI, etc.)
- Use their official usage/billing endpoints
- Store real costs from invoices

## Current System Overview

### Database Tables

#### 1. `api_usage_logs`
Logs every API call:
```sql
- user_id
- service_name (groq, twitter, youtube, etc.)
- endpoint
- method
- status_code
- tokens_used
- duration_ms
- error_message
- metadata (JSONB)
- created_at
```

#### 2. `service_rate_limit_configs`
Global default rate limits:
```sql
- service_name
- limit_type (minute, hour, day, month)
- limit_value
- description
```

**Default Values:**
- Groq: 30/minute, 14,400/day
- Twitter: 1,500/month
- YouTube: 10,000/day

#### 3. `api_rate_limits`
User-specific rate limits:
```sql
- user_id
- service_name
- limit_type
- limit_value (can override default)
- current_count
- reset_at
```

#### 4. `api_usage_daily_summary` (Materialized View)
Pre-aggregated daily stats for fast queries

### API Endpoints

#### Check Groq Balance
```bash
GET /api/usage/rate-limits/groq?limit_type=day

Response:
{
  "can_call": true,
  "current_count": 1250,
  "limit_value": 14400,
  "remaining": 13150,
  "reset_at": "2025-10-17T00:00:00Z"
}
```

#### Get Usage Stats
```bash
GET /api/usage/stats?days=30

Response:
{
  "stats": {
    "total_calls": 1250,
    "total_tokens": 450000,
    "by_service": {
      "groq": {
        "calls": 1000,
        "tokens": 400000
      }
    },
    "by_day": [...]
  }
}
```

#### Quick Summary
```bash
GET /api/usage/summary

Response:
{
  "summary": {
    "today": {
      "calls": 45,
      "tokens": 18000
    },
    "this_month": {
      "calls": 1250,
      "tokens": 450000
    },
    "groq_limits": {
      "per_minute": {
        "current_count": 12,
        "remaining": 18
      },
      "per_day": {
        "current_count": 1250,
        "remaining": 13150
      }
    }
  }
}
```

## Usage in Code

### Log API Call
```python
from app.services.api_usage_tracker import api_usage_tracker

# After calling Groq API
await api_usage_tracker.log_api_call(
    user_id=user_id,
    service_name="groq",
    endpoint="/v1/chat/completions",
    method="POST",
    status_code=200,
    tokens_used=response.usage.total_tokens,
    duration_ms=1250,
    metadata={"model": "llama-3.1-70b-versatile"}
)
```

### Check Rate Limit Before Call
```python
# Before making API call
limit_info = await api_usage_tracker.check_rate_limit(
    user_id=user_id,
    service_name="groq",
    limit_type="minute"
)

if not limit_info["can_call"]:
    raise HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded. Try again in {limit_info['reset_at']}"
    )

# Make API call...
```

## Benefits of New Design

### ✅ Flexible Rate Limits
- Global defaults for all users
- Per-user overrides for premium/custom tiers
- Easy to update without code changes
- No need to pre-create records for all users

### ✅ Accurate Tracking
- Real API call counts
- Actual tokens used
- No misleading cost estimates

### ✅ Scalable
- Materialized view for fast analytics
- Indexes for efficient queries
- Dynamic user limit creation

### ✅ Multi-Tier Support
- Free tier: Default limits
- Premium tier: Override with higher limits
- Enterprise: Custom limits per user

## Migration Steps

1. **Run Migration:**
   ```bash
   psql -h host -U postgres -d postgres \
     -f backend/database_migrations/005_api_usage_tracking.sql
   ```

2. **Verify Tables Created:**
   ```sql
   \dt api_usage_logs
   \dt service_rate_limit_configs
   \dt api_rate_limits
   ```

3. **Check Default Configs:**
   ```sql
   SELECT * FROM service_rate_limit_configs;
   ```

4. **Test API Endpoints:**
   - Visit http://localhost:8000/docs
   - Test `/api/usage/summary`
   - Verify rate limits returned

## Future Enhancements

1. **Admin Panel for Rate Limits**
   - UI to update global defaults
   - UI to set user-specific overrides
   - Bulk update for user tiers

2. **Real Cost Integration**
   - Connect to Groq billing API
   - Fetch actual usage costs
   - Display real spending

3. **Usage Alerts**
   - Email when 80% of limit reached
   - Webhook notifications
   - Dashboard warnings

4. **Analytics Dashboard**
   - Usage trends over time
   - Service comparison charts
   - Token usage patterns

## Summary

✅ **Rate limits are configurable** - Not hardcoded  
✅ **Cost estimation removed** - No misleading data  
✅ **Flexible per-user overrides** - Support multiple tiers  
✅ **Accurate tracking** - Real calls, tokens, performance  
✅ **Scalable design** - Ready for growth  

The system now provides accurate API usage tracking with flexible rate limiting, without making inaccurate cost estimates.
