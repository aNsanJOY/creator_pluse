# User Preferences Integration Plan

## Overview
This document outlines how the entire CreatorPulse application should respect user preferences set in the Profile page. All backend services, schedulers, draft generation, and notification systems must honor these settings.

## User Preference Categories

### 1. Schedule & Frequency Settings
```typescript
{
  draft_schedule_time: string;        // e.g., "09:00" (24-hour format)
  newsletter_frequency: "daily" | "weekly" | "custom";
}
```

### 2. Tone & Style Preferences
```typescript
{
  tone_preferences: {
    formality: "casual" | "balanced" | "formal";
    enthusiasm: "low" | "moderate" | "high";
    length_preference: "short" | "medium" | "long";
    use_emojis: boolean;
  };
  use_voice_profile: boolean;  // If true, use analyzed voice; if false, use tone_preferences
}
```

### 3. Notification Preferences
```typescript
{
  notification_preferences: {
    email_on_draft_ready: boolean;
    email_on_publish_success: boolean;
    email_on_errors: boolean;
    weekly_summary: boolean;
  }
}
```

### 4. Email Settings
```typescript
{
  email_preferences: {
    default_subject_template: string;    // e.g., "{title} - Weekly Newsletter"
    include_preview_text: boolean;
    track_opens: boolean;
    track_clicks: boolean;
  }
}
```

## Integration Points

### Backend Components That Must Respect Preferences

#### 1. **Draft Scheduler** (`backend/app/services/draft_scheduler.py`)
**Current Status**: ❌ Needs Implementation
**Required Changes**:
- Read `draft_schedule_time` from user preferences
- Schedule draft generation at user-specified time (not hardcoded 8:00 AM)
- Respect `newsletter_frequency` setting
- Create per-user scheduled jobs instead of global jobs

**Implementation**:
```python
# Load user preferences
preferences = await get_user_preferences(user_id)
schedule_time = preferences.get('draft_schedule_time', '09:00')

# Schedule based on frequency
if preferences.get('newsletter_frequency') == 'daily':
    scheduler.add_job(
        generate_draft,
        trigger='cron',
        hour=int(schedule_time.split(':')[0]),
        minute=int(schedule_time.split(':')[1]),
        args=[user_id]
    )
elif preferences.get('newsletter_frequency') == 'weekly':
    # Schedule for specific day of week
    pass
```

#### 2. **Draft Generation Service** (`backend/app/services/draft_generator.py`)
**Current Status**: ❌ Needs Implementation
**Required Changes**:
- Check `use_voice_profile` preference
- If `true`: Use voice profile from database
- If `false`: Use `tone_preferences` for LLM prompts
- Apply formality, enthusiasm, length, and emoji preferences to prompts
- Generate content matching user's style preferences

**Implementation**:
```python
async def generate_draft(user_id: str, content_items: List):
    preferences = await get_user_preferences(user_id)
    
    if preferences.get('use_voice_profile'):
        # Use voice profile
        voice_profile = await get_voice_profile(user_id)
        prompt = build_prompt_with_voice(voice_profile, content_items)
    else:
        # Use tone preferences
        tone_prefs = preferences.get('tone_preferences', {})
        prompt = build_prompt_with_tone(
            formality=tone_prefs.get('formality', 'balanced'),
            enthusiasm=tone_prefs.get('enthusiasm', 'moderate'),
            length=tone_prefs.get('length_preference', 'medium'),
            use_emojis=tone_prefs.get('use_emojis', True),
            content_items=content_items
        )
    
    draft = await llm_service.generate(prompt)
    return draft
```

#### 3. **Email/Notification Service** (`backend/app/services/email_service.py`)
**Current Status**: ❌ Needs Implementation
**Required Changes**:
- Check notification preferences before sending emails
- Only send if corresponding preference is enabled
- Apply email preferences (subject template, preview text, tracking)

**Implementation**:
```python
async def send_draft_ready_notification(user_id: str, draft_id: str):
    preferences = await get_user_preferences(user_id)
    
    # Check if user wants this notification
    if not preferences.get('notification_preferences', {}).get('email_on_draft_ready'):
        return  # Don't send
    
    # Apply email preferences
    email_prefs = preferences.get('email_preferences', {})
    subject = email_prefs.get('default_subject_template', '{title}').format(title=draft.title)
    
    await send_email(
        to=user.email,
        subject=subject,
        body=draft.content,
        include_preview=email_prefs.get('include_preview_text', True),
        track_opens=email_prefs.get('track_opens', False),
        track_clicks=email_prefs.get('track_clicks', False)
    )
```

#### 4. **Source Crawler** (`backend/app/services/crawler.py`)
**Current Status**: ✅ Partially Implemented
**Required Changes**:
- Respect `newsletter_frequency` when scheduling crawls
- Adjust crawl frequency based on user's newsletter frequency
- Daily newsletter → More frequent crawls
- Weekly newsletter → Less frequent crawls

#### 5. **LLM Service** (`backend/app/services/llm_service.py`)
**Current Status**: ❌ Needs Implementation
**Required Changes**:
- Accept tone preferences as parameters
- Build prompts that incorporate formality, enthusiasm, length
- Handle emoji inclusion/exclusion
- Support voice profile-based generation

**Prompt Templates**:
```python
FORMALITY_PROMPTS = {
    'casual': "Write in a friendly, conversational tone as if talking to a friend.",
    'balanced': "Write in a professional yet approachable tone.",
    'formal': "Write in a business-like, structured, and formal tone."
}

ENTHUSIASM_PROMPTS = {
    'low': "Keep the tone matter-of-fact and straightforward.",
    'moderate': "Be enthusiastic but not overwhelming.",
    'high': "Be very excited and energetic about the content."
}

LENGTH_PROMPTS = {
    'short': "Keep it concise and to the point. Aim for 200-300 words.",
    'medium': "Provide balanced detail. Aim for 400-600 words.",
    'long': "Be comprehensive with full explanations. Aim for 800-1200 words."
}
```

### Frontend Components That Must Respect Preferences

#### 1. **Draft Editor** (`frontend/src/pages/DraftEditor.tsx`)
**Current Status**: ❓ Needs Review
**Required Changes**:
- Display current tone/style settings
- Allow override per draft if needed
- Show voice profile status

#### 2. **Newsletter Preview** (`frontend/src/components/NewsletterPreview.tsx`)
**Current Status**: ❓ Needs Review
**Required Changes**:
- Apply email preferences to preview
- Show subject line with template applied
- Display preview text if enabled

## Database Schema

### User Preferences Table
```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Schedule & Frequency
    draft_schedule_time TIME NOT NULL DEFAULT '09:00:00',
    newsletter_frequency VARCHAR(20) NOT NULL DEFAULT 'weekly',
    
    -- Tone Preferences
    formality VARCHAR(20) NOT NULL DEFAULT 'balanced',
    enthusiasm VARCHAR(20) NOT NULL DEFAULT 'moderate',
    length_preference VARCHAR(20) NOT NULL DEFAULT 'medium',
    use_emojis BOOLEAN NOT NULL DEFAULT true,
    use_voice_profile BOOLEAN NOT NULL DEFAULT false,
    
    -- Notification Preferences
    email_on_draft_ready BOOLEAN NOT NULL DEFAULT true,
    email_on_publish_success BOOLEAN NOT NULL DEFAULT true,
    email_on_errors BOOLEAN NOT NULL DEFAULT true,
    weekly_summary BOOLEAN NOT NULL DEFAULT false,
    
    -- Email Preferences
    default_subject_template TEXT NOT NULL DEFAULT '{title} - Weekly Newsletter',
    include_preview_text BOOLEAN NOT NULL DEFAULT true,
    track_opens BOOLEAN NOT NULL DEFAULT false,
    track_clicks BOOLEAN NOT NULL DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);
```

## API Endpoints

### Existing Endpoints
```
GET    /api/user/preferences          - Get user preferences
PATCH  /api/user/preferences          - Update preferences
POST   /api/user/preferences/reset    - Reset to defaults
```

### Required New Endpoints (if needed)
```
GET    /api/user/preferences/voice-profile    - Get voice profile status
POST   /api/user/preferences/apply-to-draft   - Apply preferences to specific draft
```

## Implementation Priority

### Phase 1: Critical (Must Have)
1. ✅ **User Preferences API** - Already implemented
2. ❌ **Draft Scheduler** - Respect `draft_schedule_time`
3. ❌ **Draft Generator** - Use `tone_preferences` or `use_voice_profile`
4. ❌ **Notification Service** - Check notification preferences before sending

### Phase 2: Important (Should Have)
5. ❌ **Email Service** - Apply email preferences (subject, preview, tracking)
6. ❌ **LLM Prompt Builder** - Incorporate tone preferences into prompts
7. ❌ **Crawler Frequency** - Adjust based on newsletter frequency

### Phase 3: Nice to Have
8. ❌ **Weekly Summary** - Generate and send if enabled
9. ❌ **Per-Draft Override** - Allow temporary preference override
10. ❌ **Preference History** - Track preference changes

## Testing Checklist

### Schedule & Frequency
- [ ] Draft generated at user-specified time
- [ ] Daily frequency triggers daily drafts
- [ ] Weekly frequency triggers weekly drafts
- [ ] Custom frequency works as expected

### Tone & Style
- [ ] Casual tone produces friendly content
- [ ] Formal tone produces business-like content
- [ ] Low enthusiasm is matter-of-fact
- [ ] High enthusiasm is energetic
- [ ] Short length is concise (~200-300 words)
- [ ] Long length is comprehensive (~800-1200 words)
- [ ] Emojis included when enabled
- [ ] Emojis excluded when disabled
- [ ] Voice profile used when enabled
- [ ] Tone preferences used when voice profile disabled

### Notifications
- [ ] Draft ready email sent only if enabled
- [ ] Publish success email sent only if enabled
- [ ] Error email sent only if enabled
- [ ] Weekly summary sent only if enabled

### Email Settings
- [ ] Subject template applied correctly
- [ ] {title} placeholder replaced
- [ ] Preview text included when enabled
- [ ] Open tracking works when enabled
- [ ] Click tracking works when enabled

## Migration Plan

### Step 1: Database Migration
```sql
-- Already exists, verify schema matches requirements
```

### Step 2: Update Backend Services
1. Create `PreferencesService` utility class
2. Update `DraftScheduler` to read preferences
3. Update `DraftGenerator` to use preferences
4. Update `EmailService` to check preferences
5. Update `LLMService` to accept tone parameters

### Step 3: Update Frontend
1. Ensure Profile page saves preferences correctly ✅
2. Update draft editor to show current preferences
3. Add preference indicators in UI

### Step 4: Testing
1. Unit tests for each service
2. Integration tests for end-to-end flow
3. User acceptance testing

## Notes

- **Default Values**: Always provide sensible defaults if preferences not set
- **Backward Compatibility**: Handle cases where preferences don't exist yet
- **Performance**: Cache preferences to avoid repeated database queries
- **Validation**: Validate preference values on save
- **Documentation**: Update user documentation with preference descriptions

## Current Status Summary

| Component | Status | Priority | Notes |
|-----------|--------|----------|-------|
| User Preferences API | ✅ Done | Critical | Already implemented |
| Profile UI | ✅ Done | Critical | Already implemented |
| Draft Scheduler | ❌ TODO | Critical | Needs per-user scheduling |
| Draft Generator | ❌ TODO | Critical | Needs tone/voice integration |
| Notification Service | ❌ TODO | Critical | Needs preference checks |
| Email Service | ❌ TODO | Important | Needs template & tracking |
| LLM Prompts | ❌ TODO | Important | Needs tone parameters |
| Crawler Frequency | ⚠️ Partial | Important | Needs frequency adjustment |
| Weekly Summary | ❌ TODO | Nice to Have | New feature |

## Next Steps

1. **Immediate**: Implement Draft Generator tone/voice preference integration
2. **Next**: Update Draft Scheduler to respect user schedule times
3. **Then**: Implement Notification Service with preference checks
4. **Finally**: Add Email Service preference application
