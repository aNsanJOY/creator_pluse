# Single Save Button for Preferences Update

## Overview
Implemented a single "Save Changes" button for all preference settings in the Profile page, replacing the previous auto-save behavior where each field update immediately saved to the backend.

## Changes Made

### User Experience Improvements

**Before:**
- Each preference field change triggered an immediate API call
- Multiple API requests when changing several settings
- No way to preview changes before saving
- No way to discard changes

**After:**
- All changes are tracked locally without immediate saves
- Single "Save Changes" button appears when there are unsaved changes
- Ability to discard all unsaved changes
- Batch update - all changes saved in one API call
- Visual indicator (pulsing dot) shows unsaved changes
- Sticky save button stays visible while scrolling

## Implementation Details

### New State Variables
```typescript
const [localPreferences, setLocalPreferences] = useState<UserPreferences | null>(null);
const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
```

### New Functions

#### `handleLocalPreferenceChange(updates: PreferencesUpdate)`
- Updates local state without saving to backend
- Merges updates with existing local preferences
- Sets `hasUnsavedChanges` flag to true

#### `handleSavePreferences()`
- Saves all local changes to backend via API
- Updates both `preferences` and `localPreferences` states
- Resets `hasUnsavedChanges` flag
- Shows success/error toast

#### `handleDiscardChanges()`
- Reverts local changes to last saved state
- Resets `hasUnsavedChanges` flag

### Updated Sections

All preference sections now use `localPreferences` and `handleLocalPreferenceChange`:

1. **Schedule & Frequency**
   - Draft Generation Time
   - Newsletter Frequency

2. **Tone & Style Preferences**
   - Use Voice Profile toggle
   - Formality Level
   - Enthusiasm Level
   - Content Length
   - Use Emojis

3. **Notifications**
   - Email on draft ready
   - Email on publish success
   - Email on errors
   - Weekly summary

4. **Email Settings**
   - Default Subject Template
   - Include Preview Text
   - Track Opens
   - Track Clicks

### Save Changes UI

The save button appears as a sticky card at the bottom when there are unsaved changes:

```tsx
{hasUnsavedChanges && (
  <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-300 sticky bottom-4 shadow-lg z-10">
    <CardContent className="py-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
          <p className="text-sm font-medium text-gray-900">
            You have unsaved changes
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handleDiscardChanges}>
            Discard
          </Button>
          <Button onClick={handleSavePreferences}>
            {isUpdatingPreferences ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>
    </CardContent>
  </Card>
)}
```

## Benefits

1. **Better Performance**
   - Reduces API calls from multiple to single batch update
   - Less network traffic and server load

2. **Improved UX**
   - Users can make multiple changes before committing
   - Clear visual feedback for unsaved changes
   - Ability to discard unwanted changes
   - Prevents accidental saves

3. **More Control**
   - Users decide when to save
   - Can review all changes before applying
   - Sticky button always accessible

4. **Consistency**
   - All preference sections follow the same pattern
   - Unified save mechanism

## Testing

To test the new functionality:

1. Navigate to Profile page
2. Make changes to any preference fields
3. Verify the "Save Changes" button appears at the bottom
4. Make more changes across different sections
5. Click "Discard" - all changes should revert
6. Make changes again
7. Click "Save Changes" - all changes should be saved
8. Refresh the page - changes should persist
9. Verify the Quick Settings Overview updates in real-time as you make changes

## Migration Notes

- No database changes required
- No API changes required
- Frontend-only update
- Backward compatible with existing preferences API
