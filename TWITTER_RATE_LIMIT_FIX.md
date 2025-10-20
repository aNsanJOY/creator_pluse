# Twitter Rate Limit Handling Fix

## Problem
The application was hanging/becoming unresponsive when crawling Twitter sources that hit rate limits.

### Root Cause
1. **Tweepy client configured with `wait_on_rate_limit=True`**
   - When rate limit was hit, Tweepy would sleep synchronously for 600+ seconds
   - This blocked the entire async event loop
   - Application became unresponsive during the wait period

2. **Blocking behavior in async context**
   - The synchronous sleep in Tweepy blocked all other async operations
   - No other requests could be processed while waiting for rate limit reset

## Solution

### 1. Disabled Automatic Rate Limit Waiting
**File**: `backend/app/services/sources/twitter_connector.py`

Changed all Tweepy client initializations from:
```python
wait_on_rate_limit=True  # BLOCKS the event loop
```

To:
```python
wait_on_rate_limit=False  # Don't block, handle manually
```

This affects:
- OAuth 1.0a client initialization (line 55, 63)
- Bearer Token client initialization (line 71)

### 2. Updated Rate Limit Exception Handling
Changed from sleeping/waiting to raising an error immediately:

**Before:**
```python
except tweepy.TooManyRequests as e:
    print(f"X (Twitter) rate limit reached: {e}")
    await self.handle_rate_limit(retry_after=900)  # Sleeps for 15 minutes!
    return []
```

**After:**
```python
except tweepy.TooManyRequests as e:
    error_msg = (
        f"X (Twitter) rate limit exceeded: {e}\n\n"
        "Twitter API rate limits have been reached. Please try again later.\n"
        "Rate limits typically reset every 15 minutes.\n\n"
        "For more information: https://developer.x.com/en/docs/twitter-api/rate-limits"
    )
    print(error_msg)
    raise ValueError("X (Twitter) rate limit exceeded. Please try again in 15 minutes.")
```

## Benefits

✅ **Non-blocking**: Application remains responsive even when rate limited  
✅ **Clear error messages**: Users know exactly what happened and when to retry  
✅ **Proper error handling**: Rate limit errors are propagated to the crawler service  
✅ **Source status updates**: Failed crawls update source status to "error" with message  
✅ **Better UX**: Users can continue using the app while waiting for rate limit reset  

## User Experience

### When Rate Limit is Hit:
1. Crawl attempt fails immediately (no hanging)
2. Source status set to "error"
3. Error message displayed: "X (Twitter) rate limit exceeded. Please try again in 15 minutes."
4. User can retry manually after waiting period
5. Application remains fully functional for other operations

### Twitter API Rate Limits:
- **Free tier**: Very limited (500 posts/month read)
- **Basic tier**: $200/month, higher limits
- **Rate limit window**: Typically 15 minutes
- **Endpoint-specific**: Different endpoints have different limits

## Testing

1. ✅ Test crawl with valid credentials (should work)
2. ✅ Test crawl when rate limited (should fail gracefully without hanging)
3. ✅ Verify application remains responsive during rate limit error
4. ✅ Verify error message is clear and helpful
5. ✅ Test retry after rate limit window expires

## Related Files Modified

- `backend/app/services/sources/twitter_connector.py`
  - Lines 55, 63, 71: Changed `wait_on_rate_limit=False`
  - Lines 289-298: Updated rate limit exception handling
