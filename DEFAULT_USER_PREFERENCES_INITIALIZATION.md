# Default User Preferences Initialization - Implementation Summary

## Overview
Implemented automatic initialization of user preferences with default values when creating a new user account. This ensures all new users have a complete set of preferences from the start, improving the user experience and preventing null/undefined errors.

## Changes Made

### 1. Backend - Auth Routes (`backend/app/api/routes/auth.py`)

#### Added Default Preferences Constant
```python
# Default preferences for new users
DEFAULT_USER_PREFERENCES = {
    "draft_schedule_time": "09:00",
    "newsletter_frequency": "weekly",
    "tone_preferences": {
        "formality": "balanced",
        "enthusiasm": "moderate",
        "length_preference": "medium",
        "use_emojis": True
    },
    "notification_preferences": {
        "email_on_draft_ready": True,
        "email_on_publish_success": True,
        "email_on_errors": True,
        "weekly_summary": False
    },
    "email_preferences": {
        "default_subject_template": "{title} - Weekly Newsletter",
        "include_preview_text": True,
        "track_opens": False,
        "track_clicks": False
    }
}
```

#### Updated Signup Function
**Before:**
```python
new_user = {
    "email": user_data.email,
    "full_name": user_data.full_name,
    "password_hash": hashed_password,
    "is_active": True
}
```

**After:**
```python
new_user = {
    "email": user_data.email,
    "full_name": user_data.full_name,
    "password_hash": hashed_password,
    "is_active": True,
    "preferences": DEFAULT_USER_PREFERENCES,  # ← Initialize with defaults
    "use_voice_profile": False  # ← Default to using tone preferences
}
```

#### Added User Crawl Schedule Initialization
```python
# Initialize user crawl schedule
try:
    supabase.table("user_crawl_schedule").insert({
        "user_id": user_id,
        "is_crawling": False,
        "crawl_frequency_hours": 24  # Default: daily crawls
    }).execute()
    logger.info(f"Initialized crawl schedule for new user {user_id}")
except Exception as e:
    # Don't fail signup if crawl schedule creation fails
    logger.warning(f"Failed to create crawl schedule for user {user_id}: {str(e)}")
```

#### Updated Documentation
```python
"""
Register a new user without email verification.
Creates user in database with default preferences and returns JWT token.

Default preferences include:
- Draft schedule time: 09:00
- Newsletter frequency: weekly
- Tone preferences: balanced formality, moderate enthusiasm
- Notification preferences: enabled for drafts and publishing
- Email preferences: default templates and tracking settings
"""
```

## Default Values Breakdown

### Draft Scheduling
- **draft_schedule_time**: `"09:00"` - Drafts generated at 9 AM
- **newsletter_frequency**: `"weekly"` - Weekly newsletter cadence

### Tone Preferences
- **formality**: `"balanced"` - Not too casual, not too formal
- **enthusiasm**: `"moderate"` - Balanced energy level
- **length_preference**: `"medium"` - Medium-length content
- **use_emojis**: `true` - Allow emojis in content

### Notification Preferences
- **email_on_draft_ready**: `true` - Notify when draft is ready
- **email_on_publish_success**: `true` - Notify when newsletter published
- **email_on_errors**: `true` - Notify on errors
- **weekly_summary**: `false` - No weekly summary emails (can be enabled)

### Email Preferences
- **default_subject_template**: `"{title} - Weekly Newsletter"`
- **include_preview_text**: `true` - Include preview text
- **track_opens**: `false` - Email open tracking disabled
- **track_clicks**: `false` - Link click tracking disabled

### Voice Profile
- **use_voice_profile**: `false` - Default to tone preferences until voice training completed

### Crawl Schedule
- **is_crawling**: `false` - Not actively crawling
- **crawl_frequency_hours**: `24` - Daily crawls (every 24 hours)

## User Flow

### New User Signup
```
1. User submits signup form
   ↓
2. Backend validates email (not already registered)
   ↓
3. Password is hashed
   ↓
4. User record created with:
   - Email, name, password hash
   - preferences: DEFAULT_USER_PREFERENCES ✅
   - use_voice_profile: false ✅
   ↓
5. User crawl schedule initialized ✅
   ↓
6. JWT token generated and returned
   ↓
7. User is logged in with full preferences ready!
```

### First Login Experience
```
User logs in
  ↓
Navigates to Profile page
  ↓
Sees preferences already populated with sensible defaults ✅
  ↓
Can customize as needed (optional)
  ↓
Can start using the app immediately!
```

## Benefits

### 1. **Better User Experience**
- ✅ No need to configure preferences before using the app
- ✅ Sensible defaults work for most users
- ✅ Can customize later if needed

### 2. **Prevents Errors**
- ✅ No null/undefined preference errors
- ✅ All code paths have valid preference values
- ✅ Graceful fallbacks already in place

### 3. **Consistency**
- ✅ All new users start with same baseline
- ✅ Easier to support and debug
- ✅ Predictable behavior

### 4. **Immediate Functionality**
- ✅ Draft generation works immediately
- ✅ Crawl scheduling works immediately
- ✅ Notifications work immediately

## Existing Safeguards

The codebase already had safeguards for missing preferences:

### Preferences API (`preferences.py`)
```python
# Get stored preferences or use defaults
stored_prefs = response.data[0].get("preferences") or {}

# Merge with defaults to ensure all fields exist
preferences = deep_merge(DEFAULT_PREFERENCES, stored_prefs)
```

### Draft Scheduler (`draft_scheduler.py`)
```python
async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
    """Get user's draft preferences with fallback to defaults"""
    try:
        result = self.supabase.table("users").select("preferences").eq(
            "id", user_id
        ).execute()
        
        if result.data and len(result.data) > 0:
            prefs = result.data[0].get("preferences", {})
            return prefs if prefs else self._get_default_preferences()
        
        return self._get_default_preferences()
    except Exception as e:
        logger.error(f"Error fetching user preferences: {str(e)}")
        return self._get_default_preferences()
```

These safeguards remain in place as a safety net, but now new users won't need them!

## Testing

### Test Case 1: New User Signup
1. Create a new account
2. Check database:
   ```sql
   SELECT 
     email,
     preferences,
     use_voice_profile
   FROM users
   WHERE email = 'newuser@example.com';
   ```
3. **Expected:**
   - `preferences` is populated with DEFAULT_USER_PREFERENCES
   - `use_voice_profile` is `false`

### Test Case 2: User Crawl Schedule
1. Create a new account
2. Check database:
   ```sql
   SELECT *
   FROM user_crawl_schedule
   WHERE user_id = 'new-user-id';
   ```
3. **Expected:**
   - Record exists
   - `is_crawling` is `false`
   - `crawl_frequency_hours` is `24`

### Test Case 3: Profile Page
1. Create new account
2. Log in
3. Navigate to Profile page
4. **Expected:**
   - All preference fields show default values
   - No errors or null values
   - Can modify preferences immediately

### Test Case 4: Draft Generation
1. Create new account
2. Add a source
3. Crawl content
4. Generate draft
5. **Expected:**
   - Draft uses tone preferences (default)
   - Scheduled time is 09:00
   - Frequency is weekly

## Database Schema

The `users` table should have:
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255),
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  preferences JSONB DEFAULT '{}'::jsonb,  -- Now initialized with defaults
  use_voice_profile BOOLEAN DEFAULT FALSE,  -- Now explicitly set
  voice_profile JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

The `user_crawl_schedule` table:
```sql
CREATE TABLE user_crawl_schedule (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  is_crawling BOOLEAN DEFAULT FALSE,
  crawl_frequency_hours INTEGER DEFAULT 24,  -- Now initialized on signup
  last_batch_crawl_at TIMESTAMPTZ,
  next_scheduled_crawl_at TIMESTAMPTZ,
  last_crawl_duration_seconds INTEGER,
  sources_crawled_count INTEGER DEFAULT 0,
  sources_failed_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);
```

## Summary

✅ **New users** are initialized with complete, sensible default preferences
✅ **User crawl schedule** is created automatically on signup
✅ **use_voice_profile** is explicitly set to `false` (use tone preferences)
✅ **Documentation** updated to reflect new behavior
✅ **Existing safeguards** remain in place for backwards compatibility
✅ **Better UX** - users can start using the app immediately

All new users now have a complete, working configuration from the moment they sign up! 🎉
