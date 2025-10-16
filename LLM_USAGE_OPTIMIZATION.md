# LLM Usage Card Optimization

## Issue
The `/api/llm/usage/summary` endpoint was being called excessively, causing unnecessary load on the backend and database.

## Root Causes
1. **Short refresh interval**: Component was refreshing every 30 seconds
2. **No caching**: Each component mount made a fresh API call
3. **Component re-mounts**: Dashboard re-renders could cause multiple calls

## Solutions Implemented

### 1. Increased Refresh Interval
- **Before**: 30 seconds (30000ms)
- **After**: 2 minutes (120000ms)
- **Impact**: 75% reduction in periodic API calls

### 2. Global Caching Layer
Added a global cache with 1-minute duration:
```typescript
let cachedUsage: any = null;
let lastFetchTime = 0;
const CACHE_DURATION = 60000; // 1 minute cache
```

**Benefits**:
- Multiple component instances share the same cached data
- Prevents duplicate API calls within the cache window
- Component re-mounts use cached data instead of making new requests

### 3. Cache Logic
```typescript
const now = Date.now();

// Use cached data if available and fresh
if (cachedUsage && (now - lastFetchTime) < CACHE_DURATION) {
  console.log("Using cached LLM usage data");
  setUsage(cachedUsage);
  return;
}

// Fetch fresh data and update cache
const response = await axios.get(`${API_URL}/api/llm/usage/summary`, ...);
cachedUsage = response.data.summary;
lastFetchTime = now;
```

## Results

### Before Optimization
- API call every 30 seconds
- Additional calls on every component mount/re-mount
- No request deduplication
- **Estimated**: 120+ calls per hour

### After Optimization
- API call every 2 minutes (when component is mounted)
- Cached responses for 1 minute
- Shared cache across component instances
- **Estimated**: ~30 calls per hour (75% reduction)

## Monitoring
Check browser console for these logs:
- `"Using cached LLM usage data"` - Cache hit
- `"Fetching fresh LLM usage data..."` - Fresh API call
- `"LLM Usage Response:"` - API response received

## Future Improvements
1. **React Context**: Move to a global context provider to centralize state
2. **WebSocket**: Use real-time updates instead of polling
3. **User activity detection**: Pause polling when user is inactive
4. **Exponential backoff**: Reduce frequency if data doesn't change often

## Files Modified
- `frontend/src/components/LLMUsageCard.tsx`
  - Added global cache variables
  - Implemented cache checking logic
  - Increased refresh interval from 30s to 2min
  - Added console logging for debugging
