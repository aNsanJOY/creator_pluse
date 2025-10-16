-- Migration: Add LLM API usage tracking
-- Tracks API calls to LLM service (Groq, OpenAI, etc.)

CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255), -- API endpoint called (/v1/chat/completions, etc.)
    model VARCHAR(100), -- Model used (llama-3.1-70b-versatile, etc.)
    status_code INTEGER, -- HTTP status code
    tokens_used INTEGER DEFAULT 0, -- Total tokens consumed
    prompt_tokens INTEGER DEFAULT 0, -- Input tokens
    completion_tokens INTEGER DEFAULT 0, -- Output tokens
    duration_ms INTEGER, -- Request duration in milliseconds
    error_message TEXT, -- Error if failed
    metadata JSONB, -- Additional data (temperature, max_tokens, etc.)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_llm_usage_user_id ON llm_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_model ON llm_usage_logs(model);
CREATE INDEX IF NOT EXISTS idx_llm_usage_created_at ON llm_usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_llm_usage_user_date ON llm_usage_logs(user_id, created_at);

-- Create materialized view for daily LLM usage summary
CREATE MATERIALIZED VIEW IF NOT EXISTS llm_usage_daily_summary AS
SELECT 
    user_id,
    model,
    DATE(created_at) as usage_date,
    COUNT(*) as total_calls,
    SUM(tokens_used) as total_tokens,
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens,
    AVG(duration_ms) as avg_duration_ms,
    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
FROM llm_usage_logs
GROUP BY user_id, model, DATE(created_at);

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_llm_usage_daily_summary_unique 
ON llm_usage_daily_summary(user_id, model, usage_date);

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_llm_usage_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY llm_usage_daily_summary;
END;
$$ LANGUAGE plpgsql;

-- Create table for LLM rate limit configurations (global defaults)
CREATE TABLE IF NOT EXISTS llm_rate_limit_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    limit_type VARCHAR(20) NOT NULL, -- 'minute', 'hour', 'day', 'month'
    limit_value INTEGER NOT NULL, -- Max calls allowed
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(limit_type)
);

-- Create table for user-specific LLM rate limits
CREATE TABLE IF NOT EXISTS llm_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    limit_type VARCHAR(20) NOT NULL, -- 'minute', 'hour', 'day', 'month'
    limit_value INTEGER NOT NULL, -- Max calls allowed (can override default)
    current_count INTEGER DEFAULT 0, -- Current usage
    reset_at TIMESTAMPTZ NOT NULL, -- When the counter resets
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, limit_type)
);

-- Create index for rate limits
CREATE INDEX IF NOT EXISTS idx_llm_rate_limits_user ON llm_rate_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_rate_limits_reset ON llm_rate_limits(reset_at);

-- Add trigger to update updated_at
CREATE OR REPLACE FUNCTION update_llm_rate_limits_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_llm_rate_limits_updated_at
    BEFORE UPDATE ON llm_rate_limits
    FOR EACH ROW
    EXECUTE FUNCTION update_llm_rate_limits_updated_at();

-- Insert default LLM rate limit configurations
-- These are global defaults that can be customized per user
-- Default values based on Groq free tier, but can be adjusted for any provider
INSERT INTO llm_rate_limit_configs (limit_type, limit_value, description) VALUES
    ('minute', 30, 'Default: 30 requests per minute'),
    ('day', 14400, 'Default: 14,400 requests per day')
ON CONFLICT (limit_type) DO NOTHING;

-- Note: User-specific rate limits will be created dynamically when first accessed
-- This allows for flexible per-user limits without pre-creating records for all users

-- Comments
COMMENT ON TABLE llm_usage_logs IS 'Logs all LLM API calls for usage tracking (Groq, OpenAI, etc.)';
COMMENT ON TABLE llm_rate_limit_configs IS 'Global default LLM rate limit configurations';
COMMENT ON TABLE llm_rate_limits IS 'User-specific LLM rate limits (can override defaults)';
COMMENT ON COLUMN llm_usage_logs.tokens_used IS 'Total tokens consumed (prompt + completion)';
COMMENT ON COLUMN llm_usage_logs.prompt_tokens IS 'Input/prompt tokens';
COMMENT ON COLUMN llm_usage_logs.completion_tokens IS 'Output/completion tokens';
COMMENT ON COLUMN llm_rate_limits.limit_type IS 'Time window for rate limit: minute, hour, day, month';
COMMENT ON COLUMN llm_rate_limits.current_count IS 'Current number of LLM API calls in this time window';
COMMENT ON COLUMN llm_rate_limits.reset_at IS 'When the rate limit counter resets';
COMMENT ON COLUMN llm_rate_limit_configs.limit_value IS 'Default limit value that applies to all users unless overridden';
