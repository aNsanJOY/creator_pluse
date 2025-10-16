# Draft Generation Bug Fixes

## Issues Fixed

### 1. Missing LLM Usage Logs
**Problem**: LLM API calls were not being logged to the `llm_usage_logs` table due to datetime comparison errors.

**Root Cause**: 
- `datetime.utcnow()` creates offset-naive datetime objects
- Database timestamps are offset-aware (include timezone info)
- Comparing naive and aware datetimes throws: `can't compare offset-naive and offset-aware datetimes`

**Solution**:
- Updated all `datetime.utcnow()` calls to `datetime.now(timezone.utc)` in `llm_usage_tracker.py`
- This ensures all datetime objects are timezone-aware and comparable
- Files modified:
  - `backend/app/services/llm_usage_tracker.py`

### 2. Duplicate Draft Generation
**Problem**: Clicking "Generate New Draft" twice would create duplicate drafts.

**Root Cause**:
- Background task approach created a placeholder draft
- Then `draft_generator.generate_draft()` called `_store_draft()` which created another draft
- Result: Two drafts in the database for a single generation request

**Solution**:
- Refactored draft generation to update the placeholder instead of creating new drafts
- Modified `_create_fallback_draft()` to accept a `store` parameter (default `True` for backward compatibility)
- Updated background tasks in routes to:
  1. Create placeholder draft
  2. Generate content using internal methods
  3. Update placeholder with generated content
  4. Never create duplicate drafts
- Files modified:
  - `backend/app/api/routes/drafts.py` - `/generate` and `/{draft_id}/regenerate` endpoints
  - `backend/app/services/draft_generator.py` - `_create_fallback_draft()` method

## Testing Recommendations

### Test LLM Usage Logging
1. Generate a new draft
2. Check the `llm_usage_logs` table for new entries
3. Verify the logs contain:
   - `user_id`
   - `model` (e.g., "openai/gpt-oss-20b")
   - `tokens_used`, `prompt_tokens`, `completion_tokens`
   - `duration_ms`
   - `metadata` with service info

### Test Single Draft Generation
1. Click "Generate New Draft" once
2. Wait for generation to complete
3. Verify only ONE draft appears in the drafts list
4. Check database to confirm no duplicate entries

### Test Regeneration
1. Regenerate an existing draft
2. Verify the old draft is deleted
3. Verify only ONE new draft is created
4. Check that no orphaned drafts remain

## Database Queries for Verification

```sql
-- Check LLM usage logs
SELECT * FROM llm_usage_logs 
WHERE user_id = 'YOUR_USER_ID' 
ORDER BY created_at DESC 
LIMIT 10;

-- Check for duplicate drafts
SELECT id, title, status, generated_at 
FROM newsletter_drafts 
WHERE user_id = 'YOUR_USER_ID' 
ORDER BY generated_at DESC;

-- Count drafts by status
SELECT status, COUNT(*) 
FROM newsletter_drafts 
WHERE user_id = 'YOUR_USER_ID' 
GROUP BY status;
```

## Changes Summary

### Files Modified
1. `backend/app/services/llm_usage_tracker.py`
   - Added `timezone` import
   - Replaced all `datetime.utcnow()` with `datetime.now(timezone.utc)`

2. `backend/app/api/routes/drafts.py`
   - Refactored `generate_draft` endpoint background task
   - Refactored `regenerate_draft` endpoint background task
   - Both now update placeholders instead of creating new drafts

3. `backend/app/services/draft_generator.py`
   - Added `store` parameter to `_create_fallback_draft()`
   - Returns draft data without storing when `store=False`

## Next Steps
1. Restart the backend server to apply changes
2. Test draft generation with the fixes
3. Monitor logs for any remaining issues
4. Verify LLM usage tracking is working correctly
