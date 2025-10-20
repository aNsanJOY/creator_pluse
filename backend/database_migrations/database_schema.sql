-- CreatorPulse Database Schema for Supabase
-- This file contains the complete database schema for the application

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    voice_profile JSONB NULL,
    preferences JSONB NULL DEFAULT '{}'::jsonb,
    reset_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sources table (Twitter, YouTube, RSS, and extensible for future sources)
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL, -- Removed CHECK constraint to allow new source types
    name VARCHAR(255) NOT NULL,
    url TEXT,
    credentials JSONB, -- Flexible storage for any source-specific credentials
    config JSONB DEFAULT '{}', -- Additional configuration per source type
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'error', 'pending')),
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Source content cache table
CREATE TABLE IF NOT EXISTS source_content_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    url TEXT,
    metadata JSONB,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- NOTE: newsletters table removed - using newsletter_drafts table instead (see draft_schema.sql)
-- All newsletter drafts and published newsletters are stored in newsletter_drafts table

-- Newsletter samples (for voice training)
CREATE TABLE IF NOT EXISTS newsletter_samples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feedback table (thumbs up/down)
-- Note: newsletter_id references newsletter_drafts table (not newsletters)
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    newsletter_id UUID NOT NULL,
    feedback_type VARCHAR(50) NOT NULL CHECK (feedback_type IN ('thumbs_up', 'thumbs_down')),
    section_id VARCHAR(255),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trends table
CREATE TABLE IF NOT EXISTS trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic VARCHAR(500) NOT NULL,
    score FLOAT NOT NULL,
    sources JSONB,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sources_user_id ON sources(user_id);
CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);
CREATE INDEX IF NOT EXISTS idx_source_content_cache_source_id ON source_content_cache(source_id);
CREATE INDEX IF NOT EXISTS idx_source_content_cache_published_at ON source_content_cache(published_at DESC);
-- Indexes for newsletters table removed (table deprecated)
CREATE INDEX IF NOT EXISTS idx_newsletter_samples_user_id ON newsletter_samples(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_newsletter_id ON feedback(newsletter_id);
CREATE INDEX IF NOT EXISTS idx_trends_user_id ON trends(user_id);
CREATE INDEX IF NOT EXISTS idx_trends_detected_at ON trends(detected_at DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for newsletters table removed (table deprecated)

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_content_cache ENABLE ROW LEVEL SECURITY;
-- RLS for newsletters table removed (table deprecated)
ALTER TABLE newsletter_samples ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE trends ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view their own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- RLS Policies for sources table
CREATE POLICY "Users can view their own sources" ON sources
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sources" ON sources
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sources" ON sources
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own sources" ON sources
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for source_content_cache table
CREATE POLICY "Users can view content from their sources" ON source_content_cache
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM sources 
            WHERE sources.id = source_content_cache.source_id 
            AND sources.user_id = auth.uid()
        )
    );

-- RLS Policies for newsletters table removed (table deprecated)
-- See draft_schema.sql for newsletter_drafts RLS policies

-- RLS Policies for newsletter_samples table
CREATE POLICY "Users can view their own samples" ON newsletter_samples
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own samples" ON newsletter_samples
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own samples" ON newsletter_samples
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for feedback table
CREATE POLICY "Users can view their own feedback" ON feedback
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own feedback" ON feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS Policies for trends table
CREATE POLICY "Users can view their own trends" ON trends
    FOR SELECT USING (auth.uid() = user_id);

-- Comments for documentation
COMMENT ON TABLE users IS 'Stores user account information and preferences';
COMMENT ON TABLE sources IS 'Stores connected content sources (Twitter, YouTube, RSS, and extensible for future sources like Substack, Medium, LinkedIn, etc.)';
COMMENT ON TABLE source_content_cache IS 'Cache of content fetched from sources';
-- COMMENT ON TABLE newsletters removed (table deprecated - using newsletter_drafts instead);
COMMENT ON TABLE newsletter_samples IS 'Stores user-uploaded newsletters for voice training';
COMMENT ON TABLE feedback IS 'Stores user feedback on newsletter drafts';
COMMENT ON TABLE trends IS 'Stores detected trending topics';

-- Source type examples and extensibility
COMMENT ON COLUMN sources.source_type IS 'Type of source: twitter, youtube, rss, substack, medium, linkedin, podcast, newsletter, custom, etc. Extensible to support new types';
COMMENT ON COLUMN sources.config IS 'Source-specific configuration (e.g., polling frequency, filters, custom API endpoints)';
COMMENT ON COLUMN sources.credentials IS 'Source-specific credentials (OAuth tokens, API keys, etc.) - encrypted at rest';
