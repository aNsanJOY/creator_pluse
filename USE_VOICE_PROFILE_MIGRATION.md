# Migration: use_voice_profile Column to Preferences JSONB

## Overview
This migration moves the `use_voice_profile` field from a separate database column to the `preferences` JSONB field in the `users` table.

## Problem
Previously, `use_voice_profile` was stored as a separate column in the `users` table (created by migration 009), while other preferences were stored in the `preferences` JSONB field. This caused inconsistency and made the preference update API fail to properly update the value.

## Solution
Store `use_voice_profile` in the `preferences` JSONB field along with all other user preferences.

## Changes Made

### 1. Database Migration
**File:** `backend/database_migrations/010_migrate_use_voice_profile_to_preferences.sql`

This migration:
- Copies existing `use_voice_profile` column values into the `preferences` JSONB field
- Drops the `use_voice_profile` column from the `users` table
- Updates the comment on the `preferences` column

### 2. Backend Code Updates

#### `backend/app/services/draft_scheduler.py`
**Changed:** Reading `use_voice_profile` from preferences JSONB instead of column
```python
# Before:
user_result = self.supabase.table("users").select("use_voice_profile").eq("id", user_id).execute()
use_voice = user_result.data[0].get("use_voice_profile", False)

# After:
use_voice = preferences.get("use_voice_profile", False)
```

#### `backend/app/api/routes/preferences.py`
**Already configured correctly** - handles `use_voice_profile` as part of the JSONB preferences:
- GET `/api/user/preferences` - returns `use_voice_profile` from JSONB
- PATCH `/api/user/preferences` - updates `use_voice_profile` in JSONB
- POST `/api/user/preferences/reset` - resets `use_voice_profile` to default (false)

### 3. Default Preferences
Both `auth.py` and `preferences.py` have `use_voice_profile: False` in their default preferences.

## How to Apply the Migration

### Option 1: Using Supabase CLI (Recommended)
```bash
cd backend
supabase db push
```

### Option 2: Manual SQL Execution
Run the SQL from `010_migrate_use_voice_profile_to_preferences.sql` directly in your Supabase SQL editor or via psql:

```sql
-- Migrate use_voice_profile from column to preferences JSONB field
UPDATE users 
SET preferences = jsonb_set(
    COALESCE(preferences, '{}'::jsonb),
    '{use_voice_profile}',
    to_jsonb(COALESCE(use_voice_profile, false))
)
WHERE preferences IS NULL OR NOT (preferences ? 'use_voice_profile');

-- Drop the use_voice_profile column
ALTER TABLE users 
DROP COLUMN IF EXISTS use_voice_profile;
```

## Verification Steps

1. **Before Migration:**
   ```sql
   SELECT id, use_voice_profile, preferences->'use_voice_profile' as pref_use_voice 
   FROM users LIMIT 5;
   ```

2. **After Migration:**
   ```sql
   -- Verify column is dropped
   SELECT column_name 
   FROM information_schema.columns 
   WHERE table_name = 'users' AND column_name = 'use_voice_profile';
   -- Should return no rows
   
   -- Verify data is in preferences
   SELECT id, preferences->'use_voice_profile' as use_voice_profile 
   FROM users LIMIT 5;
   ```

3. **Test API:**
   ```bash
   # Get preferences
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8000/api/user/preferences
   
   # Update use_voice_profile
   curl -X PATCH \
        -H "Authorization: Bearer YOUR_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"use_voice_profile": true}' \
        http://localhost:8000/api/user/preferences
   ```

## Rollback Plan
If you need to rollback:

```sql
-- Add column back
ALTER TABLE users ADD COLUMN use_voice_profile BOOLEAN DEFAULT FALSE;

-- Copy from preferences to column
UPDATE users 
SET use_voice_profile = (preferences->>'use_voice_profile')::boolean
WHERE preferences ? 'use_voice_profile';

-- Remove from preferences (optional)
UPDATE users 
SET preferences = preferences - 'use_voice_profile';
```

## Impact
- ✅ Fixes the checkbox update issue in the Profile page
- ✅ Centralizes all preferences in one JSONB field
- ✅ Simplifies preference management
- ✅ No data loss - existing values are migrated
- ✅ Backward compatible with default value (false)
