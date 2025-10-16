# API Usage Tracking

## Overview
Comprehensive system to track API calls to external services (Groq, Twitter, YouTube, etc.), monitor rate limits, and calculate costs.

## Features

### 1. Usage Logging
- Tracks every API call to external services
- Records tokens used (for LLM services)
- Calculates estimated costs
- Logs response times and errors

### 2. Rate Limiting
- Enforces rate limits per service
- Supports multiple time windows (minute, hour, day, month)
- Auto-resets counters when time window expires
- Prevents exceeding API quotas

### 3. Cost Tracking
- Estimates costs based on tokens used
- Supports multiple pricing tiers
- Tracks cumulative costs over time

### 4. Analytics
- Daily, weekly, monthly usage summaries
- Breakdown by service
- Performance metrics (avg response time)
- Error rate tracking

## Database Schema

### `api_usage_logs`
Logs every API call:
- `user_id`: User making the call
- `service_name`: Service (groq, twitter, youtube, etc.)
- `endpoint`: API endpoint called
- `method`: HTTP method
- `status_code`: Response status
- `tokens_used`: Tokens consumed (for LLMs)
- `cost_usd`: Estimated cost
- `duration_ms`: Request duration
- `error_message`: Error if failed
- `metadata`: Additional data (model, parameters)
- `created_at`: Timestamp

### `api_rate_limits`
Tracks rate limits per user/service:
- `user_id`: User ID
- `service_name`: Service name
- `limit_type`: Time window (minute, hour, day, month)
- `limit_value`: Maximum calls allowed
- `current_count`: Current usage in window
- `reset_at`: When counter resets

### `api_usage_daily_summary` (Materialized View)
Pre-aggregated daily statistics for fast queries

## API Endpoints

### GET /api/usage/stats
Get usage statistics

**Query Parameters:**
- `service` (optional): Filter by service name
- `days` (default: 30): Number of days to look back

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_calls": 1250,
    "total_tokens": 450000,
    "total_cost": 0.265,
    "by_service": {
      "groq": {
        "calls": 1000,
        "tokens": 400000,
        "cost": 0.236
      },
      "twitter": {
        "calls": 250,
        "tokens": 0,
        "cost": 0.029
      }
    },
    "by_day": [
      {
        "date": "2025-10-15",
        "calls": 45,
        "tokens": 18000,
        "cost": 0.011
      }
    ]
  }
}
```

### GET /api/usage/rate-limits
Get all rate limits for current user

**Query Parameters:**
- `service` (optional): Filter by service

**Response:**
```json
{
  "success": true,
  "rate_limits": [
    {
      "service_name": "groq",
      "limit_type": "minute",
      "current_count": 12,
      "limit_value": 30,
      "remaining": 18,
      "reset_at": "2025-10-16T14:05:00Z",
      "percentage_used": 40.0
    },
    {
      "service_name": "groq",
      "limit_type": "day",
      "current_count": 1250,
      "limit_value": 14400,
      "remaining": 13150,
      "percentage_used": 8.68
    }
  ]
}
```

### GET /api/usage/rate-limits/{service}
Check rate limit for specific service

**Path Parameters:**
- `service`: Service name (groq, twitter, etc.)

**Query Parameters:**
- `limit_type` (default: minute): minute, hour, day, or month

**Response:**
```json
{
  "success": true,
  "can_call": true,
  "current_count": 12,
  "limit_value": 30,
  "remaining": 18,
  "reset_at": "2025-10-16T14:05:00Z"
}
```

### GET /api/usage/logs
Get detailed usage logs

**Query Parameters:**
- `service` (optional): Filter by service
- `limit` (default: 50): Number of logs to return
- `offset` (default: 0): Pagination offset

**Response:**
```json
{
  "success": true,
  "logs": [
    {
      "id": "uuid",
      "service_name": "groq",
      "endpoint": "/v1/chat/completions",
      "method": "POST",
      "status_code": 200,
      "tokens_used": 450,
      "cost_usd": 0.000265,
      "duration_ms": 1250,
      "metadata": {
        "model": "llama-3.1-70b-versatile"
      },
      "created_at": "2025-10-16T13:45:23Z"
    }
  ],
  "total": 1250,
  "limit": 50,
  "offset": 0
}
```

### GET /api/usage/summary
Get quick usage summary

**Response:**
```json
{
  "success": true,
  "summary": {
    "today": {
      "calls": 45,
      "tokens": 18000,
      "cost": 0.011
    },
    "this_month": {
      "calls": 1250,
      "tokens": 450000,
      "cost": 0.265
    },
    "groq_limits": {
      "per_minute": {
        "can_call": true,
        "current_count": 12,
        "limit_value": 30,
        "remaining": 18
      },
      "per_day": {
        "can_call": true,
        "current_count": 1250,
        "limit_value": 14400,
        "remaining": 13150
      }
    }
  }
}
```

## Usage in Code

### Logging API Calls

```python
from app.services.api_usage_tracker import api_usage_tracker

# After making an API call to Groq
await api_usage_tracker.log_api_call(
    user_id=user_id,
    service_name="groq",
    endpoint="/v1/chat/completions",
    method="POST",
    status_code=200,
    tokens_used=450,
    duration_ms=1250,
    metadata={
        "model": "llama-3.1-70b-versatile",
        "temperature": 0.7
    }
)
```

### Checking Rate Limits

```python
from app.services.api_usage_tracker import api_usage_tracker

# Before making an API call
limit_info = await api_usage_tracker.check_rate_limit(
    user_id=user_id,
    service_name="groq",
    limit_type="minute"
)

if not limit_info["can_call"]:
    raise HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded. Resets at {limit_info['reset_at']}"
    )

# Make API call...
```

## Rate Limits (Default)

### Groq (Free Tier)
- **Per Minute**: 30 requests
- **Per Day**: 14,400 requests

### Twitter API (Free Tier)
- **Per Month**: 1,500 tweets

### YouTube API (Free Tier)
- **Per Day**: 10,000 quota units

## Cost Estimates

### Groq Pricing (per 1M tokens)
- **llama-3.1-70b-versatile**: $0.59
- **llama-3.1-8b-instant**: $0.05
- **mixtral-8x7b**: $0.24

### OpenAI Pricing (per 1M tokens)
- **GPT-4**: $30.00
- **GPT-3.5-turbo**: $0.50

*Note: Costs are estimates. Actual costs may vary.*

## Integration with Existing Services

### 1. Newsletter Generation Service
Add logging after Groq API calls:

```python
# In newsletter_generator.py
response = groq_client.chat.completions.create(...)

# Log the call
await api_usage_tracker.log_api_call(
    user_id=user_id,
    service_name="groq",
    endpoint="/v1/chat/completions",
    tokens_used=response.usage.total_tokens,
    metadata={"model": model}
)
```

### 2. Twitter Crawler
Add logging after Twitter API calls:

```python
# In twitter crawler
tweets = api.user_timeline(...)

# Log the call
await api_usage_tracker.log_api_call(
    user_id=user_id,
    service_name="twitter",
    endpoint="/2/users/:id/tweets",
    metadata={"count": len(tweets)}
)
```

### 3. YouTube Crawler
Add logging after YouTube API calls:

```python
# In youtube crawler
videos = youtube.search().list(...)

# Log the call
await api_usage_tracker.log_api_call(
    user_id=user_id,
    service_name="youtube",
    endpoint="/youtube/v3/search",
    metadata={"quota_cost": 100}
)
```

## Dashboard Integration

Add a usage stats card to the dashboard:

```tsx
// In Dashboard.tsx
const [usageStats, setUsageStats] = useState(null);

useEffect(() => {
  const fetchUsageStats = async () => {
    const response = await axios.get('/api/usage/summary', {
      headers: { Authorization: `Bearer ${token}` }
    });
    setUsageStats(response.data.summary);
  };
  fetchUsageStats();
}, []);

// Display in UI
<Card>
  <CardTitle>API Usage Today</CardTitle>
  <CardContent>
    <div>Calls: {usageStats?.today.calls}</div>
    <div>Tokens: {usageStats?.today.tokens}</div>
    <div>Cost: ${usageStats?.today.cost}</div>
  </CardContent>
</Card>
```

## Maintenance

### Refresh Materialized View
Run periodically (e.g., daily via cron):

```sql
SELECT refresh_api_usage_summary();
```

### Clean Old Logs
Archive logs older than 90 days:

```sql
DELETE FROM api_usage_logs 
WHERE created_at < NOW() - INTERVAL '90 days';
```

## Monitoring Alerts

Set up alerts for:
1. **High Usage**: >80% of daily limit
2. **Rate Limit Exceeded**: 429 errors
3. **High Costs**: Daily cost exceeds threshold
4. **API Errors**: Error rate >5%

## Future Enhancements

1. **Budget Limits**: Set spending caps per user
2. **Usage Predictions**: Predict when limits will be reached
3. **Cost Optimization**: Suggest cheaper alternatives
4. **Real-time Dashboards**: Live usage monitoring
5. **Webhook Alerts**: Notify on threshold breaches
6. **Multi-tier Pricing**: Different limits for different user tiers

## Migration Instructions

1. **Run Database Migration:**
   ```bash
   psql -h your-host -U postgres -d postgres \
     -f backend/database_migrations/005_api_usage_tracking.sql
   ```

2. **Restart Backend:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

3. **Test Endpoints:**
   - Visit `http://localhost:8000/docs`
   - Test `/api/usage/summary`
   - Verify rate limits are created

4. **Integrate Logging:**
   - Add `api_usage_tracker.log_api_call()` to all external API calls
   - Test with a few API calls
   - Verify logs appear in database

## Troubleshooting

**Issue**: Rate limits not updating
**Solution**: Check that `_update_rate_limit()` is being called after logging

**Issue**: Costs showing as 0
**Solution**: Verify `tokens_used` is being passed and model is in COSTS dict

**Issue**: Logs not appearing
**Solution**: Check database connection and table permissions

## Summary

The API usage tracking system provides:
- ✅ Complete visibility into API usage
- ✅ Automatic rate limit enforcement
- ✅ Cost tracking and estimation
- ✅ Usage analytics and trends
- ✅ Protection against quota exhaustion

This ensures you never exceed API limits and can monitor costs effectively.
