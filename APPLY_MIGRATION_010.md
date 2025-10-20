# Quick Guide: Apply Migration 010

## What This Does
Moves `use_voice_profile` from a database column to the `preferences` JSONB field, fixing the checkbox update issue.

## Steps to Apply

### 1. Connect to Your Database
Choose one of these methods:

#### Option A: Supabase Dashboard (Easiest)
1. Go to your Supabase project dashboard
2. Click on "SQL Editor" in the left sidebar
3. Click "New Query"
4. Copy and paste the SQL below
5. Click "Run"

#### Option B: Local Development
```bash
# If using Supabase CLI
cd backend
supabase db push
```

### 2. Run This SQL

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

### 3. Verify Migration Success

Run this query to confirm the column is gone:
```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'use_voice_profile';
```
**Expected result:** No rows (empty result)

Run this to check data is in preferences:
```sql
SELECT id, email, preferences->'use_voice_profile' as use_voice_profile 
FROM users 
LIMIT 5;
```
**Expected result:** You should see `true` or `false` values

### 4. Restart Your Backend Server
```bash
# Stop the backend if running (Ctrl+C)
# Then restart it
cd backend
python -m uvicorn app.main:app --reload
```

### 5. Test the Fix
1. Open your app in the browser
2. Go to Profile page
3. Toggle the "Use Voice Profile" checkbox
4. Verify it updates correctly
5. Refresh the page - checkbox should maintain its state

## Troubleshooting

### If migration fails with "column does not exist"
The column was already removed. Just run the first UPDATE statement to ensure data is in preferences:
```sql
UPDATE users 
SET preferences = jsonb_set(
    COALESCE(preferences, '{}'::jsonb),
    '{use_voice_profile}',
    to_jsonb(false)
)
WHERE preferences IS NULL OR NOT (preferences ? 'use_voice_profile');
```

### If checkbox still doesn't update
1. Check browser console for errors
2. Verify backend is restarted
3. Clear browser cache and reload
4. Check that preferences API is returning `use_voice_profile` in the response

## Need Help?
See `USE_VOICE_PROFILE_MIGRATION.md` for detailed documentation and rollback instructions.
