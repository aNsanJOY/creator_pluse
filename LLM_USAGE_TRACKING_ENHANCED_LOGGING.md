# LLM Usage Tracking - Enhanced Logging & Debugging

## Issue
LLM API Usage data was not updating when generating drafts. The tracking code was in place but failures were happening silently without clear visibility into what was going wrong.

## Solution
Added comprehensive logging throughout the LLM usage tracking system to make all operations visible and debuggable.

## Changes Made

### `backend/app/services/llm_usage_tracker.py`

#### Enhanced `log_llm_call` Function

**Added detailed logging at every step:**

```python
async def log_llm_call(self, user_id: str, model: str, ...):
    try:
        self.initialize()
        
        # Log the incoming call
        logger.info(f"[LLM_USAGE] Logging call for user {user_id}: model={model}, tokens={tokens_used}, prompt={prompt_tokens}, completion={completion_tokens}")
        
        # Log the data being inserted
        log_data = {...}
        logger.info(f"[LLM_USAGE] Inserting log data: {log_data}")
        
        # Insert and verify
        result = self.supabase.table("llm_usage_logs").insert(log_data).execute()
        
        if result.data:
            logger.info(f"[LLM_USAGE] ✓ Log inserted successfully with ID: {result.data[0].get('id')}")
        else:
            logger.warning(f"[LLM_USAGE] ⚠ Log insert returned no data")
        
        # Log rate limit update
        logger.info(f"[LLM_USAGE] Updating rate limits for user {user_id}")
        await self._update_rate_limit(user_id)
        logger.info(f"[LLM_USAGE] ✓ Rate limits updated successfully")
        
    except Exception as e:
        logger.error(f"[LLM_USAGE] ✗ ERROR logging LLM usage: {str(e)}", exc_info=True)
        # Don't re-raise - logging failures shouldn't break the main operation
```

#### Enhanced `_update_rate_limit` Function

**Added detailed logging for rate limit operations:**

```python
async def _update_rate_limit(self, user_id: str):
    try:
        self.initialize()
        limit_types = ["minute", "day"]
        
        for limit_type in limit_types:
            logger.info(f"[RATE_LIMIT] Updating {limit_type} limit for user {user_id}")
            
            # Get existing limit
            result = self.supabase.table("llm_rate_limits").select("*").eq(
                "user_id", user_id
            ).eq("limit_type", limit_type).execute()
            
            now = datetime.now(timezone.utc)
            
            if not result.data:
                logger.info(f"[RATE_LIMIT] No {limit_type} limit found, creating new one")
                await self._create_user_rate_limit(user_id, limit_type)
                update_result = self.supabase.table("llm_rate_limits").update({
                    "current_count": 1
                }).eq("user_id", user_id).eq("limit_type", limit_type).execute()
                logger.info(f"[RATE_LIMIT] ✓ Created {limit_type} limit with count=1")
            else:
                limit = result.data[0]
                reset_at = datetime.fromisoformat(limit["reset_at"].replace("Z", "+00:00"))
                current_count = limit["current_count"]
                
                logger.info(f"[RATE_LIMIT] Current {limit_type}: count={current_count}, reset_at={reset_at}")
                
                if now >= reset_at:
                    # Reset counter
                    new_reset_at = self._calculate_next_reset(limit_type)
                    update_result = self.supabase.table("llm_rate_limits").update({
                        "current_count": 1,
                        "reset_at": new_reset_at.isoformat()
                    }).eq("id", limit["id"]).execute()
                    logger.info(f"[RATE_LIMIT] ✓ Reset {limit_type} limit: count=1, new_reset={new_reset_at}")
                else:
                    # Increment counter
                    new_count = current_count + 1
                    update_result = self.supabase.table("llm_rate_limits").update({
                        "current_count": new_count
                    }).eq("id", limit["id"]).execute()
                    logger.info(f"[RATE_LIMIT] ✓ Incremented {limit_type} limit: {current_count} -> {new_count}")
    
    except Exception as e:
        logger.error(f"[RATE_LIMIT] ✗ ERROR updating rate limit: {str(e)}", exc_info=True)
```

## Logging Prefixes

All logs now use clear prefixes for easy filtering:

- **`[LLM_USAGE]`** - Main LLM usage logging operations
- **`[RATE_LIMIT]`** - Rate limit update operations
- **`✓`** - Success indicator
- **`⚠`** - Warning indicator
- **`✗`** - Error indicator

## Log Examples

### Successful Draft Generation

```
[LLM_USAGE] Logging call for user abc123: model=openai/gpt-oss-20b, tokens=1234, prompt=800, completion=434
[LLM_USAGE] Inserting log data: {'user_id': 'abc123', 'model': 'openai/gpt-oss-20b', ...}
[LLM_USAGE] ✓ Log inserted successfully with ID: log-id-xyz
[LLM_USAGE] Updating rate limits for user abc123
[RATE_LIMIT] Updating minute limit for user abc123
[RATE_LIMIT] Current minute: count=5, reset_at=2025-10-18 15:46:00+00:00
[RATE_LIMIT] ✓ Incremented minute limit: 5 -> 6
[RATE_LIMIT] Updating day limit for user abc123
[RATE_LIMIT] Current day: count=42, reset_at=2025-10-19 00:00:00+00:00
[RATE_LIMIT] ✓ Incremented day limit: 42 -> 43
[LLM_USAGE] ✓ Rate limits updated successfully
```

### First Call (Creating Rate Limits)

```
[LLM_USAGE] Logging call for user new-user: model=openai/gpt-oss-20b, tokens=1000, prompt=600, completion=400
[LLM_USAGE] Inserting log data: {...}
[LLM_USAGE] ✓ Log inserted successfully with ID: log-123
[LLM_USAGE] Updating rate limits for user new-user
[RATE_LIMIT] Updating minute limit for user new-user
[RATE_LIMIT] No minute limit found, creating new one
[RATE_LIMIT] ✓ Created minute limit with count=1
[RATE_LIMIT] Updating day limit for user new-user
[RATE_LIMIT] No day limit found, creating new one
[RATE_LIMIT] ✓ Created day limit with count=1
[LLM_USAGE] ✓ Rate limits updated successfully
```

### Rate Limit Reset

```
[RATE_LIMIT] Updating minute limit for user abc123
[RATE_LIMIT] Current minute: count=30, reset_at=2025-10-18 15:45:00+00:00
[RATE_LIMIT] ✓ Reset minute limit: count=1, new_reset=2025-10-18 15:46:00+00:00
```

### Error Case

```
[LLM_USAGE] Logging call for user abc123: model=openai/gpt-oss-20b, tokens=1000
[LLM_USAGE] Inserting log data: {...}
[LLM_USAGE] ✗ ERROR logging LLM usage: Database connection failed
Traceback (most recent call last):
  ...
```

## Debugging Workflow

### Check if Logging is Being Called

```bash
# Search logs for LLM_USAGE entries
grep "[LLM_USAGE]" app.log

# Check for specific user
grep "[LLM_USAGE].*user_id_here" app.log
```

### Check if Rate Limits are Updating

```bash
# Search logs for RATE_LIMIT entries
grep "[RATE_LIMIT]" app.log

# Check for increment operations
grep "Incremented.*limit" app.log
```

### Check for Errors

```bash
# Search for error indicators
grep "✗" app.log

# Search for exceptions
grep "ERROR" app.log
```

### Verify in Database

```sql
-- Check recent LLM usage logs
SELECT * FROM llm_usage_logs 
WHERE user_id = 'user-id' 
ORDER BY created_at DESC 
LIMIT 10;

-- Check current rate limits
SELECT * FROM llm_rate_limits 
WHERE user_id = 'user-id';
```

## Common Issues & Solutions

### Issue 1: Logs Not Appearing

**Symptom:** No `[LLM_USAGE]` logs in output

**Possible Causes:**
- LLM usage tracker not being called
- Logger not configured
- Log level too high (set to ERROR instead of INFO)

**Solution:**
```python
# Check if draft_generator is calling the tracker
# Look for this in draft_generator.py around line 306:
await llm_usage_tracker.log_llm_call(...)
```

### Issue 2: Database Insert Fails

**Symptom:** `[LLM_USAGE] ✗ ERROR logging LLM usage: ...`

**Possible Causes:**
- Database connection issue
- Missing table or columns
- Invalid data types

**Solution:**
```sql
-- Verify table exists
SELECT * FROM llm_usage_logs LIMIT 1;

-- Check table structure
\d llm_usage_logs
```

### Issue 3: Rate Limits Not Updating

**Symptom:** Logs show insert success but rate limits don't change

**Possible Causes:**
- `_update_rate_limit` throwing exception
- Database update not committing

**Solution:**
- Check for `[RATE_LIMIT] ✗ ERROR` in logs
- Verify rate limit table exists and has correct schema

## Files Modified

- ✅ `backend/app/services/llm_usage_tracker.py`
  - Enhanced `log_llm_call` with detailed logging
  - Enhanced `_update_rate_limit` with detailed logging
  - Added clear log prefixes and indicators

## Benefits

1. **Visibility** - Every operation is logged with clear indicators
2. **Debuggability** - Easy to trace issues through log prefixes
3. **Non-Blocking** - Errors don't break draft generation
4. **Detailed Context** - Logs include user IDs, counts, timestamps
5. **Easy Filtering** - Use `grep "[LLM_USAGE]"` or `grep "[RATE_LIMIT]"`

## Testing

1. **Generate a draft** and watch the logs
2. **Check for `[LLM_USAGE]` entries** showing the call being logged
3. **Check for `[RATE_LIMIT]` entries** showing counters being updated
4. **Verify in database** that logs and rate limits are updated
5. **Check frontend** that LLM Usage card shows updated counts

## Summary

✅ **Enhanced logging** throughout LLM usage tracking system
✅ **Clear prefixes** for easy log filtering (`[LLM_USAGE]`, `[RATE_LIMIT]`)
✅ **Visual indicators** (✓, ⚠, ✗) for quick status scanning
✅ **Detailed context** in every log message
✅ **Non-blocking errors** - failures don't break draft generation
✅ **Full traceability** from API call to database update

Now you can easily debug LLM usage tracking issues by checking the logs! 🎉
