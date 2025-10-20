# LLM Rate Limit Tracking - Fix Summary

## Issues Fixed

### 1. **Rate Limits Not Updating Correctly**
**Problem:** Per Minute and Per Day counters were not incrementing properly or showing correct values in the UI.

**Root Causes:**
- Rate limits were only updated if they already existed in the database
- No automatic creation of rate limit records for both "minute" and "day" types
- Reset time calculations were not precise (not aligned to minute/day boundaries)
- Frontend was caching data for too long (2 minutes)

### 2. **Backend Fixes**

#### `backend/app/services/llm_usage_tracker.py`

**A. Updated `_update_rate_limit()` Method:**
```python
async def _update_rate_limit(self, user_id: str):
    """Update rate limit counters for all limit types"""
    # Ensure rate limits exist for all types
    limit_types = ["minute", "day"]
    
    for limit_type in limit_types:
        # Get or create rate limit
        result = self.supabase.table("llm_rate_limits").select("*").eq(
            "user_id", user_id
        ).eq("limit_type", limit_type).execute()
        
        now = datetime.now(timezone.utc)
        
        if not result.data:
            # Create new rate limit
            await self._create_user_rate_limit(user_id, limit_type)
            # Set count to 1 for this call
            self.supabase.table("llm_rate_limits").update({
                "current_count": 1
            }).eq("user_id", user_id).eq("limit_type", limit_type).execute()
        else:
            limit = result.data[0]
            reset_at = datetime.fromisoformat(limit["reset_at"].replace("Z", "+00:00"))
            
            # Check if reset time has passed
            if now >= reset_at:
                # Reset counter and set new reset time
                new_reset_at = self._calculate_next_reset(limit_type)
                self.supabase.table("llm_rate_limits").update({
                    "current_count": 1,
                    "reset_at": new_reset_at.isoformat()
                }).eq("id", limit["id"]).execute()
            else:
                # Increment counter
                self.supabase.table("llm_rate_limits").update({
                    "current_count": limit["current_count"] + 1
                }).eq("id", limit["id"]).execute()
```

**Changes:**
- ✅ Now updates BOTH "minute" and "day" rate limits on every LLM call
- ✅ Automatically creates rate limit records if they don't exist
- ✅ Properly resets counters when reset time has passed
- ✅ Sets new reset time when resetting

**B. Improved `_calculate_next_reset()` Method:**
```python
def _calculate_next_reset(self, limit_type: str) -> datetime:
    """Calculate next reset time based on limit type"""
    now = datetime.now(timezone.utc)
    
    if limit_type == "minute":
        # Reset at the start of the next minute
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        return next_minute
    elif limit_type == "hour":
        # Reset at the start of the next hour
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return next_hour
    elif limit_type == "day":
        # Reset at midnight UTC of the next day
        next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return next_day
    elif limit_type == "month":
        # Reset at start of next month
        if now.month == 12:
            return datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            return datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    
    # Default to next day at midnight
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
```

**Changes:**
- ✅ Minute resets align to exact minute boundaries (e.g., 10:05:00, 10:06:00)
- ✅ Day resets align to midnight UTC (00:00:00)
- ✅ More predictable and accurate reset times

**C. Enhanced `check_rate_limit()` Method:**
```python
# Check if reset time has passed
if now >= reset_at:
    # Reset the counter and update reset time
    new_reset_at = self._calculate_next_reset(limit_type)
    self.supabase.table("llm_rate_limits").update({
        "current_count": 0,
        "reset_at": new_reset_at.isoformat()
    }).eq("id", limit["id"]).execute()
    
    can_call = True
    current_count = 0
    reset_at_str = new_reset_at.isoformat()
else:
    can_call = limit["current_count"] < limit["limit_value"]
    current_count = limit["current_count"]
    reset_at_str = limit["reset_at"]
```

**Changes:**
- ✅ Automatically resets counters when checking if reset time passed
- ✅ Updates reset time to next period
- ✅ Returns accurate current_count

**D. Added Logging:**
```python
logger.info(f"Rate limit check for user {user_id}, type {limit_type}: {result_dict}")
```

**Changes:**
- ✅ Logs rate limit values for debugging
- ✅ Helps track what values are being returned

### 3. **Frontend Fixes**

#### `frontend/src/components/LLMUsageCard.tsx`

**A. Reduced Cache Duration:**
```typescript
const CACHE_DURATION = 10000; // 10 seconds cache (reduced for real-time updates)
```

**Changes:**
- ✅ Reduced from 60 seconds to 10 seconds
- ✅ More frequent updates for real-time accuracy

**B. Increased Refresh Frequency:**
```typescript
// Refresh every 30 seconds for real-time updates
const interval = setInterval(fetchUsage, 30000);
```

**Changes:**
- ✅ Reduced from 2 minutes to 30 seconds
- ✅ Better real-time tracking

**C. Added Manual Refresh Button:**
```tsx
<button
  onClick={handleRefresh}
  disabled={refreshing}
  className="p-1.5 hover:bg-gray-100 rounded-full transition-colors disabled:opacity-50"
  title="Refresh usage data"
>
  <RefreshCw className={`w-4 h-4 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
</button>
```

**Changes:**
- ✅ Users can manually refresh to see latest counts
- ✅ Shows spinning animation while refreshing
- ✅ Bypasses cache when manually refreshed

**D. Display Current Count:**
```tsx
{/* Per Minute */}
<span>{usage.rate_limits.per_minute.current_count} / {usage.rate_limits.per_minute.limit_value} calls</span>

{/* Per Day */}
<span>
  {formatNumber(usage.rate_limits.per_day.current_count)} / {formatNumber(usage.rate_limits.per_day.limit_value)} calls
</span>
```

**Changes:**
- ✅ Shows "5 / 30 calls" instead of just "30 calls"
- ✅ Makes it clear how many calls have been made
- ✅ Easier to verify counts are updating

## How It Works Now

### 1. **When LLM Call is Made:**
```
User makes LLM API call
  ↓
llm_usage_tracker.log_llm_call() is called
  ↓
Log is inserted into llm_usage_logs table
  ↓
_update_rate_limit() is called
  ↓
For "minute" limit:
  - Check if record exists → Create if not
  - Check if reset time passed → Reset counter if yes
  - Increment counter
  ↓
For "day" limit:
  - Check if record exists → Create if not
  - Check if reset time passed → Reset counter if yes
  - Increment counter
```

### 2. **When UI Checks Rate Limits:**
```
Frontend calls /api/llm/usage/summary
  ↓
Backend calls check_rate_limit("minute")
  ↓
Check if reset time passed → Reset if yes
  ↓
Return: current_count, limit_value, remaining, reset_at
  ↓
Backend calls check_rate_limit("day")
  ↓
Check if reset time passed → Reset if yes
  ↓
Return: current_count, limit_value, remaining, reset_at
  ↓
Frontend displays both limits with current counts
```

### 3. **Reset Behavior:**

**Per Minute:**
- Resets at the start of each minute (e.g., 10:05:00, 10:06:00)
- Counter goes back to 0
- New reset_at set to next minute

**Per Day:**
- Resets at midnight UTC (00:00:00)
- Counter goes back to 0
- New reset_at set to next day at midnight

## Testing

### Verify Rate Limit Updates:

1. **Make an LLM API call** (e.g., generate a draft)
2. **Check the dashboard** - Per Minute and Per Day counts should increment
3. **Click refresh button** - Should show updated counts immediately
4. **Wait for auto-refresh** (30 seconds) - Counts update automatically
5. **Check backend logs** - Should see rate limit logging

### Verify Reset Behavior:

1. **Per Minute:** Wait for the next minute boundary, refresh, count should reset to 0
2. **Per Day:** Wait until midnight UTC, refresh, count should reset to 0

### Database Verification:

```sql
-- Check rate limits for a user
SELECT * FROM llm_rate_limits WHERE user_id = 'your-user-id';

-- Check recent LLM usage logs
SELECT * FROM llm_usage_logs 
WHERE user_id = 'your-user-id' 
ORDER BY created_at DESC 
LIMIT 10;
```

## Summary of Changes

### Backend (`llm_usage_tracker.py`)
- ✅ Fixed `_update_rate_limit()` to update both minute and day limits
- ✅ Auto-creates rate limit records if missing
- ✅ Improved `_calculate_next_reset()` for precise reset times
- ✅ Enhanced `check_rate_limit()` to auto-reset expired counters
- ✅ Added logging for debugging

### Frontend (`LLMUsageCard.tsx`)
- ✅ Reduced cache duration from 60s to 10s
- ✅ Increased refresh frequency from 2min to 30s
- ✅ Added manual refresh button with loading state
- ✅ Display current count alongside limit (e.g., "5 / 30 calls")
- ✅ Force refresh bypasses cache

## Expected Behavior

✅ **Per Minute counter** increments with each LLM call
✅ **Per Day counter** increments with each LLM call
✅ **Counters reset** at precise boundaries (minute/day)
✅ **UI updates** every 30 seconds automatically
✅ **Manual refresh** shows immediate updates
✅ **Current counts** are clearly visible
✅ **Progress bars** accurately reflect usage
✅ **Remaining counts** are calculated correctly

The LLM rate limiting system now provides accurate, real-time tracking of API usage! 🎉
