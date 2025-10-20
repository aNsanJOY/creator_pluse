# User Preferences System

## Overview
The user preferences system allows users to customize their newsletter generation experience. Preferences are stored in the `users.preferences` JSONB field in the database and can be managed through the Profile page.

## Database Schema

### Users Table
The `users` table includes a `preferences` JSONB column:

```sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    voice_profile JSONB,
    preferences JSONB DEFAULT '{}',  -- User preferences stored here
    reset_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Preference Categories

### 1. Schedule & Frequency
- **draft_schedule_time**: Time when daily drafts are generated (format: "HH:MM")
  - Default: "09:00"
- **newsletter_frequency**: How often newsletters are sent
  - Options: "daily", "weekly", "custom"
  - Default: "weekly"

### 2. Tone Preferences
- **formality**: Writing style formality level
  - Options: "casual", "balanced", "formal"
  - Default: "balanced"
- **enthusiasm**: Energy level of the content
  - Options: "low", "moderate", "high"
  - Default: "moderate"
- **length_preference**: Preferred content length
  - Options: "short", "medium", "long"
  - Default: "medium"
- **use_emojis**: Whether to include emojis in content
  - Type: boolean
  - Default: true

### 3. Notification Preferences
- **email_on_draft_ready**: Send email when draft is ready
  - Default: true
- **email_on_publish_success**: Send email when newsletter is published
  - Default: true
- **email_on_errors**: Send email when errors occur
  - Default: true
- **weekly_summary**: Send weekly performance summary
  - Default: false

### 4. Email Preferences
- **default_subject_template**: Template for email subject lines
  - Default: "{title} - Weekly Newsletter"
  - Supports {title} placeholder
- **include_preview_text**: Show preview text in email clients
  - Default: true
- **track_opens**: Track when recipients open emails
  - Default: false
- **track_clicks**: Track link clicks in emails
  - Default: false

## API Endpoints

### GET /api/user/preferences
Get user preferences

**Response:**
```json
{
  "draft_schedule_time": "09:00",
  "newsletter_frequency": "weekly",
  "tone_preferences": {
    "formality": "balanced",
    "enthusiasm": "moderate",
    "length_preference": "medium",
    "use_emojis": true
  },
  "notification_preferences": {
    "email_on_draft_ready": true,
    "email_on_publish_success": true,
    "email_on_errors": true,
    "weekly_summary": false
  },
  "email_preferences": {
    "default_subject_template": "{title} - Weekly Newsletter",
    "include_preview_text": true,
    "track_opens": false,
    "track_clicks": false
  }
}
```

### PATCH /api/user/preferences
Update user preferences (partial update)

**Request Body:**
```json
{
  "draft_schedule_time": "10:00",
  "tone_preferences": {
    "formality": "casual"
  }
}
```

**Response:** Updated preferences object

### POST /api/user/preferences/reset
Reset all preferences to defaults

**Response:** Default preferences object

## Frontend Implementation

### Service Layer
Location: `frontend/src/services/preferences.service.ts`

```typescript
import preferencesService from '../services/preferences.service';

// Get preferences
const prefs = await preferencesService.getPreferences();

// Update preferences
const updated = await preferencesService.updatePreferences({
  draft_schedule_time: "10:00"
});

// Reset preferences
const defaults = await preferencesService.resetPreferences();
```

### UI Components
Location: `frontend/src/pages/Profile.tsx`

The Profile page includes:
- **Quick Settings Overview**: Visual summary of key preferences
- **Schedule & Frequency Card**: Time and frequency settings
- **Tone & Style Card**: Writing style preferences
- **Notifications Card**: Email notification settings
- **Email Settings Card**: Email template and tracking options
- **Reset Button**: Reset all preferences to defaults

### Toast Notifications
All preference updates show toast notifications:
- ✅ Success: "Preferences Updated - Your settings have been saved successfully."
- ❌ Error: "Update Failed - Failed to update preferences"
- 🔄 Reset: "Preferences Reset - All preferences have been reset to their default values."

## Usage in Draft Generation

The preferences are used during draft generation to customize:

1. **Scheduling**: `draft_schedule_time` determines when daily drafts are generated
2. **Tone**: `tone_preferences` guide the LLM to write in the preferred style
3. **Notifications**: `notification_preferences` control email alerts
4. **Email Templates**: `email_preferences` customize newsletter emails

### Example: Using Preferences in Draft Generation

```python
from app.core.database import get_db_connection

def get_user_preferences(user_id: str) -> dict:
    """Get user preferences from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT preferences FROM users WHERE id = %s",
        (user_id,)
    )
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return result[0] if result and result[0] else {}

# Use in draft generation
user_prefs = get_user_preferences(user_id)
tone = user_prefs.get('tone_preferences', {})

# Customize LLM prompt based on preferences
prompt = f"""
Write a newsletter in a {tone.get('formality', 'balanced')} tone
with {tone.get('enthusiasm', 'moderate')} enthusiasm.
Keep it {tone.get('length_preference', 'medium')} length.
{"Use emojis where appropriate." if tone.get('use_emojis', True) else ""}
"""
```

## Default Values

All preferences have sensible defaults that are applied when:
- User hasn't set preferences yet
- Preference fields are missing
- User resets preferences

The defaults are defined in:
- Backend: `backend/app/api/routes/preferences.py` (DEFAULT_PREFERENCES)
- Frontend: `frontend/src/services/preferences.service.ts` (DEFAULT_PREFERENCES)

## Migration Notes

No database migration is needed as the `preferences` JSONB field already exists in the `users` table. The field defaults to an empty object `{}` and is populated on first use.

## Testing

### Manual Testing
1. Navigate to `/profile` in the frontend
2. Modify any preference setting
3. Verify toast notification appears
4. Refresh the page - settings should persist
5. Click "Reset to Defaults" - verify all settings reset

### API Testing
```bash
# Get preferences
curl -X GET http://localhost:8000/api/user/preferences \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update preferences
curl -X PATCH http://localhost:8000/api/user/preferences \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"draft_schedule_time": "10:00"}'

# Reset preferences
curl -X POST http://localhost:8000/api/user/preferences/reset \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Future Enhancements

Potential improvements:
1. **Preference Validation**: Add stricter validation for time formats and enum values
2. **Preference History**: Track preference changes over time
3. **A/B Testing**: Test different preference combinations for engagement
4. **Smart Defaults**: Learn optimal preferences based on user behavior
5. **Preference Templates**: Pre-configured preference sets for different use cases
6. **Import/Export**: Allow users to backup and restore preferences
