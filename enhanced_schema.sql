-- Enhanced Supabase Schema for Beat Sensei
-- Includes user tracking, better search, and tier management

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "vector";   -- For embedding search (future)

-- ==================== CORE TABLES ====================

-- 1. SAMPLES TABLE (Main sample metadata)
CREATE TABLE IF NOT EXISTS samples (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    filename TEXT NOT NULL,
    file_url TEXT NOT NULL,
    title TEXT NOT NULL,
    bpm INTEGER,
    key TEXT,
    genre TEXT,
    tags TEXT[] DEFAULT '{}',
    duration DECIMAL(10, 2), -- in seconds
    file_size BIGINT, -- in bytes
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    download_count INTEGER DEFAULT 0,
    play_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. SAMPLE_TAGS TABLE (Normalized tags for better search)
CREATE TABLE IF NOT EXISTS sample_tags (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    sample_id UUID REFERENCES samples(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    tag_type TEXT CHECK (tag_type IN ('category', 'mood', 'instrument', 'genre', 'style')),
    confidence DECIMAL(3, 2) DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(sample_id, tag, tag_type)
);

-- 3. USER_DOWNLOADS TABLE (Track who downloaded what)
CREATE TABLE IF NOT EXISTS user_downloads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL, -- Can be Supabase auth user_id or anonymous session_id
    sample_id UUID REFERENCES samples(id) ON DELETE CASCADE,
    downloaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET,
    country_code TEXT,
    -- For analytics
    download_source TEXT, -- 'chatbot', 'search', 'recommendation'
    session_id TEXT
);

-- 4. USER_FAVORITES TABLE (Track user favorites)
CREATE TABLE IF NOT EXISTS user_favorites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    sample_id UUID REFERENCES samples(id) ON DELETE CASCADE,
    favorited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, sample_id)
);

-- 5. USAGE_LIMITS TABLE (For tier management)
CREATE TABLE IF NOT EXISTS usage_limits (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'enterprise')),
    monthly_download_limit INTEGER DEFAULT 100,
    downloads_this_month INTEGER DEFAULT 0,
    monthly_reset_date DATE DEFAULT (DATE_TRUNC('month', NOW()) + INTERVAL '1 month')::DATE,
    max_concurrent_downloads INTEGER DEFAULT 3,
    can_access_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. API_USAGE TABLE (Track API calls for rate limiting)
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    called_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET
);

-- ==================== INDEXES FOR PERFORMANCE ====================

-- Samples table indexes
CREATE INDEX IF NOT EXISTS idx_samples_bpm ON samples(bpm);
CREATE INDEX IF NOT EXISTS idx_samples_genre ON samples(genre);
CREATE INDEX IF NOT EXISTS idx_samples_key ON samples(key);
CREATE INDEX IF NOT EXISTS idx_samples_tags ON samples USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_samples_upload_date ON samples(upload_date);
CREATE INDEX IF NOT EXISTS idx_samples_download_count ON samples(download_count);
CREATE INDEX IF NOT EXISTS idx_samples_is_featured ON samples(is_featured);
CREATE INDEX IF NOT EXISTS idx_samples_is_premium ON samples(is_premium);
CREATE INDEX IF NOT EXISTS idx_samples_title_trgm ON samples USING GIN(title gin_trgm_ops);

-- Sample tags indexes
CREATE INDEX IF NOT EXISTS idx_sample_tags_tag ON sample_tags(tag);
CREATE INDEX IF NOT EXISTS idx_sample_tags_tag_type ON sample_tags(tag_type);
CREATE INDEX IF NOT EXISTS idx_sample_tags_sample_id ON sample_tags(sample_id);

-- User downloads indexes
CREATE INDEX IF NOT EXISTS idx_user_downloads_user_id ON user_downloads(user_id);
CREATE INDEX IF NOT EXISTS idx_user_downloads_sample_id ON user_downloads(sample_id);
CREATE INDEX IF NOT EXISTS idx_user_downloads_downloaded_at ON user_downloads(downloaded_at);

-- User favorites indexes
CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_sample_id ON user_favorites(sample_id);

-- ==================== ROW LEVEL SECURITY ====================

-- Enable RLS on all tables
ALTER TABLE samples ENABLE ROW LEVEL SECURITY;
ALTER TABLE sample_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_downloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;

-- Samples: Public read access, but only admins can modify
CREATE POLICY "Allow public read access to samples"
ON samples FOR SELECT
TO public
USING (true);

CREATE POLICY "Allow authenticated users to update their favorites"
ON user_favorites FOR ALL
TO authenticated
USING (auth.uid()::text = user_id)
WITH CHECK (auth.uid()::text = user_id);

-- User downloads: Users can only see their own downloads
CREATE POLICY "Users can view their own downloads"
ON user_downloads FOR SELECT
TO authenticated
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own downloads"
ON user_downloads FOR INSERT
TO authenticated
WITH CHECK (auth.uid()::text = user_id);

-- ==================== FUNCTIONS & TRIGGERS ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_samples_updated_at
    BEFORE UPDATE ON samples
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_limits_updated_at
    BEFORE UPDATE ON usage_limits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to increment download count
CREATE OR REPLACE FUNCTION increment_download_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE samples 
    SET download_count = download_count + 1
    WHERE id = NEW.sample_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to increment download count
CREATE TRIGGER increment_sample_download_count
    AFTER INSERT ON user_downloads
    FOR EACH ROW
    EXECUTE FUNCTION increment_download_count();

-- Function to check download limits
CREATE OR REPLACE FUNCTION check_download_limit()
RETURNS TRIGGER AS $$
DECLARE
    user_limit RECORD;
BEGIN
    -- Get user's limits
    SELECT * INTO user_limit
    FROM usage_limits
    WHERE user_id = NEW.user_id;
    
    -- If user doesn't exist in limits table, create default entry
    IF NOT FOUND THEN
        INSERT INTO usage_limits (user_id, tier, monthly_download_limit)
        VALUES (NEW.user_id, 'free', 100);
        
        SELECT * INTO user_limit
        FROM usage_limits
        WHERE user_id = NEW.user_id;
    END IF;
    
    -- Check if monthly reset is needed
    IF user_limit.monthly_reset_date <= NOW()::DATE THEN
        UPDATE usage_limits
        SET downloads_this_month = 0,
            monthly_reset_date = (DATE_TRUNC('month', NOW()) + INTERVAL '1 month')::DATE
        WHERE user_id = NEW.user_id;
        
        user_limit.downloads_this_month := 0;
    END IF;
    
    -- Check if user has reached limit
    IF user_limit.downloads_this_month >= user_limit.monthly_download_limit THEN
        RAISE EXCEPTION 'Monthly download limit reached for user %', NEW.user_id;
    END IF;
    
    -- Increment download count
    UPDATE usage_limits
    SET downloads_this_month = downloads_this_month + 1
    WHERE user_id = NEW.user_id;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to check download limits
CREATE TRIGGER check_user_download_limit
    BEFORE INSERT ON user_downloads
    FOR EACH ROW
    EXECUTE FUNCTION check_download_limit();

-- ==================== VIEWS FOR ANALYTICS ====================

-- View for popular samples
CREATE OR REPLACE VIEW popular_samples AS
SELECT 
    s.*,
    COUNT(DISTINCT ud.id) as total_downloads,
    COUNT(DISTINCT uf.id) as total_favorites,
    (s.download_count * 0.5 + s.play_count * 0.3 + s.like_count * 0.2) as popularity_score
FROM samples s
LEFT JOIN user_downloads ud ON s.id = ud.sample_id
LEFT JOIN user_favorites uf ON s.id = uf.sample_id
GROUP BY s.id
ORDER BY popularity_score DESC;

-- View for user activity
CREATE OR REPLACE VIEW user_activity AS
SELECT 
    user_id,
    COUNT(DISTINCT sample_id) as unique_samples_downloaded,
    COUNT(*) as total_downloads,
    MIN(downloaded_at) as first_download,
    MAX(downloaded_at) as last_download,
    COUNT(DISTINCT DATE(downloaded_at)) as active_days
FROM user_downloads
GROUP BY user_id;

-- ==================== STORAGE BUCKET ====================

-- Create storage bucket (run this separately or in Storage UI)
-- SELECT storage.create_bucket(
--     'beat-sensei-samples',
--     '{"public": true, "file_size_limit": 52428800, "allowed_mime_types": ["audio/*"]}'
-- );

-- ==================== COMMENTS ====================

COMMENT ON TABLE samples IS 'Main audio sample metadata';
COMMENT ON TABLE sample_tags IS 'Normalized tags for advanced search';
COMMENT ON TABLE user_downloads IS 'Track user downloads for analytics and limits';
COMMENT ON TABLE user_favorites IS 'User favorite samples';
COMMENT ON TABLE usage_limits IS 'User tier and usage limit management';
COMMENT ON TABLE api_usage IS 'API call tracking for rate limiting';

-- ==================== INITIAL DATA ====================

-- Insert default usage limits for anonymous users
INSERT INTO usage_limits (user_id, tier, monthly_download_limit, can_access_premium)
VALUES 
    ('anonymous', 'free', 50, FALSE),
    ('demo_user', 'pro', 500, TRUE)
ON CONFLICT (user_id) DO NOTHING;