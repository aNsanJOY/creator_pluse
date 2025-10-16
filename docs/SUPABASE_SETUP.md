# Supabase Database Setup Guide

This guide provides detailed instructions for setting up the Supabase database for CreatorPulse.

## Overview

CreatorPulse uses Supabase for:
- PostgreSQL database
- User authentication
- Row Level Security (RLS)
- Real-time subscriptions (future feature)

## Prerequisites

- A Supabase account ([Sign up here](https://supabase.com))
- Access to the SQL Editor in Supabase dashboard

## Step-by-Step Setup

### 1. Create a New Supabase Project

1. Log in to [Supabase Dashboard](https://app.supabase.com)
2. Click **"New Project"**
3. Fill in the project details:
   - **Name**: `creatorpulse` (or your preferred name)
   - **Database Password**: Generate a strong password and save it securely
   - **Region**: Choose the region closest to your users
   - **Pricing Plan**: Free tier is sufficient for MVP
4. Click **"Create new project"**
5. Wait 2-3 minutes for the project to be provisioned

### 2. Get Your API Credentials

Once your project is ready:

1. Go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** → This is your `SUPABASE_URL`
   - **Project API keys** → **anon public** → This is your `SUPABASE_KEY`
   - **Project API keys** → **service_role** → This is your `SUPABASE_SERVICE_KEY`

⚠️ **Important**: Keep the `service_role` key secret! Never expose it in client-side code.

### 3. Execute the Database Schema

1. In your Supabase dashboard, navigate to **SQL Editor**
2. Click **"New Query"**
3. Open the file `backend/database_schema.sql` from your local project
4. Copy the entire content
5. Paste it into the SQL Editor
6. Click **"Run"** or press `Ctrl+Enter`

You should see a success message indicating all tables and policies were created.

### 4. Verify Database Setup

Check that all tables were created:

1. Go to **Table Editor** in the Supabase dashboard
2. You should see the following tables:
   - `users`
   - `sources`
   - `source_content`
   - `newsletters`
   - `newsletter_samples`
   - `feedback`
   - `trends`

### 5. Configure Authentication

1. Go to **Authentication** → **Providers**
2. Ensure **Email** provider is enabled (it should be by default)
3. Go to **Authentication** → **Settings**
4. Configure the following:

   **Site URL**: `http://localhost:5173` (for development)
   
   **Redirect URLs**: Add the following:
   - `http://localhost:5173/**`
   - Your production URL when ready

5. **Email Templates** (Optional for MVP):
   - You can customize the confirmation and password reset emails
   - For MVP, you can disable email confirmation

6. **Disable Email Confirmation** (Optional for faster MVP testing):
   - Go to **Authentication** → **Settings**
   - Scroll to **Email Auth**
   - Toggle off **"Enable email confirmations"**
   - ⚠️ Re-enable this for production!

### 6. Set Up Row Level Security (RLS)

RLS is already configured in the `database_schema.sql` file. To verify:

1. Go to **Authentication** → **Policies**
2. Select each table and verify policies exist
3. Example policies you should see:
   - Users can view their own data
   - Users can insert/update/delete their own sources
   - Users can view content from their sources

### 7. Update Backend Environment Variables

Add your Supabase credentials to `backend/.env`:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_anon_public_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

## Database Schema Overview

### Tables

#### `users`
Stores user account information and preferences.
- `id` (UUID, Primary Key)
- `email` (VARCHAR, Unique)
- `password_hash` (VARCHAR)
- `full_name` (VARCHAR, Optional)
- `is_active` (BOOLEAN)
- `voice_profile` (JSONB) - Stores writing style analysis
- `preferences` (JSONB) - User preferences
- `created_at`, `updated_at` (TIMESTAMP)

#### `sources`
Stores connected content sources (Twitter, YouTube, RSS).
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key → users)
- `source_type` (VARCHAR) - 'twitter', 'youtube', or 'rss'
- `name` (VARCHAR) - Display name
- `url` (TEXT, Optional)
- `credentials` (JSONB) - OAuth tokens, API keys
- `status` (VARCHAR) - 'active', 'error', or 'pending'
- `last_crawled_at` (TIMESTAMP)
- `error_message` (TEXT)
- `created_at`, `updated_at` (TIMESTAMP)

#### `source_content`
Cache of content fetched from sources.
- `id` (UUID, Primary Key)
- `source_id` (UUID, Foreign Key → sources)
- `content_type` (VARCHAR)
- `title` (TEXT)
- `content` (TEXT)
- `url` (TEXT)
- `metadata` (JSONB)
- `published_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)

#### `newsletters`
Stores newsletter drafts and sent newsletters.
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key → users)
- `title` (VARCHAR)
- `content` (TEXT)
- `status` (VARCHAR) - 'draft', 'sent', or 'scheduled'
- `sent_at` (TIMESTAMP)
- `metadata` (JSONB)
- `created_at`, `updated_at` (TIMESTAMP)

#### `newsletter_samples`
User-uploaded newsletters for voice training.
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key → users)
- `title` (VARCHAR, Optional)
- `content` (TEXT)
- `created_at` (TIMESTAMP)

#### `feedback`
User feedback on newsletter drafts (thumbs up/down).
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key → users)
- `newsletter_id` (UUID, Foreign Key → newsletters)
- `feedback_type` (VARCHAR) - 'thumbs_up' or 'thumbs_down'
- `section_id` (VARCHAR, Optional)
- `comment` (TEXT, Optional)
- `created_at` (TIMESTAMP)

#### `trends`
Detected trending topics.
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key → users)
- `topic` (VARCHAR)
- `score` (FLOAT)
- `sources` (JSONB)
- `detected_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)

### Indexes

The schema includes indexes on frequently queried columns:
- User ID foreign keys
- Status fields
- Timestamp fields (for sorting)

### Triggers

- `update_updated_at_column`: Automatically updates the `updated_at` field on row updates

## Testing the Database

### Test Database Connection

Run this in the Supabase SQL Editor:

```sql
SELECT 
  tablename 
FROM 
  pg_tables 
WHERE 
  schemaname = 'public'
ORDER BY 
  tablename;
```

You should see all 7 tables listed.

### Test RLS Policies

```sql
-- Check policies on users table
SELECT 
  schemaname, 
  tablename, 
  policyname, 
  permissive, 
  roles, 
  cmd 
FROM 
  pg_policies 
WHERE 
  tablename = 'users';
```

## Common Issues & Solutions

### Issue: "permission denied for table"

**Solution**: RLS is enabled but policies aren't working correctly.
- Re-run the RLS policy section of `database_schema.sql`
- Ensure you're using the correct authentication method

### Issue: "relation does not exist"

**Solution**: Table wasn't created.
- Re-run the entire `database_schema.sql`
- Check for SQL syntax errors in the output

### Issue: "duplicate key value violates unique constraint"

**Solution**: Trying to insert duplicate data.
- Check if data already exists
- Use `ON CONFLICT` clauses in your queries

### Issue: Can't connect from backend

**Solution**: Check credentials and network.
- Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Check if Supabase project is active (not paused)
- Verify network connectivity

## Database Maintenance

### Backup

Supabase automatically backs up your database daily on the free tier.

To create a manual backup:
1. Go to **Database** → **Backups**
2. Click **"Create backup"**

### Monitoring

Monitor database usage:
1. Go to **Database** → **Usage**
2. Check:
   - Database size
   - Number of rows
   - API requests
   - Bandwidth usage

### Migrations (Future)

For schema changes after initial setup:
1. Create migration files in `backend/migrations/`
2. Use Alembic or Supabase migrations
3. Test in development before applying to production

## Security Best Practices

1. **Never expose `service_role` key** in client-side code
2. **Use RLS policies** for all tables with user data
3. **Validate input** in your backend before database operations
4. **Rotate keys** if they're accidentally exposed
5. **Monitor logs** for suspicious activity
6. **Use prepared statements** to prevent SQL injection
7. **Limit API key permissions** where possible

## Production Considerations

Before going to production:

1. **Enable email confirmation** for new users
2. **Set up custom SMTP** for branded emails
3. **Configure proper redirect URLs**
4. **Set up database backups** (automatic on paid plans)
5. **Monitor database size** and upgrade plan if needed
6. **Set up alerts** for errors and unusual activity
7. **Review and tighten RLS policies**
8. **Enable SSL** for all connections (enabled by default)

## Useful SQL Queries

### Count users
```sql
SELECT COUNT(*) FROM users;
```

### View recent newsletters
```sql
SELECT 
  n.id,
  n.title,
  n.status,
  u.email,
  n.created_at
FROM 
  newsletters n
JOIN 
  users u ON n.user_id = u.id
ORDER BY 
  n.created_at DESC
LIMIT 10;
```

### Check source status
```sql
SELECT 
  s.name,
  s.source_type,
  s.status,
  s.last_crawled_at,
  u.email
FROM 
  sources s
JOIN 
  users u ON s.user_id = u.id
ORDER BY 
  s.last_crawled_at DESC;
```

### Feedback summary
```sql
SELECT 
  feedback_type,
  COUNT(*) as count
FROM 
  feedback
GROUP BY 
  feedback_type;
```

## Next Steps

After setting up Supabase:

1. ✅ Database schema is ready
2. ✅ Authentication is configured
3. ✅ RLS policies are in place
4. → Start the backend server
5. → Test API endpoints
6. → Begin Phase 2 implementation

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Supabase Auth Guide](https://supabase.com/docs/guides/auth)

---

**Need Help?**
- Supabase Discord: [https://discord.supabase.com](https://discord.supabase.com)
- Supabase Support: support@supabase.com
