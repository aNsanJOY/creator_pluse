-- Migration: Add crawl_logs table for tracking scheduled crawls
-- Date: 2025-10-15
-- Description: Adds table to track crawl job execution, status, and errors

-- Crawl logs table for tracking scheduled crawl jobs
CREATE TABLE IF NOT EXISTS crawl_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
    crawl_type VARCHAR(50) NOT NULL, -- 'scheduled', 'manual', 'retry'
    status VARCHAR(50) NOT NULL CHECK (status IN ('started', 'success', 'failed', 'partial')),
    items_fetched INTEGER DEFAULT 0,
    items_new INTEGER DEFAULT 0,
    error_message TEXT,
    error_details JSONB,
    duration_ms INTEGER, -- Duration in milliseconds
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Indexes for crawl_logs
CREATE INDEX IF NOT EXISTS idx_crawl_logs_user_id ON crawl_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_source_id ON crawl_logs(source_id);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_status ON crawl_logs(status);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_started_at ON crawl_logs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_crawl_type ON crawl_logs(crawl_type);

-- Enable RLS
ALTER TABLE crawl_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for crawl_logs
CREATE POLICY "Users can view their own crawl logs" ON crawl_logs
    FOR SELECT USING (auth.uid() = user_id);

-- Comments
COMMENT ON TABLE crawl_logs IS 'Tracks execution of scheduled and manual crawl jobs';
COMMENT ON COLUMN crawl_logs.crawl_type IS 'Type of crawl: scheduled (daily cron), manual (user-triggered), retry (automatic retry)';
COMMENT ON COLUMN crawl_logs.status IS 'Crawl status: started, success, failed, partial (some items failed)';
COMMENT ON COLUMN crawl_logs.items_fetched IS 'Total number of items fetched from source';
COMMENT ON COLUMN crawl_logs.items_new IS 'Number of new items (not already in cache)';
COMMENT ON COLUMN crawl_logs.duration_ms IS 'Crawl duration in milliseconds';
