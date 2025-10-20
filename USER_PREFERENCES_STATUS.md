# User Preferences Integration Status

## Overview
This document tracks which parts of the CreatorPulse application respect user preferences from the `users.preferences` JSONB column.

## Preferences Structure
```json
{
  "tone_preferences": {
    "formality": "balanced",
    "enthusiasm": "moderate",
    "use_emojis": true,
    "length_preference": "medium"
  },
  "email_preferences": {
    "track_opens": false,
    "track_clicks": false,
    "include_preview_text": true,
    "default_subject_template": "{title} - Newsletter"
  },
  "use_voice_profile": true,
  "draft_schedule_time": "08:00",
  "newsletter_frequency": "daily",
  "notification_preferences": {
    "weekly_summary": false,
    "email_on_errors": false,
    "email_on_draft_ready": false,
    "email_on_publish_success": true
  }
}
```

## ✅ Currently Implemented

### 1. **Draft Generation** (`/api/drafts/generate`)
- ✅ Fetches user preferences from `users.preferences`
- ✅ Passes preferences to `draft_generator._generate_draft_content()`
- ✅ Applies `tone_preferences` (formality, enthusiasm, length, emojis)
- ✅ Respects `use_voice_profile` setting
- ✅ Uses `PreferencesService.build_tone_prompt()` to apply tone settings

**Files:**
- `backend/app/api/routes/drafts.py` (lines 156-204)
- `backend/app/services/draft_generator.py` (lines 260-340)
- `backend/app/services/preferences_service.py` (lines 168-218)

### 2. **Draft Regeneration** (`/api/drafts/{draft_id}/regenerate`)
- ✅ Fetches user preferences from `users.preferences`
- ✅ Passes preferences to `draft_generator._generate_draft_content()`
- ✅ Applies tone and voice profile settings

**Files:**
- `backend/app/api/routes/drafts.py` (lines 522-569)

### 3. **Draft Scheduler** (`draft_scheduler.py`)
- ✅ Uses `PreferencesService` to fetch preferences
- ✅ Respects `draft_schedule_time` for scheduling
- ✅ Respects `newsletter_frequency` (daily/weekly)
- ✅ Checks `notification_preferences.email_on_draft_ready` before sending notifications
- ✅ Checks `notification_preferences.email_on_errors` before sending error notifications

**Files:**
- `backend/app/services/draft_scheduler.py` (lines 66-193)

### 4. **PreferencesService**
- ✅ Fetches from `users.preferences` JSONB column
- ✅ Merges with defaults for missing values
- ✅ Provides `build_tone_prompt()` for LLM instructions
- ✅ Provides `get_voice_profile()` with preference check

**Files:**
- `backend/app/services/preferences_service.py` (all)

## ❌ Missing Implementations

### 1. **Email Service** (`email_service.py`)
**Missing:**
- ❌ Does NOT respect `email_preferences.default_subject_template`
- ❌ Does NOT respect `email_preferences.include_preview_text`
- ❌ Does NOT respect `email_preferences.track_opens`
- ❌ Does NOT respect `email_preferences.track_clicks`
- ❌ Does NOT check `notification_preferences.email_on_publish_success`

**Current Behavior:**
- Uses hardcoded subject from request or draft title
- No preview text implementation
- No tracking pixel/link implementation
- Sends notifications without checking preferences

**Files Needing Updates:**
- `backend/app/services/email_service.py` (lines 213-354, 356-442)

### 2. **Publish Draft Endpoint** (`/api/drafts/{draft_id}/publish`)
**Missing:**
- ❌ Does NOT fetch user preferences
- ❌ Does NOT apply `email_preferences.default_subject_template`
- ❌ Does NOT check `notification_preferences.email_on_publish_success`

**Current Behavior:**
- Uses subject from request or draft title directly
- Sends email without checking notification preferences

**Files Needing Updates:**
- `backend/app/api/routes/drafts.py` (lines 641-714)

### 3. **Draft Notification** (`send_draft_notification`)
**Missing:**
- ❌ Does NOT check `notification_preferences.email_on_draft_ready` before sending

**Current Behavior:**
- Always sends notification when called
- Preference check happens in scheduler, but not in the service itself

**Files Needing Updates:**
- `backend/app/services/email_service.py` (lines 356-442)

## 🔧 Required Changes

### Priority 1: Email Service Updates

#### A. Add Preferences to `send_newsletter()`
```python
async def send_newsletter(
    self,
    draft_id: str,
    subject: str,
    recipients: List[str],
    user_id: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    # Fetch user preferences
    from app.services.preferences_service import PreferencesService
    preferences_service = PreferencesService(self.supabase)
    preferences = await preferences_service.get_preferences(user_id)
    
    email_prefs = preferences.get("email_preferences", {})
    
    # Apply subject template if not provided
    if not subject or subject == draft["title"]:
        template = email_prefs.get("default_subject_template", "{title} - Newsletter")
        subject = template.replace("{title}", draft["title"])
    
    # Add tracking if enabled
    track_opens = email_prefs.get("track_opens", False)
    track_clicks = email_prefs.get("track_clicks", False)
    
    # Generate HTML with tracking
    html_content = self._draft_to_html(
        draft, 
        user_id, 
        track_opens=track_opens, 
        track_clicks=track_clicks
    )
```

#### B. Add Preferences to `send_draft_notification()`
```python
async def send_draft_notification(
    self,
    draft_id: str,
    user_email: str,
    user_id: str
) -> bool:
    # Check notification preferences
    from app.services.preferences_service import PreferencesService
    preferences_service = PreferencesService(self.supabase)
    preferences = await preferences_service.get_preferences(user_id)
    
    notification_prefs = preferences.get("notification_preferences", {})
    if not notification_prefs.get("email_on_draft_ready", True):
        logger.info(f"Draft notification disabled for user {user_id}")
        return False
    
    # Continue with sending...
```

### Priority 2: Publish Draft Endpoint

#### Update `publish_draft()` to respect preferences
```python
@router.post("/{draft_id}/publish")
async def publish_draft(...):
    # Fetch user preferences
    from app.services.preferences_service import PreferencesService
    preferences_service = PreferencesService(supabase)
    preferences = await preferences_service.get_preferences(user_id)
    
    # Check if publish notification is enabled
    notification_prefs = preferences.get("notification_preferences", {})
    should_notify = notification_prefs.get("email_on_publish_success", True)
    
    # Apply email preferences
    email_prefs = preferences.get("email_preferences", {})
    if not subject:
        template = email_prefs.get("default_subject_template", "{title} - Newsletter")
        subject = template.replace("{title}", draft["title"])
    
    # Send email with preferences
    if request.send_email and should_notify:
        # ... send email
```

### Priority 3: Email Tracking Implementation

#### Add tracking pixels and link wrapping
- Implement open tracking with 1x1 pixel
- Implement click tracking by wrapping links
- Store tracking events in database
- Respect `track_opens` and `track_clicks` preferences

## Summary

### What's Working ✅
1. Draft generation respects tone preferences and voice profile
2. Draft scheduler respects schedule time and frequency
3. Draft scheduler checks notification preferences
4. PreferencesService properly fetches from users table

### What Needs Work ❌
1. Email service doesn't apply email preferences (subject template, tracking)
2. Publish endpoint doesn't check notification preferences
3. Email service doesn't check notification preferences internally
4. No tracking implementation for opens/clicks

### Estimated Work
- **Email Service Updates**: 2-3 hours
- **Publish Endpoint Updates**: 30 minutes
- **Tracking Implementation**: 3-4 hours
- **Testing**: 1-2 hours

**Total**: ~7-10 hours of development work
