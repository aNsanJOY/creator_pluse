# Groq Usage UI Implementation

## Overview
Added a dashboard card to display remaining Groq API calls with real-time updates and visual indicators.

## What Was Added

### 1. GroqUsageCard Component
**Location:** `frontend/src/components/GroqUsageCard.tsx`

**Features:**
- ✅ Real-time rate limit display (per minute & per day)
- ✅ Visual progress bars with color coding
- ✅ Remaining calls prominently displayed
- ✅ Usage statistics (today & monthly)
- ✅ Auto-refresh every 30 seconds
- ✅ Warning alerts when approaching limits
- ✅ Error alerts when limits exceeded

**Visual Design:**
```
┌─────────────────────────────────────┐
│ ⚡ Groq API Usage                   │
├─────────────────────────────────────┤
│ 🕐 Per Minute                       │
│ ✓ 18 remaining                      │
│ 12 / 30 calls     40% used          │
│ [████████░░░░░░░░░░]                │
│                                     │
│ 📈 Per Day                          │
│ ✓ 13,150 remaining                  │
│ 1.3K / 14.4K calls    8.7% used     │
│ [██░░░░░░░░░░░░░░░░░░]              │
│                                     │
│ Today's Calls:        45            │
│ Today's Tokens:       18K           │
│ Monthly Calls:        1.3K          │
│ Monthly Tokens:       450K          │
└─────────────────────────────────────┘
```

**Color Coding:**
- 🟢 **Green** (0-69%): Healthy usage
- 🟡 **Yellow** (70-89%): Approaching limit
- 🔴 **Red** (90-100%): Near/at limit

### 2. Dashboard Integration
**Location:** `frontend/src/pages/Dashboard.tsx`

Added the `<GroqUsageCard />` component to the dashboard, positioned between Voice Training and Crawl Status cards.

## User-Specific Rate Limits

### Backend Implementation
Rate limits are **fully user-specific**:

**Database Structure:**
```sql
groq_rate_limits (
    user_id UUID,        -- Unique per user
    limit_type VARCHAR,  -- 'minute' or 'day'
    limit_value INT,     -- Can be customized per user
    current_count INT,   -- User's current usage
    reset_at TIMESTAMP   -- When user's counter resets
)
```

**How It Works:**
1. Each user has their own rate limit records
2. Limits are created on-demand when user first accesses Groq
3. Counters increment only for that specific user
4. Resets happen independently per user
5. Premium users can have higher limits

**Example:**
```sql
-- User A: Free tier (default)
user_id: 'user-a-uuid'
limit_type: 'day'
limit_value: 14400
current_count: 1250

-- User B: Premium tier (custom limit)
user_id: 'user-b-uuid'
limit_type: 'day'
limit_value: 50000  -- Higher limit
current_count: 5000
```

### Setting Custom Limits Per User

**Via SQL:**
```sql
-- Set custom limit for premium user
INSERT INTO groq_rate_limits (user_id, limit_type, limit_value, reset_at)
VALUES ('user-uuid', 'day', 50000, NOW() + INTERVAL '1 day')
ON CONFLICT (user_id, limit_type) 
DO UPDATE SET limit_value = 50000;
```

**Via API (Future):**
```bash
POST /api/admin/groq/rate-limits
{
  "user_id": "user-uuid",
  "limit_type": "day",
  "limit_value": 50000
}
```

## API Endpoints Used

### GET /api/groq/usage/summary
Returns user-specific data:
```json
{
  "summary": {
    "today": {
      "calls": 45,
      "tokens": 18000,
      "prompt_tokens": 12000,
      "completion_tokens": 6000
    },
    "this_month": {
      "calls": 1250,
      "tokens": 450000,
      "prompt_tokens": 300000,
      "completion_tokens": 150000
    },
    "rate_limits": {
      "per_minute": {
        "can_call": true,
        "current_count": 12,
        "limit_value": 30,
        "remaining": 18,
        "reset_at": "2025-10-16T14:05:00Z"
      },
      "per_day": {
        "can_call": true,
        "current_count": 1250,
        "limit_value": 14400,
        "remaining": 13150,
        "reset_at": "2025-10-17T00:00:00Z"
      }
    }
  }
}
```

## Features

### 1. Real-Time Updates
- Auto-refreshes every 30 seconds
- Shows current usage immediately
- Updates progress bars dynamically

### 2. Visual Indicators
- **Progress Bars**: Show percentage used
- **Color Coding**: Green → Yellow → Red
- **Icons**: ✓ for OK, ⚠ for warning, ✗ for exceeded

### 3. Smart Warnings
**80% Warning:**
```
⚠ Approaching Rate Limit
You're using 85% of your Groq API quota.
Consider optimizing your usage or upgrading your plan.
```

**100% Error:**
```
✗ Rate Limit Exceeded
You've reached your Groq API limit.
Please wait for the counter to reset.
```

### 4. Number Formatting
- Large numbers formatted (1,250 → 1.3K)
- Millions shown as M (1,500,000 → 1.5M)
- Easy to read at a glance

### 5. Responsive Design
- Works on mobile and desktop
- Adapts to different screen sizes
- Clean, modern UI with Tailwind CSS

## Testing

### 1. View Dashboard
```bash
# Start frontend
cd frontend
npm run dev

# Navigate to dashboard
# Should see "Groq API Usage" card
```

### 2. Test Rate Limits
```bash
# Make some Groq API calls
# Watch the counters increment in real-time
# Progress bars should update
```

### 3. Test Warnings
```sql
-- Manually set high usage to test warning
UPDATE groq_rate_limits 
SET current_count = 25 
WHERE user_id = 'your-user-id' AND limit_type = 'minute';

-- Refresh dashboard - should show yellow warning
```

### 4. Test Limit Exceeded
```sql
-- Set usage to limit
UPDATE groq_rate_limits 
SET current_count = 30 
WHERE user_id = 'your-user-id' AND limit_type = 'minute';

-- Refresh dashboard - should show red error
```

## User Scenarios

### Scenario 1: New User
1. User logs in for first time
2. No rate limit records exist yet
3. First Groq call creates default limits (30/min, 14400/day)
4. Dashboard shows 0 usage, full quota available

### Scenario 2: Active User
1. User makes Groq API calls throughout the day
2. Dashboard shows real-time usage
3. Progress bars fill up as calls are made
4. Remaining calls decrease

### Scenario 3: Approaching Limit
1. User reaches 80% of daily quota
2. Yellow warning appears on dashboard
3. User can see exactly how many calls remain
4. Can plan usage accordingly

### Scenario 4: Limit Exceeded
1. User reaches 100% of quota
2. Red error message appears
3. Shows when limit will reset
4. User knows to wait or upgrade

### Scenario 5: Premium User
1. Admin sets custom higher limit (50K/day)
2. User sees their custom limit in dashboard
3. Has more quota than free tier users
4. Everything else works the same

## Benefits

### ✅ Transparency
Users always know their current usage and remaining quota

### ✅ Proactive Warnings
Alerts before hitting limits, not after

### ✅ User-Specific
Each user has independent limits and counters

### ✅ Real-Time
Updates every 30 seconds, no manual refresh needed

### ✅ Visual Feedback
Color-coded progress bars make status obvious

### ✅ Flexible
Easy to customize limits per user or tier

## Future Enhancements

1. **Usage Trends Chart**
   - Show usage over last 7 days
   - Identify usage patterns

2. **Predictive Alerts**
   - "At current rate, you'll hit limit in 2 hours"
   - Suggest optimal usage patterns

3. **Upgrade Prompts**
   - Show upgrade options when near limit
   - Compare plans side-by-side

4. **Token Breakdown**
   - Show prompt vs completion tokens
   - Identify optimization opportunities

5. **Model Usage**
   - Break down by Groq model
   - Show which models use most tokens

## Summary

✅ **UI Component Created** - GroqUsageCard with real-time updates  
✅ **Dashboard Integration** - Added to main dashboard  
✅ **User-Specific Limits** - Each user has independent rate limits  
✅ **Visual Indicators** - Progress bars, colors, warnings  
✅ **Auto-Refresh** - Updates every 30 seconds  
✅ **Flexible Limits** - Can be customized per user  

Users now have complete visibility into their Groq API usage with clear warnings before hitting limits!
