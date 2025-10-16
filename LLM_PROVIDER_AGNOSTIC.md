# LLM Provider Agnostic Implementation

## Overview
Renamed all "Groq"-specific references to generic "LLM" naming to support future provider changes (OpenAI, Anthropic, etc.) without code modifications.

## Changes Made

### 1. Database Tables (Migration File)
**File:** `backend/database_migrations/005_api_usage_tracking.sql`

**Renamed:**
- `groq_usage_logs` → `llm_usage_logs`
- `groq_rate_limit_configs` → `llm_rate_limit_configs`
- `groq_rate_limits` → `llm_rate_limits`
- `groq_usage_daily_summary` → `llm_usage_daily_summary`
- `refresh_groq_usage_summary()` → `refresh_llm_usage_summary()`

**Updated Comments:**
- "Groq API" → "LLM API (Groq, OpenAI, etc.)"
- "Groq free tier" → "Default" (in rate limit descriptions)

### 2. Backend Service
**Files:**
- ❌ Deleted: `groq_usage_tracker.py`
- ✅ Created: `llm_usage_tracker.py`

**Class Renamed:**
- `GroqUsageTracker` → `LLMUsageTracker`
- `groq_usage_tracker` → `llm_usage_tracker` (instance)

**Methods:**
- `log_groq_call()` → `log_llm_call()`
- All references to "Groq" in docstrings updated to "LLM"

**Supports Multiple Providers:**
```python
# Works with any LLM provider
await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model="llama-3.1-70b-versatile",  # Groq model
    # OR
    model="gpt-4",  # OpenAI model
    # OR
    model="claude-3-opus",  # Anthropic model
    ...
)
```

### 3. API Routes
**Files:**
- ❌ Deleted: `groq_usage.py`
- ✅ Created: `llm_usage.py`

**Endpoints Changed:**
- `/api/groq/usage/*` → `/api/llm/usage/*`

**New Endpoints:**
- `GET /api/llm/usage/summary`
- `GET /api/llm/usage/stats`
- `GET /api/llm/usage/rate-limits`
- `GET /api/llm/usage/rate-limit/{type}`
- `GET /api/llm/usage/logs`

### 4. Frontend Component
**Files:**
- ❌ Deleted: `GroqUsageCard.tsx`
- ✅ Created: `LLMUsageCard.tsx`

**Component Renamed:**
- `GroqUsageCard` → `LLMUsageCard`
- `GroqUsageSummary` → `LLMUsageSummary`

**UI Text Updated:**
- "Groq API Usage" → "LLM API Usage"
- "Groq API quota" → "LLM API quota"
- "Groq API limit" → "LLM API limit"

**API Endpoint:**
- `/api/groq/usage/summary` → `/api/llm/usage/summary`

### 5. Main App Router
**File:** `backend/app/main.py`

**Import Changed:**
```python
# Before
from app.api.routes import groq_usage
app.include_router(groq_usage.router, prefix="/api/groq/usage", tags=["Groq Usage"])

# After
from app.api.routes import llm_usage
app.include_router(llm_usage.router, prefix="/api/llm/usage", tags=["LLM Usage"])
```

### 6. Dashboard Integration
**File:** `frontend/src/pages/Dashboard.tsx`

**Import Changed:**
```tsx
// Before
import { GroqUsageCard } from "../components/GroqUsageCard"

// After
import { LLMUsageCard } from "../components/LLMUsageCard"
```

**Component Usage:**
```tsx
{/* LLM API Usage Card */}
<LLMUsageCard />
```

## Benefits

### ✅ Provider Flexibility
Can switch from Groq to OpenAI, Anthropic, or any other LLM provider without renaming tables or code.

### ✅ Multi-Provider Support
Can track usage across multiple LLM providers simultaneously:
```python
# Track Groq call
await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model="llama-3.1-70b-versatile",
    metadata={"provider": "groq"}
)

# Track OpenAI call
await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model="gpt-4",
    metadata={"provider": "openai"}
)
```

### ✅ Future-Proof
No code changes needed when:
- Switching providers
- Adding new providers
- Using multiple providers

### ✅ Clean Abstraction
Code refers to "LLM" generically, not tied to specific vendor.

## Migration Path

### If Already Using Groq Tables

**Option 1: Rename Existing Tables (Recommended)**
```sql
-- Rename tables
ALTER TABLE groq_usage_logs RENAME TO llm_usage_logs;
ALTER TABLE groq_rate_limit_configs RENAME TO llm_rate_limit_configs;
ALTER TABLE groq_rate_limits RENAME TO llm_rate_limits;
ALTER MATERIALIZED VIEW groq_usage_daily_summary RENAME TO llm_usage_daily_summary;

-- Rename function
ALTER FUNCTION refresh_groq_usage_summary() RENAME TO refresh_llm_usage_summary;

-- Update indexes
ALTER INDEX idx_groq_usage_user_id RENAME TO idx_llm_usage_user_id;
ALTER INDEX idx_groq_usage_model RENAME TO idx_llm_usage_model;
-- ... (rename all indexes)
```

**Option 2: Fresh Migration**
- Drop old Groq tables
- Run new `005_api_usage_tracking.sql` migration
- Start fresh (loses historical data)

### If Starting Fresh
Just run the migration as-is:
```bash
psql -h host -U postgres -d postgres \
  -f backend/database_migrations/005_api_usage_tracking.sql
```

## Usage Examples

### Logging LLM Calls

**With Groq:**
```python
from app.services.llm_usage_tracker import llm_usage_tracker

response = groq_client.chat.completions.create(...)

await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model="llama-3.1-70b-versatile",
    tokens_used=response.usage.total_tokens,
    prompt_tokens=response.usage.prompt_tokens,
    completion_tokens=response.usage.completion_tokens,
    metadata={"provider": "groq"}
)
```

**With OpenAI:**
```python
response = openai_client.chat.completions.create(...)

await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model="gpt-4",
    tokens_used=response.usage.total_tokens,
    prompt_tokens=response.usage.prompt_tokens,
    completion_tokens=response.usage.completion_tokens,
    metadata={"provider": "openai"}
)
```

**With Anthropic:**
```python
response = anthropic_client.messages.create(...)

await llm_usage_tracker.log_llm_call(
    user_id=user_id,
    model="claude-3-opus",
    tokens_used=response.usage.input_tokens + response.usage.output_tokens,
    prompt_tokens=response.usage.input_tokens,
    completion_tokens=response.usage.output_tokens,
    metadata={"provider": "anthropic"}
)
```

### Checking Rate Limits
```python
# Same code works regardless of provider
limit_info = await llm_usage_tracker.check_rate_limit(
    user_id=user_id,
    limit_type="minute"
)

if not limit_info["can_call"]:
    raise HTTPException(429, "Rate limit exceeded")
```

### Getting Usage Stats
```python
# Returns stats across all LLM providers
stats = await llm_usage_tracker.get_usage_stats(
    user_id=user_id,
    days=30
)

# Shows breakdown by model (works for any provider)
print(stats["by_model"])
# {
#   "llama-3.1-70b-versatile": {...},  # Groq
#   "gpt-4": {...},                     # OpenAI
#   "claude-3-opus": {...}              # Anthropic
# }
```

## Configuration

### Rate Limits
Rate limits are provider-agnostic. Set them based on your needs:

```sql
-- Update default limits
UPDATE llm_rate_limit_configs 
SET limit_value = 100 
WHERE limit_type = 'minute';

-- Set user-specific limits
INSERT INTO llm_rate_limits (user_id, limit_type, limit_value, reset_at)
VALUES ('user-id', 'minute', 200, NOW() + INTERVAL '1 minute');
```

### Provider-Specific Limits (Future)
If needed, can add provider-specific limits:

```sql
-- Add provider column (optional future enhancement)
ALTER TABLE llm_rate_limits ADD COLUMN provider VARCHAR(50);

-- Set different limits per provider
INSERT INTO llm_rate_limits (user_id, limit_type, limit_value, provider, reset_at)
VALUES 
  ('user-id', 'minute', 30, 'groq', NOW() + INTERVAL '1 minute'),
  ('user-id', 'minute', 60, 'openai', NOW() + INTERVAL '1 minute');
```

## Testing

### Test with Current Provider (Groq)
```bash
# Everything works exactly as before
# Just uses generic "LLM" naming
```

### Test Provider Switch
```python
# Change from Groq to OpenAI
# Only need to change the client initialization
# All tracking code stays the same

# Before (Groq)
client = Groq(api_key=...)

# After (OpenAI)
client = OpenAI(api_key=...)

# Tracking code unchanged
await llm_usage_tracker.log_llm_call(...)
```

## Summary

✅ **All "Groq" references removed** - Now uses generic "LLM"  
✅ **Database tables renamed** - `llm_*` instead of `groq_*`  
✅ **Backend service renamed** - `LLMUsageTracker`  
✅ **API endpoints updated** - `/api/llm/usage/*`  
✅ **Frontend component renamed** - `LLMUsageCard`  
✅ **Provider-agnostic** - Works with Groq, OpenAI, Anthropic, etc.  
✅ **Future-proof** - No code changes needed to switch providers  

The system now tracks "LLM usage" generically, making it easy to switch providers or use multiple providers simultaneously!
