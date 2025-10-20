-- Migration: Add email tracking events table
-- Description: Adds table to track email opens and clicks for analytics
-- Date: 2025-01-20

-- Create email_tracking_events table
CREATE TABLE IF NOT EXISTS email_tracking_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    draft_id UUID NOT NULL REFERENCES newsletter_drafts(id) ON DELETE CASCADE,
    recipient_email TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('open', 'click')),
    event_data JSONB DEFAULT '{}'::jsonb,
    tracked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_tracking_events_draft 
    ON email_tracking_events(draft_id);

CREATE INDEX IF NOT EXISTS idx_tracking_events_user 
    ON email_tracking_events(user_id);

CREATE INDEX IF NOT EXISTS idx_tracking_events_type 
    ON email_tracking_events(event_type);

CREATE INDEX IF NOT EXISTS idx_tracking_events_recipient 
    ON email_tracking_events(recipient_email);

CREATE INDEX IF NOT EXISTS idx_tracking_events_tracked_at 
    ON email_tracking_events(tracked_at DESC);

-- Add comment to table
COMMENT ON TABLE email_tracking_events IS 'Tracks email open and click events for newsletter analytics';
COMMENT ON COLUMN email_tracking_events.event_type IS 'Type of event: open or click';
COMMENT ON COLUMN email_tracking_events.event_data IS 'Additional event data (e.g., clicked URL)';
COMMENT ON COLUMN email_tracking_events.tracked_at IS 'When the event occurred';

-- Enable Row Level Security (RLS)
ALTER TABLE email_tracking_events ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only view their own tracking events
CREATE POLICY "Users can view own tracking events"
    ON email_tracking_events
    FOR SELECT
    USING (user_id = auth.uid());

-- Service role can insert tracking events (for tracking endpoints)
CREATE POLICY "Service can insert tracking events"
    ON email_tracking_events
    FOR INSERT
    WITH CHECK (true);

-- Users can delete their own tracking events
CREATE POLICY "Users can delete own tracking events"
    ON email_tracking_events
    FOR DELETE
    USING (user_id = auth.uid());
