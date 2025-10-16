-- Migration: Add user_crawl_schedule table for tracking batch crawl times
-- This table tracks when all sources for a user were last crawled together
-- and when the next batch crawl is scheduled

CREATE TABLE IF NOT EXISTS user_crawl_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_batch_crawl_at TIMESTAMPTZ,
    next_scheduled_crawl_at TIMESTAMPTZ,
    crawl_frequency_hours INTEGER DEFAULT 24,
    is_crawling BOOLEAN DEFAULT FALSE,
    last_crawl_duration_seconds INTEGER,
    sources_crawled_count INTEGER DEFAULT 0,
    sources_failed_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_crawl_schedule_user_id ON user_crawl_schedule(user_id);
CREATE INDEX IF NOT EXISTS idx_user_crawl_schedule_next_scheduled ON user_crawl_schedule(next_scheduled_crawl_at);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_crawl_schedule_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_crawl_schedule_updated_at
    BEFORE UPDATE ON user_crawl_schedule
    FOR EACH ROW
    EXECUTE FUNCTION update_user_crawl_schedule_updated_at();

-- Insert default records for existing users
INSERT INTO user_crawl_schedule (user_id, crawl_frequency_hours)
SELECT id, 24 FROM users
ON CONFLICT (user_id) DO NOTHING;

COMMENT ON TABLE user_crawl_schedule IS 'Tracks batch crawl schedule and status for each user';
COMMENT ON COLUMN user_crawl_schedule.last_batch_crawl_at IS 'Timestamp of the last completed batch crawl for all user sources';
COMMENT ON COLUMN user_crawl_schedule.next_scheduled_crawl_at IS 'Timestamp when the next batch crawl is scheduled';
COMMENT ON COLUMN user_crawl_schedule.crawl_frequency_hours IS 'How often to crawl all sources (in hours)';
COMMENT ON COLUMN user_crawl_schedule.is_crawling IS 'Whether a batch crawl is currently in progress';
COMMENT ON COLUMN user_crawl_schedule.last_crawl_duration_seconds IS 'Duration of the last batch crawl in seconds';
COMMENT ON COLUMN user_crawl_schedule.sources_crawled_count IS 'Number of sources successfully crawled in last batch';
COMMENT ON COLUMN user_crawl_schedule.sources_failed_count IS 'Number of sources that failed in last batch';
