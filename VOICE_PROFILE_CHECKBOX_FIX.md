# Voice Profile Checkbox Update Fix

## Problem
The "Use Voice Profile" checkbox in the Profile page was not updating correctly after toggling. The checkbox state wasn't reflecting the change after API calls.

## Root Causes
1. **Non-existent API endpoint**: The frontend was initially calling `/api/user/voice-profile-preference` which didn't exist
2. **Wrong data source**: The checkbox was bound to `preferences?.use_voice_profile`, but the code was calling `refreshUser()` instead of reloading preferences
3. **Incorrect service usage**: Using `userService.updateVoiceProfilePreference()` instead of the preferences API
4. **Database schema inconsistency**: `use_voice_profile` existed as both a database column (from migration 009) AND in the preferences JSONB, causing conflicts

## Solution

### Backend Changes

#### 1. Updated `backend/app/api/routes/preferences.py`
- Added `use_voice_profile` field to `UserPreferences` model
- Added `use_voice_profile` field to `PreferencesUpdate` model
- Added `use_voice_profile: False` to `DEFAULT_PREFERENCES`
- Added handling for `use_voice_profile` in the update logic

This ensures that the voice profile preference is properly managed through the preferences API.

### Frontend Changes

#### 1. Updated `frontend/src/pages/Profile.tsx`
Changed the checkbox `onChange` handler from:
```typescript
await userService.updateVoiceProfilePreference(e.target.checked);
await refreshUser();
```

To:
```typescript
const updatedPrefs = await preferencesService.updatePreferences({
  use_voice_profile: e.target.checked
});
setPreferences(updatedPrefs);
```

This ensures:
- The correct API endpoint is called (`/api/preferences`)
- The local preferences state is updated with the response
- The checkbox reflects the new state immediately

#### 2. Updated `frontend/src/services/user.service.ts`
- Removed the unused `updateVoiceProfilePreference()` method

#### 3. Updated `frontend/src/services/preferences.service.ts`
- Already had `use_voice_profile` field in the `UserPreferences` interface (user had added this)

## How It Works Now

1. User toggles the "Use Voice Profile" checkbox
2. Frontend calls `PATCH /api/preferences` with `{ use_voice_profile: true/false }`
3. Backend updates the `users.preferences` JSONB field
4. Backend returns the updated preferences
5. Frontend updates local state with `setPreferences(updatedPrefs)`
6. Checkbox UI updates immediately to reflect the new state

## Database Migration
Created migration `010_migrate_use_voice_profile_to_preferences.sql` to:
- Move `use_voice_profile` data from column to preferences JSONB
- Drop the `use_voice_profile` column
- Ensure all preferences are stored in one place

See `USE_VOICE_PROFILE_MIGRATION.md` for detailed migration instructions.

## Testing
To verify the fix:
1. Run the database migration (see USE_VOICE_PROFILE_MIGRATION.md)
2. Navigate to Profile page
3. Toggle the "Use Voice Profile" checkbox
4. Verify the checkbox state updates correctly
5. Verify the success toast appears
6. Refresh the page and confirm the checkbox maintains its state
7. Verify draft generation respects the preference
