-- Migration: Add content_summaries table for storing AI-generated summaries
-- Date: 2025-10-15
-- Description: Adds table to store structured summaries of content items

-- Content summaries table
CREATE TABLE IF NOT EXISTS content_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES source_content_cache(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary_type VARCHAR(50) DEFAULT 'standard', -- 'standard', 'brief', 'detailed'
    title TEXT,
    key_points JSONB, -- Array of key points/highlights
    summary_text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- Additional metadata (word count, topics, etc.)
    model_used VARCHAR(100), -- LLM model used for generation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for content_summaries
CREATE INDEX IF NOT EXISTS idx_content_summaries_content_id ON content_summaries(content_id);
CREATE INDEX IF NOT EXISTS idx_content_summaries_user_id ON content_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_content_summaries_created_at ON content_summaries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_summaries_summary_type ON content_summaries(summary_type);

-- Enable RLS
ALTER TABLE content_summaries ENABLE ROW LEVEL SECURITY;

-- RLS Policies for content_summaries
CREATE POLICY "Users can view their own summaries" ON content_summaries
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own summaries" ON content_summaries
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own summaries" ON content_summaries
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own summaries" ON content_summaries
    FOR DELETE USING (auth.uid() = user_id);

-- Trigger for updated_at
CREATE TRIGGER update_content_summaries_updated_at BEFORE UPDATE ON content_summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE content_summaries IS 'Stores AI-generated summaries of content items';
COMMENT ON COLUMN content_summaries.summary_type IS 'Type of summary: standard (default), brief (short), detailed (comprehensive)';
COMMENT ON COLUMN content_summaries.key_points IS 'Array of key points/highlights extracted from content';
COMMENT ON COLUMN content_summaries.metadata IS 'Additional metadata like word count, topics, sentiment, etc.';
