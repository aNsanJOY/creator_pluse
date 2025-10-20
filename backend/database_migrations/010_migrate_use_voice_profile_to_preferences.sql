-- Migrate use_voice_profile from column to preferences JSONB field
-- This migration moves the use_voice_profile data from the column into the preferences JSONB

-- Step 1: Update preferences JSONB to include use_voice_profile from the column
UPDATE users 
SET preferences = jsonb_set(
    COALESCE(preferences, '{}'::jsonb),
    '{use_voice_profile}',
    to_jsonb(COALESCE(use_voice_profile, false))
)
WHERE preferences IS NULL OR NOT (preferences ? 'use_voice_profile');

-- Step 2: Drop the use_voice_profile column
ALTER TABLE users 
DROP COLUMN IF EXISTS use_voice_profile;

-- Add comment
COMMENT ON COLUMN users.preferences IS 'User preferences stored as JSONB including use_voice_profile, tone_preferences, notification_preferences, etc.';
