# Database Schema Cleanup Summary

## Changes Made

### Problem
The database had two tables for storing newsletters:
- `newsletters` - Original table from initial schema
- `newsletter_drafts` - Added later for draft functionality

This caused:
- Confusion about which table to use
- Duplicate logic in code
- Foreign key issues with feedback table

### Solution
**Consolidated to use only `newsletter_drafts` table**

## Files Modified

### 1. `database_migrations/database_schema.sql`
- **Removed**: `newsletters` table definition
- **Updated**: `feedback` table to remove foreign key constraint (will be added in migration)
- **Removed**: All indexes, triggers, RLS policies, and comments for `newsletters` table
- **Added**: Comments explaining the deprecation

### 2. `database_migrations/003_update_feedback_foreign_key.sql` (NEW)
- Migration script to:
  - Drop old foreign key constraint from feedback table
  - Add new foreign key to `newsletter_drafts` table
  - Drop the deprecated `newsletters` table
  - Add documentation comments

### 3. `backend/app/api/routes/feedback.py`
- **Simplified**: Removed dual-table checks
- **Updated**: `submit_feedback()` to only check `newsletter_drafts`
- **Updated**: `get_newsletter_feedback()` to only check `newsletter_drafts`
- **Cleaner**: More straightforward error messages

### 4. `backend/app/api/routes/user.py`
- **Updated**: Account deletion to delete from `newsletter_drafts` instead of `newsletters`
- **Added**: Deletion of `newsletter_samples` table data

## Database Structure (After Cleanup)

### Tables
```
users
├── sources
│   └── source_content_cache
├── newsletter_drafts (main table for all newsletters)
├── newsletter_samples (for voice training)
├── feedback (references newsletter_drafts)
└── trends
```

### Feedback Table
```sql
CREATE TABLE feedback (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    newsletter_id UUID,  -- Will reference newsletter_drafts after migration
    feedback_type VARCHAR(50),
    section_id VARCHAR(255),
    comment TEXT,
    created_at TIMESTAMP
);
```

## Migration Steps

### To Apply This Change to Your Database:

1. **Run the migration script**:
   ```sql
   -- Execute: database_migrations/003_update_feedback_foreign_key.sql
   ```

2. **What the migration does**:
   - Drops old foreign key constraint
   - Adds new foreign key to `newsletter_drafts`
   - **DROPS the `newsletters` table** (⚠️ data will be lost)

3. **Before running migration**:
   - Backup your database
   - Ensure no important data exists in `newsletters` table
   - Or migrate data from `newsletters` to `newsletter_drafts` first

### If You Have Data in `newsletters` Table:

**Option A**: Migrate data first
```sql
-- Copy data from newsletters to newsletter_drafts
INSERT INTO newsletter_drafts (id, user_id, title, sections, status, metadata, generated_at)
SELECT 
    id, 
    user_id, 
    title, 
    ARRAY[]::jsonb[], -- Empty sections array
    CASE 
        WHEN status = 'sent' THEN 'published'
        WHEN status = 'scheduled' THEN 'ready'
        ELSE 'ready'
    END,
    metadata,
    created_at
FROM newsletters
WHERE id NOT IN (SELECT id FROM newsletter_drafts);

-- Then run the migration
```

**Option B**: Just drop it (if no important data)
```sql
-- The migration script will handle this
```

## Benefits

✅ **Simpler codebase** - No more dual-table checks  
✅ **Clearer data model** - One source of truth  
✅ **Better maintainability** - Less confusion  
✅ **Proper foreign keys** - Database integrity enforced  
✅ **Faster queries** - No need to check multiple tables  

## Testing

After applying changes:

1. **Test feedback submission**:
   ```bash
   POST /api/feedback
   {
     "newsletter_id": "<draft_id>",
     "section_id": "intro",
     "feedback_type": "thumbs_up"
   }
   ```

2. **Verify foreign key**:
   ```sql
   -- Should fail (good!)
   INSERT INTO feedback (user_id, newsletter_id, feedback_type)
   VALUES ('some-user-id', 'non-existent-draft-id', 'thumbs_up');
   ```

3. **Test account deletion**:
   ```bash
   DELETE /api/user/account
   ```

## Notes

- The `newsletter_drafts` table is defined in `draft_schema.sql`
- All draft-related APIs already use `newsletter_drafts`
- The feedback API now correctly references the right table
- No application code changes needed beyond what's already done

---

**Status**: ✅ Code updated, migration script ready  
**Next Step**: Run migration script on your Supabase database
