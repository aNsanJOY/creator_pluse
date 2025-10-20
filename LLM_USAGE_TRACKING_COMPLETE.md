# LLM Usage Tracking - Complete Implementation

## Overview
Comprehensive LLM usage tracking has been implemented across all services that make LLM API calls. This enables monitoring, rate limiting, and cost analysis.

## Services with LLM Usage Tracking

### ✅ 1. Draft Generator (`app/services/draft_generator.py`)
**Function:** `_generate_draft_content()`
**Tracks:**
- Model: Groq model (llama-3.1-70b-versatile)
- Tokens: Total, prompt, completion
- Duration: Request time in milliseconds
- Metadata: Service name, trends count

```python
await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model=self.model,
    endpoint="/v1/chat/completions",
    status_code=200,
    tokens_used=response.usage.total_tokens if response.usage else 0,
    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
    completion_tokens=response.usage.completion_tokens if response.usage else 0,
    duration_ms=duration_ms,
    metadata={"service": "draft_generator", "trends_count": len(trends)}
)
```

### ✅ 2. Voice Analyzer (`app/services/voice_analyzer.py`)
**Function:** `analyze_voice()`
**Tracks:**
- Model: Groq model
- Tokens: Total, prompt, completion
- Duration: Request time in milliseconds
- Metadata: Service name, samples count

```python
await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model=self.model,
    endpoint="/v1/chat/completions",
    status_code=200,
    tokens_used=response.usage.total_tokens if response.usage else 0,
    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
    completion_tokens=response.usage.completion_tokens if response.usage else 0,
    duration_ms=duration_ms,
    metadata={"service": "voice_analyzer", "samples_count": len(samples)}
)
```

### ✅ 3. Trend Detector (`app/services/trend_detector.py`)
**Function:** `detect_trends()`
**Tracks:**
- Model: Groq model
- Tokens: Total, prompt, completion
- Duration: Request time in milliseconds
- Metadata: Service name, content count

```python
await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model=self.model,
    endpoint="/v1/chat/completions",
    status_code=200,
    tokens_used=response.usage.total_tokens if response.usage else 0,
    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
    completion_tokens=response.usage.completion_tokens if response.usage else 0,
    duration_ms=duration_ms,
    metadata={"service": "trend_detector", "content_count": len(content_summaries)}
)
```

### ✅ 4. Feedback Analyzer (`app/services/feedback_analyzer.py`)
**Function:** `_analyze_patterns_with_groq()`
**Tracks:**
- Model: Groq model
- Tokens: Total, prompt, completion
- Duration: Request time in milliseconds
- Metadata: Service name, feedback count

```python
await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model=self.model,
    endpoint="/v1/chat/completions",
    status_code=200,
    tokens_used=response.usage.total_tokens if response.usage else 0,
    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
    completion_tokens=response.usage.completion_tokens if response.usage else 0,
    duration_ms=duration_ms,
    metadata={"service": "feedback_analyzer", "feedback_count": len(feedback_items)}
)
```

### ✅ 5. Content Summarizer (`app/services/content_summarizer.py`)
**Function:** `_summarize_with_groq()`
**Tracks:**
- Model: Groq model
- Tokens: Total, prompt, completion
- Duration: Request time in milliseconds
- Metadata: Service name, summary type

```python
await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model=self.model,
    endpoint="/v1/chat/completions",
    status_code=200,
    tokens_used=response.usage.total_tokens if response.usage else 0,
    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
    completion_tokens=response.usage.completion_tokens if response.usage else 0,
    duration_ms=duration_ms,
    metadata={"service": "content_summarizer", "summary_type": summary_type}
)
```

## Database Schema

### `llm_usage_logs` Table
```sql
CREATE TABLE llm_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    model VARCHAR(255) NOT NULL,
    endpoint VARCHAR(255) DEFAULT '/v1/chat/completions',
    status_code INTEGER DEFAULT 200,
    tokens_used INTEGER DEFAULT 0,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_llm_usage_logs_user_id ON llm_usage_logs(user_id);
CREATE INDEX idx_llm_usage_logs_created_at ON llm_usage_logs(created_at);
CREATE INDEX idx_llm_usage_logs_model ON llm_usage_logs(model);
```

### `llm_rate_limits` Table
```sql
CREATE TABLE llm_rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    limit_type VARCHAR(50) NOT NULL,  -- 'minute', 'hour', 'day', 'month'
    limit_value INTEGER NOT NULL,
    current_count INTEGER DEFAULT 0,
    reset_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, limit_type)
);
```

### `llm_rate_limit_configs` Table
```sql
CREATE TABLE llm_rate_limit_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    limit_type VARCHAR(50) NOT NULL UNIQUE,
    limit_value INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## LLM Usage Tracker Service

### Core Functions

#### 1. `log_llm_call()`
Logs every LLM API call with detailed metrics:
- User ID
- Model name
- Endpoint
- Status code
- Token usage (total, prompt, completion)
- Duration
- Error messages
- Custom metadata

#### 2. `check_rate_limit()`
Checks if user has exceeded rate limits:
- Returns: `can_call`, `current_count`, `limit_value`, `reset_at`, `remaining`
- Automatically creates default limits if none exist
- Returns safe defaults (1000) instead of 0 to prevent NaN errors

#### 3. `get_usage_stats()`
Retrieves usage statistics for a user:
- Total calls
- Total tokens
- Breakdown by model
- Breakdown by day
- Prompt vs completion tokens

#### 4. `_update_rate_limit()`
Updates rate limit counters after each call:
- Increments counter
- Resets counter if time window expired
- Calculates next reset time

## API Endpoints

### Get Usage Stats
```http
GET /api/llm/usage/stats?days=30
Authorization: Bearer <token>

Response:
{
  "total_calls": 150,
  "total_tokens": 45000,
  "total_prompt_tokens": 30000,
  "total_completion_tokens": 15000,
  "by_model": {
    "llama-3.1-70b-versatile": {
      "calls": 150,
      "tokens": 45000,
      "prompt_tokens": 30000,
      "completion_tokens": 15000
    }
  },
  "by_day": [
    {
      "date": "2024-01-01",
      "calls": 10,
      "tokens": 3000,
      "prompt_tokens": 2000,
      "completion_tokens": 1000
    }
  ]
}
```

### Get Rate Limits
```http
GET /api/llm/usage/rate-limits
Authorization: Bearer <token>

Response:
{
  "minute": {
    "can_call": true,
    "current_count": 5,
    "limit_value": 60,
    "remaining": 55,
    "reset_at": "2024-01-01T12:01:00Z"
  },
  "hour": {
    "can_call": true,
    "current_count": 50,
    "limit_value": 1000,
    "remaining": 950,
    "reset_at": "2024-01-01T13:00:00Z"
  },
  "day": {
    "can_call": true,
    "current_count": 150,
    "limit_value": 10000,
    "remaining": 9850,
    "reset_at": "2024-01-02T00:00:00Z"
  }
}
```

## Tracking Pattern

All services follow this consistent pattern:

```python
# 1. Track start time
import time
start_time = time.time()

# 2. Make LLM API call
response = self.client.chat.completions.create(...)

# 3. Calculate duration
duration_ms = int((time.time() - start_time) * 1000)

# 4. Log usage (with error handling)
if user_id:
    try:
        from app.services.llm_usage_tracker import llm_usage_tracker
        await llm_usage_tracker.log_llm_call(
            user_id=user_id,
            model=self.model,
            endpoint="/v1/chat/completions",
            status_code=200,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            duration_ms=duration_ms,
            metadata={"service": "service_name", "additional": "data"}
        )
    except Exception as log_error:
        logger.error(f"Failed to log LLM usage: {log_error}")
```

## Error Handling

### Graceful Degradation
- Logging failures don't affect main functionality
- All logging wrapped in try-except blocks
- Errors logged but not raised
- Safe defaults returned on failures

### Safe Defaults
```python
# Instead of returning 0 which causes NaN in frontend
return {
    "can_call": True,
    "current_count": 0,
    "limit_value": 1000,  # Safe default
    "reset_at": self._calculate_next_reset(limit_type).isoformat(),
    "remaining": 1000
}
```

## Benefits

1. **Cost Monitoring**: Track LLM API costs per user
2. **Rate Limiting**: Prevent abuse and manage quotas
3. **Performance Metrics**: Monitor response times
4. **Usage Analytics**: Understand which features use most tokens
5. **Debugging**: Trace LLM calls for troubleshooting
6. **Billing**: Foundation for usage-based billing

## Files Modified

### Services (Added Tracking)
- ✅ `app/services/draft_generator.py`
- ✅ `app/services/voice_analyzer.py`
- ✅ `app/services/trend_detector.py`
- ✅ `app/services/feedback_analyzer.py`
- ✅ `app/services/content_summarizer.py`

### Core Services
- ✅ `app/services/llm_usage_tracker.py` (Already existed)

### API Routes
- ✅ `app/api/routes/llm_usage.py` (Already existed)

### Database
- ✅ `database_migrations/005_api_usage_tracking.sql` (Already existed)

## Testing Checklist

### Tracking
- [ ] Draft generation logs usage
- [ ] Voice analysis logs usage
- [ ] Trend detection logs usage
- [ ] Feedback analysis logs usage
- [ ] Content summarization logs usage

### Data Accuracy
- [ ] Token counts match API response
- [ ] Duration calculated correctly
- [ ] Metadata stored properly
- [ ] User ID associated correctly

### Rate Limiting
- [ ] Limits enforced correctly
- [ ] Counters increment properly
- [ ] Reset times calculated correctly
- [ ] Default limits created for new users

### API Endpoints
- [ ] GET /api/llm/usage/stats returns correct data
- [ ] GET /api/llm/usage/rate-limits returns correct limits
- [ ] Data aggregation works correctly

### Error Handling
- [ ] Logging failures don't break main flow
- [ ] Safe defaults prevent NaN errors
- [ ] Errors logged appropriately

## Summary

✅ **All 5 LLM-calling services now track usage**
✅ **Consistent tracking pattern across all services**
✅ **Comprehensive metrics captured (tokens, duration, metadata)**
✅ **Rate limiting implemented**
✅ **Usage statistics API available**
✅ **Error handling prevents failures**
✅ **Safe defaults prevent frontend errors**

The LLM usage tracking system is now complete and consistent across the entire application!
