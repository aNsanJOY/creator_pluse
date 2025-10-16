-- Migration: Update feedback table to reference newsletter_drafts instead of newsletters
-- This migration consolidates the schema to use only newsletter_drafts table

-- Step 1: Drop the old foreign key constraint if it exists
ALTER TABLE feedback 
DROP CONSTRAINT IF EXISTS feedback_newsletter_id_fkey;

-- Step 2: Add new foreign key constraint to newsletter_drafts
-- Note: This assumes newsletter_drafts table exists (created in draft_schema.sql)
ALTER TABLE feedback 
ADD CONSTRAINT feedback_newsletter_id_fkey 
  FOREIGN KEY (newsletter_id) 
  REFERENCES newsletter_drafts(id) 
  ON DELETE CASCADE;

-- Step 3: Add comment for clarity
COMMENT ON CONSTRAINT feedback_newsletter_id_fkey ON feedback 
IS 'References newsletter_drafts table (not newsletters - that table is deprecated)';

-- Step 4: Drop the deprecated newsletters table if it exists
-- WARNING: This will delete all data in the newsletters table
-- If you have important data, migrate it to newsletter_drafts first
DROP TABLE IF EXISTS newsletters CASCADE;

-- Note: After running this migration:
-- 1. All feedback must reference valid newsletter_drafts records
-- 2. The newsletters table is completely removed
-- 3. Update any application code that references the newsletters table
