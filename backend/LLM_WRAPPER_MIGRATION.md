# LLM Wrapper Migration Summary

## Overview
All LLM API calls have been centralized through a single `LLMWrapper` class to enable proper logging and usage tracking.

## Changes Made

### 1. Created New File: `app/services/llm_wrapper.py`
- **Purpose**: Centralized wrapper for all LLM API calls
- **Key Features**:
  - Single point of entry for all LLM calls
  - Automatic usage logging to database via `llm_usage_tracker`
  - Comprehensive error handling
  - Detailed logging with service name, model, tokens, and duration
  - Metadata tracking for each call

### 2. Updated Services

All services now use `llm_wrapper.chat_completion()` instead of direct Groq API calls:

#### `app/services/voice_analyzer.py`
- **Removed**: Direct `Groq` client initialization
- **Added**: Import and use of `llm_wrapper`
- **Service Name**: `voice_analyzer`
- **Metadata Tracked**: `samples_count`

#### `app/services/feedback_analyzer.py`
- **Removed**: Direct `Groq` client initialization and manual usage logging
- **Added**: Import and use of `llm_wrapper`
- **Service Name**: `feedback_analyzer`
- **Metadata Tracked**: `positive_count`, `negative_count`

#### `app/services/draft_generator.py`
- **Removed**: Direct `Groq` client initialization and manual usage logging
- **Added**: Import and use of `llm_wrapper`
- **Service Name**: `draft_generator`
- **Metadata Tracked**: `trends_count`

#### `app/services/content_summarizer.py`
- **Removed**: Direct `Groq` client initialization and manual usage logging
- **Added**: Import and use of `llm_wrapper`
- **Service Name**: `content_summarizer`
- **Metadata Tracked**: `summary_type`

#### `app/services/trend_detector.py`
- **Removed**: Direct `Groq` client initialization and manual usage logging
- **Added**: Import and use of `llm_wrapper`
- **Service Name**: `trend_detector`
- **Metadata Tracked**: `content_count`

## Benefits

### 1. Centralized Logging
- All LLM calls are automatically logged to the `llm_usage_logs` table
- Consistent logging format across all services
- No need to manually add logging code in each service

### 2. Usage Tracking
- Token usage (total, prompt, completion) tracked for every call
- Duration tracking in milliseconds
- Service identification for analytics
- Custom metadata per service

### 3. Error Handling
- Centralized error handling and logging
- Failed calls are logged with error messages
- Prevents logging failures from breaking main operations

### 4. Maintainability
- Single point to update API configuration
- Easy to add new features (rate limiting, caching, etc.)
- Consistent interface across all services

### 5. Monitoring & Analytics
- Track which services use the most tokens
- Monitor API call durations
- Identify performance bottlenecks
- Cost tracking per service

## Usage Example

```python
from app.services.llm_wrapper import llm_wrapper

# Make a chat completion call
result = await llm_wrapper.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    user_id="user123",
    service_name="my_service",
    model="openai/gpt-oss-20b",
    temperature=0.7,
    max_tokens=1000,
    metadata={"custom_field": "value"}
)

# Access response and usage stats
response = result["response"]
usage = result["usage"]
print(f"Tokens used: {usage['total_tokens']}")
```

## Database Logging

Each call logs the following to `llm_usage_logs`:
- `user_id`: User making the request
- `model`: LLM model used
- `endpoint`: API endpoint (default: `/v1/chat/completions`)
- `status_code`: HTTP status (200 for success, 500 for error)
- `tokens_used`: Total tokens consumed
- `prompt_tokens`: Input tokens
- `completion_tokens`: Output tokens
- `duration_ms`: Request duration in milliseconds
- `error_message`: Error details if failed
- `metadata`: JSON object with service name and custom fields

## Rate Limiting

The wrapper automatically updates rate limits via `llm_usage_tracker`:
- Per-minute limits
- Per-day limits
- Automatic reset when time window expires

## Future Enhancements

Potential improvements to consider:
1. **Caching**: Cache responses for identical prompts
2. **Retry Logic**: Automatic retry with exponential backoff
3. **Model Fallback**: Try alternative models if primary fails
4. **Cost Estimation**: Pre-call cost estimation
5. **Streaming Support**: Add support for streaming responses
6. **Multi-Provider**: Support for OpenAI, Anthropic, etc.
