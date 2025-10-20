# Use Voice Profile Implementation - Users Table Storage

## Overview
Implemented storage and retrieval of the "Use Voice Profile" switch control state directly in the `users` table as a dedicated column, rather than in the `preferences` JSONB field. This setting is used throughout the application during draft generation.

## Database Changes

### Migration: `009_add_use_voice_profile_column.sql`
```sql
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS use_voice_profile BOOLEAN DEFAULT FALSE;

-- Auto-enable for users who already have voice profiles
UPDATE users 
SET use_voice_profile = TRUE 
WHERE voice_profile IS NOT NULL AND voice_profile != 'null'::jsonb;
```

### Schema
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    voice_profile JSONB,              -- Analyzed voice profile data
    use_voice_profile BOOLEAN DEFAULT FALSE,  -- ← NEW: Switch control state
    preferences JSONB DEFAULT '{}',   -- Other preferences
    -- ... other fields
);
```

## Backend Implementation

### 1. User API Route (`backend/app/api/routes/user.py`)

**New Endpoint:**
```python
@router.patch("/voice-profile-preference")
async def update_voice_profile_preference(
    use_voice_profile: bool,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Update whether to use voice profile or tone preferences"""
    result = supabase.table("users").update({
        "use_voice_profile": use_voice_profile,
        "updated_at": "now()"
    }).eq("id", current_user["id"]).execute()
    
    return {
        "success": True,
        "use_voice_profile": use_voice_profile,
        "message": f"Voice profile preference updated"
    }
```

### 2. Draft Generation API (`backend/app/api/routes/drafts.py`)

**Updated Logic:**
```python
# In generate_draft endpoint
user_result = supabase.table("users").select("use_voice_profile").eq("id", user_id).execute()
use_voice = request.use_voice_profile  # Default to request value
if user_result.data and len(user_result.data) > 0:
    # Use the user's saved preference if available
    use_voice = user_result.data[0].get("use_voice_profile", request.use_voice_profile)

# Get voice profile if enabled
voice_profile = None
if use_voice:
    voice_profile = await draft_generator._get_voice_profile(user_id)
```

**Applied to:**
- `POST /drafts/generate` - Generate new draft
- `POST /drafts/{draft_id}/regenerate` - Regenerate draft

### 3. Draft Scheduler (`backend/app/services/draft_scheduler.py`)

**Updated Logic:**
```python
# Get use_voice_profile from users table
user_result = self.supabase.table("users").select("use_voice_profile").eq("id", user_id).execute()
use_voice = False  # Default
if user_result.data and len(user_result.data) > 0:
    use_voice = user_result.data[0].get("use_voice_profile", False)

# Generate draft with user's preference
draft = await draft_generator.generate_draft(
    user_id=user_id,
    topic_count=preferences.get("topic_count", 5),
    days_back=preferences.get("days_back", 7),
    use_voice_profile=use_voice  # ← From users table
)
```

## Frontend Implementation

### 1. User Service (`frontend/src/services/user.service.ts`)

**New Method:**
```typescript
async updateVoiceProfilePreference(useVoiceProfile: boolean): Promise<{
  success: boolean;
  use_voice_profile: boolean;
  message: string;
}> {
  const response = await apiClient.patch(
    '/api/user/voice-profile-preference',
    null,
    { params: { use_voice_profile: useVoiceProfile } }
  );
  return response.data;
}
```

### 2. User Interface (`frontend/src/services/auth.service.ts`)

**Updated User Type:**
```typescript
export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  voice_profile?: any;           // Voice profile data
  use_voice_profile?: boolean;   // ← NEW: Switch state
}
```

### 3. Profile Page (`frontend/src/pages/Profile.tsx`)

**Switch Control:**
```tsx
<input
  id="useVoiceProfile"
  type="checkbox"
  checked={user?.use_voice_profile || false}  // ← Read from user object
  onChange={async (e) => {
    try {
      setIsUpdatingPreferences(true);
      await userService.updateVoiceProfilePreference(e.target.checked);
      await refreshUser();  // Refresh user data
      addToast({
        type: "success",
        title: "Voice Profile Preference Updated",
        message: e.target.checked
          ? "Drafts will use your voice profile"
          : "Drafts will use tone preferences",
      });
    } catch (error: any) {
      addToast({
        type: "error",
        title: "Update Failed",
        message: error.message || "Failed to update preference",
      });
    } finally {
      setIsUpdatingPreferences(false);
    }
  }}
  disabled={isUpdatingPreferences || !user?.voice_profile}
/>
```

**Visual Feedback:**
```tsx
{/* Show active mode */}
{user?.use_voice_profile && user?.voice_profile && (
  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
    <p className="text-sm text-blue-800">
      ✓ Drafts will be generated using your unique writing voice profile
    </p>
  </div>
)}

{/* Disable tone preferences when voice profile is active */}
<div className={user?.use_voice_profile ? "opacity-50 pointer-events-none" : ""}>
  {/* Tone preference controls */}
</div>
```

## Data Flow

### 1. User Toggles Switch
```
User clicks switch
  ↓
Frontend: userService.updateVoiceProfilePreference(true/false)
  ↓
Backend: PATCH /api/user/voice-profile-preference
  ↓
Database: UPDATE users SET use_voice_profile = ? WHERE id = ?
  ↓
Frontend: refreshUser() - Get updated user data
  ↓
UI: Switch reflects new state
```

### 2. Draft Generation
```
User requests draft generation
  ↓
Backend: POST /drafts/generate
  ↓
Query: SELECT use_voice_profile FROM users WHERE id = ?
  ↓
If use_voice_profile = TRUE:
  - Fetch voice_profile from users table
  - Generate draft using voice profile
Else:
  - Use tone_preferences from preferences JSONB
  - Generate draft using tone preferences
```

### 3. Scheduled Draft Generation
```
Scheduler runs at 8:00 AM
  ↓
For each active user:
  ↓
Query: SELECT use_voice_profile FROM users WHERE id = ?
  ↓
Generate draft with appropriate method
```

## Storage Location Comparison

### Before (JSONB):
```json
users.preferences = {
  "use_voice_profile": true,  // ← Stored in JSONB
  "tone_preferences": { ... },
  "notification_preferences": { ... }
}
```

### After (Dedicated Column):
```sql
users.use_voice_profile = TRUE  -- ← Dedicated column
users.preferences = {
  "tone_preferences": { ... },
  "notification_preferences": { ... }
}
```

## Benefits of Dedicated Column

1. **Direct Access**: No JSON parsing required
2. **Database Indexing**: Can create index for faster queries
3. **Type Safety**: Boolean type enforced at database level
4. **Simpler Queries**: Direct column access vs JSON path
5. **Performance**: Faster reads during draft generation
6. **Clarity**: Clear separation of critical vs optional preferences

## Usage Across Application

### Where `use_voice_profile` is Read:

1. **Draft Generation API** (`drafts.py`)
   - Manual draft generation
   - Draft regeneration

2. **Draft Scheduler** (`draft_scheduler.py`)
   - Scheduled daily drafts

3. **Profile Page** (`Profile.tsx`)
   - Display current state
   - Visual feedback

### Query Pattern:
```python
# Consistent pattern across all locations
user_result = supabase.table("users").select("use_voice_profile").eq("id", user_id).execute()
use_voice = user_result.data[0].get("use_voice_profile", False)
```

## Testing

### Manual Testing Steps:

1. **Initial State**
   - New user: `use_voice_profile` = FALSE
   - User with voice profile: Auto-set to TRUE (by migration)

2. **Toggle Switch**
   - Turn ON → Verify database updated
   - Turn OFF → Verify database updated
   - Refresh page → Verify state persists

3. **Draft Generation**
   - With switch ON → Verify uses voice profile
   - With switch OFF → Verify uses tone preferences
   - Check draft metadata for confirmation

4. **Scheduled Drafts**
   - Wait for scheduled time
   - Verify drafts respect user's setting

### Database Verification:
```sql
-- Check user's preference
SELECT id, email, use_voice_profile, voice_profile IS NOT NULL as has_profile
FROM users
WHERE id = 'user-uuid';

-- Check all users with voice profiles
SELECT COUNT(*) as total,
       SUM(CASE WHEN use_voice_profile THEN 1 ELSE 0 END) as using_voice
FROM users
WHERE voice_profile IS NOT NULL;
```

## Migration Notes

### Running the Migration:
```bash
# Apply migration
psql -d your_database -f backend/database_migrations/009_add_use_voice_profile_column.sql
```

### Rollback (if needed):
```sql
ALTER TABLE users DROP COLUMN IF EXISTS use_voice_profile;
```

### Data Migration:
The migration automatically sets `use_voice_profile = TRUE` for users who already have a `voice_profile`. This ensures existing users with voice profiles continue to use them by default.

## API Documentation

### Endpoint: Update Voice Profile Preference

**Request:**
```http
PATCH /api/user/voice-profile-preference?use_voice_profile=true
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "use_voice_profile": true,
  "message": "Voice profile preference updated to: enabled"
}
```

### Endpoint: Get User Profile

**Request:**
```http
GET /api/user/profile
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "use_voice_profile": true,  // ← Included in response
  "voice_profile": { ... },
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Summary

✅ **Implemented dedicated `use_voice_profile` column in users table**
✅ **Created migration to add column and set defaults**
✅ **Updated all draft generation code to read from users table**
✅ **Created API endpoint to update the preference**
✅ **Updated frontend to use the new endpoint**
✅ **Added proper type definitions**
✅ **Implemented visual feedback in UI**
✅ **Applied consistently across scheduled and manual drafts**

The voice profile preference is now stored in a dedicated database column and used consistently throughout the application for all draft generation operations!
