-- Add use_voice_profile column to users table
-- This column determines whether to use voice profile or tone preferences for draft generation

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS use_voice_profile BOOLEAN DEFAULT FALSE;

-- Set to TRUE for users who already have a voice_profile
UPDATE users 
SET use_voice_profile = TRUE 
WHERE voice_profile IS NOT NULL AND voice_profile != 'null'::jsonb;

-- Add comment
COMMENT ON COLUMN users.use_voice_profile IS 'Whether to use voice profile (true) or tone preferences (false) for draft generation';
