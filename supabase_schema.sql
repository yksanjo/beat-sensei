-- Complete Supabase Backend Schema for Beat Sensei
-- Database Schema for Sample Library

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. SAMPLE_METADATA TABLE (Extended metadata)
CREATE TABLE IF NOT EXISTS sample_metadata (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    sample_id UUID REFERENCES samples(id) ON DELETE CASCADE,
    instrument_type TEXT,
    mood_tags TEXT[] DEFAULT '{}',
    energy_level INTEGER CHECK (energy_level >= 1 AND energy_level <= 10),
    era_decade TEXT,
    audio_format TEXT,
    sample_rate INTEGER,
    bit_depth INTEGER,
    channels INTEGER,
    waveform_url TEXT,
    thumbnail_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(sample_id)
);

-- 3. USER_PREFERENCES TABLE (User preferences for recommendations)
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL, -- Could be Supabase auth user_id or CLI user ID
    favorite_genres TEXT[] DEFAULT '{}',
    favorite_bpm_range INT4RANGE, -- Range type for BPM preferences
    favorite_keys TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 4. RECOMMENDATIONS TABLE (Track user-sample interactions)
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    sample_id UUID REFERENCES samples(id) ON DELETE CASCADE,
    score DECIMAL(3, 2) DEFAULT 0.0, -- Recommendation score 0.0-1.0
    interaction_type TEXT, -- 'view', 'download', 'favorite', 'play'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. API_KEYS TABLE (For CLI authentication)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key_hash TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    user_id TEXT,
    rate_limit_per_hour INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- 6. DOWNLOAD_LOGS TABLE (Track downloads for analytics)
CREATE TABLE IF NOT EXISTS download_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    sample_id UUID REFERENCES samples(id) ON DELETE CASCADE,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    user_agent TEXT,
    ip_address INET,
    country_code TEXT,
    downloaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- INDEXES FOR PERFORMANCE
-- Samples table indexes
CREATE INDEX IF NOT EXISTS idx_samples_bpm ON samples(bpm);
CREATE INDEX IF NOT EXISTS idx_samples_genre ON samples(genre);
CREATE INDEX IF NOT EXISTS idx_samples_key ON samples(key);
CREATE INDEX IF NOT EXISTS idx_samples_tags ON samples USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_samples_upload_date ON samples(upload_date);
CREATE INDEX IF NOT EXISTS idx_samples_download_count ON samples(download_count);
CREATE INDEX IF NOT EXISTS idx_samples_title ON samples USING GIN(to_tsvector('english', title));

-- Sample metadata indexes
CREATE INDEX IF NOT EXISTS idx_sample_metadata_instrument ON sample_metadata(instrument_type);
CREATE INDEX IF NOT EXISTS idx_sample_metadata_energy ON sample_metadata(energy_level);
CREATE INDEX IF NOT EXISTS idx_sample_metadata_mood ON sample_metadata USING GIN(mood_tags);

-- User preferences indexes
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_genres ON user_preferences USING GIN(favorite_genres);

-- Recommendations indexes
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_sample_id ON recommendations(sample_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_timestamp ON recommendations(timestamp);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_sample ON recommendations(user_id, sample_id);

-- API keys indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- Download logs indexes
CREATE INDEX IF NOT EXISTS idx_download_logs_sample_id ON download_logs(sample_id);
CREATE INDEX IF NOT EXISTS idx_download_logs_downloaded_at ON download_logs(downloaded_at);
CREATE INDEX IF NOT EXISTS idx_download_logs_country ON download_logs(country_code);

-- FULL-TEXT SEARCH INDEXES
-- Create a combined search vector for samples
ALTER TABLE samples ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(genre, '')), 'B') ||
        setweight(to_tsvector('english', array_to_string(tags, ' ')), 'C')
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_samples_search ON samples USING GIN(search_vector);

-- ROW LEVEL SECURITY (RLS) POLICIES
-- Enable RLS on all tables
ALTER TABLE samples ENABLE ROW LEVEL SECURITY;
ALTER TABLE sample_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE download_logs ENABLE ROW LEVEL SECURITY;

-- SAMPLES: Public read access, authenticated write access
CREATE POLICY "Samples are publicly readable" ON samples
    FOR SELECT USING (true);

CREATE POLICY "Only authenticated users can insert samples" ON samples
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Only authenticated users can update samples" ON samples
    FOR UPDATE USING (auth.role() = 'authenticated');

-- SAMPLE_METADATA: Public read access, authenticated write access
CREATE POLICY "Sample metadata is publicly readable" ON sample_metadata
    FOR SELECT USING (true);

CREATE POLICY "Only authenticated users can modify metadata" ON sample_metadata
    FOR ALL USING (auth.role() = 'authenticated');

-- USER_PREFERENCES: Users can only access their own preferences
CREATE POLICY "Users can manage their own preferences" ON user_preferences
    FOR ALL USING (user_id = auth.uid()::text OR auth.role() = 'service_role');

-- RECOMMENDATIONS: Users can only access their own recommendations
CREATE POLICY "Users can manage their own recommendations" ON recommendations
    FOR ALL USING (user_id = auth.uid()::text OR auth.role() = 'service_role');

-- API_KEYS: Service role only (for CLI authentication)
CREATE POLICY "Only service role can manage API keys" ON api_keys
    FOR ALL USING (auth.role() = 'service_role');

-- DOWNLOAD_LOGS: Service role only (for analytics)
CREATE POLICY "Only service role can access download logs" ON download_logs
    FOR ALL USING (auth.role() = 'service_role');

-- FUNCTIONS AND TRIGGERS
-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_samples_updated_at BEFORE UPDATE ON samples
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sample_metadata_updated_at BEFORE UPDATE ON sample_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to increment download count
CREATE OR REPLACE FUNCTION increment_download_count(sample_uuid UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE samples 
    SET download_count = download_count + 1
    WHERE id = sample_uuid;
END;
$$ language 'plpgsql';

-- Function to get trending samples (most downloaded in last 7 days)
CREATE OR REPLACE FUNCTION get_trending_samples(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
    sample_id UUID,
    filename TEXT,
    title TEXT,
    bpm INTEGER,
    genre TEXT,
    download_count INTEGER,
    recent_downloads BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.filename,
        s.title,
        s.bpm,
        s.genre,
        s.download_count,
        COUNT(dl.id) as recent_downloads
    FROM samples s
    LEFT JOIN download_logs dl ON s.id = dl.sample_id 
        AND dl.downloaded_at > NOW() - INTERVAL '7 days'
    GROUP BY s.id, s.filename, s.title, s.bpm, s.genre, s.download_count
    ORDER BY recent_downloads DESC, s.download_count DESC
    LIMIT limit_count;
END;
$$ language 'plpgsql';

-- Function to search samples with filters
CREATE OR REPLACE FUNCTION search_samples(
    search_query TEXT DEFAULT NULL,
    min_bpm INTEGER DEFAULT NULL,
    max_bpm INTEGER DEFAULT NULL,
    sample_key TEXT DEFAULT NULL,
    genre_filter TEXT DEFAULT NULL,
    tags_filter TEXT[] DEFAULT NULL,
    limit_count INTEGER DEFAULT 50,
    offset_count INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    filename TEXT,
    title TEXT,
    bpm INTEGER,
    key TEXT,
    genre TEXT,
    tags TEXT[],
    duration DECIMAL(10,2),
    file_size BIGINT,
    download_count INTEGER,
    file_url TEXT,
    instrument_type TEXT,
    energy_level INTEGER,
    relevance_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.filename,
        s.title,
        s.bpm,
        s.key,
        s.genre,
        s.tags,
        s.duration,
        s.file_size,
        s.download_count,
        s.file_url,
        sm.instrument_type,
        sm.energy_level,
        CASE 
            WHEN search_query IS NOT NULL THEN 
                ts_rank(s.search_vector, plainto_tsquery('english', search_query))
            ELSE 1.0
        END as relevance_score
    FROM samples s
    LEFT JOIN sample_metadata sm ON s.id = sm.sample_id
    WHERE 
        (search_query IS NULL OR s.search_vector @@ plainto_tsquery('english', search_query))
        AND (min_bpm IS NULL OR s.bpm >= min_bpm)
        AND (max_bpm IS NULL OR s.bpm <= max_bpm)
        AND (sample_key IS NULL OR s.key = sample_key)
        AND (genre_filter IS NULL OR s.genre = genre_filter)
        AND (tags_filter IS NULL OR s.tags @> tags_filter)
    ORDER BY 
        CASE WHEN search_query IS NOT NULL THEN 
            ts_rank(s.search_vector, plainto_tsquery('english', search_query))
        ELSE 1.0 END DESC,
        s.download_count DESC,
        s.upload_date DESC
    LIMIT limit_count
    OFFSET offset_count;
END;
$$ language 'plpgsql';

-- Function to get recommendations based on user preferences
CREATE OR REPLACE FUNCTION get_sample_recommendations(
    user_id_param TEXT,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    sample_id UUID,
    filename TEXT,
    title TEXT,
    bpm INTEGER,
    key TEXT,
    genre TEXT,
    tags TEXT[],
    score DECIMAL(3,2),
    reason TEXT
) AS $$
DECLARE
    user_genres TEXT[];
    user_bpm_range INT4RANGE;
    user_keys TEXT[];
BEGIN
    -- Get user preferences
    SELECT favorite_genres, favorite_bpm_range, favorite_keys
    INTO user_genres, user_bpm_range, user_keys
    FROM user_preferences
    WHERE user_id = user_id_param;
    
    -- If no preferences, return trending samples
    IF user_genres IS NULL AND user_bpm_range IS NULL AND user_keys IS NULL THEN
        RETURN QUERY
        SELECT 
            s.id,
            s.filename,
            s.title,
            s.bpm,
            s.key,
            s.genre,
            s.tags,
            (s.download_count::DECIMAL / 1000) as score, -- Normalized score
            'Trending' as reason
        FROM samples s
        ORDER BY s.download_count DESC
        LIMIT limit_count;
        RETURN;
    END IF;
    
    -- Return recommendations based on preferences
    RETURN QUERY
    SELECT 
        s.id,
        s.filename,
        s.title,
        s.bpm,
        s.key,
        s.genre,
        s.tags,
        (
            CASE WHEN s.genre = ANY(user_genres) THEN 0.3 ELSE 0.0 END +
            CASE WHEN s.bpm::INTEGER <@ user_bpm_range THEN 0.3 ELSE 0.0 END +
            CASE WHEN s.key = ANY(user_keys) THEN 0.3 ELSE 0.0 END +
            (s.download_count::DECIMAL / 10000) -- Small boost for popularity
        ) as score,
        CASE 
            WHEN s.genre = ANY(user_genres) AND s.bpm::INTEGER <@ user_bpm_range AND s.key = ANY(user_keys) 
                THEN 'Matches all preferences'
            WHEN s.genre = ANY(user_genres) AND s.bpm::INTEGER <@ user_bpm_range 
                THEN 'Matches genre and BPM'
            WHEN s.genre = ANY(user_genres) AND s.key = ANY(user_keys) 
                THEN 'Matches genre and key'
            WHEN s.bpm::INTEGER <@ user_bpm_range AND s.key = ANY(user_keys) 
                THEN 'Matches BPM and key'
            WHEN s.genre = ANY(user_genres) 
                THEN 'Matches genre'
            WHEN s.bpm::INTEGER <@ user_bpm_range 
                THEN 'Matches BPM range'
            WHEN s.key = ANY(user_keys) 
                THEN 'Matches key'
            ELSE 'Popular sample'
        END as reason
    FROM samples s
    WHERE 
        (user_genres IS NULL OR s.genre = ANY(user_genres))
        OR (user_bpm_range IS NULL OR s.bpm::INTEGER <@ user_bpm_range)
        OR (user_keys IS NULL OR s.key = ANY(user_keys))
    ORDER BY score DESC, s.download_count DESC
    LIMIT limit_count;
END;
$$ language 'plpgsql';

-- Create a view for sample statistics
CREATE OR REPLACE VIEW sample_statistics AS
SELECT 
    COUNT(*) as total_samples,
    COUNT(DISTINCT genre) as unique_genres,
    COUNT(DISTINCT key) as unique_keys,
    AVG(bpm) as avg_bpm,
    MIN(bpm) as min_bpm,
    MAX(bpm) as max_bpm,
    SUM(file_size) as total_storage_bytes,
    SUM(download_count) as total_downloads,
    MAX(upload_date) as latest_upload
FROM samples;

-- Create a view for daily download statistics
CREATE OR REPLACE VIEW daily_download_stats AS
SELECT 
    DATE(downloaded_at) as download_date,
    COUNT(*) as download_count,
    COUNT(DISTINCT sample_id) as unique_samples,
    COUNT(DISTINCT ip_address) as unique_users
FROM download_logs
GROUP BY DATE(downloaded_at)
ORDER BY download_date DESC;

-- Comments for documentation
COMMENT ON TABLE samples IS 'Main sample library with audio file metadata';
COMMENT ON TABLE sample_metadata IS 'Extended audio analysis metadata';
COMMENT ON TABLE user_preferences IS 'User preferences for personalized recommendations';
COMMENT ON TABLE recommendations IS 'User-sample interaction tracking for recommendation engine';
COMMENT ON TABLE api_keys IS 'API keys for CLI authentication and rate limiting';
COMMENT ON TABLE download_logs IS 'Download tracking for analytics and trending calculations';

COMMENT ON COLUMN samples.duration IS 'Duration in seconds';
COMMENT ON COLUMN samples.file_size IS 'File size in bytes';
COMMENT ON COLUMN sample_metadata.energy_level IS 'Energy level from 1 (calm) to 10 (intense)';
COMMENT ON COLUMN user_preferences.favorite_bpm_range IS 'Preferred BPM range using PostgreSQL range type';

-- Grant necessary permissions
GRANT SELECT ON samples TO anon, authenticated;
GRANT SELECT ON sample_metadata TO anon, authenticated;
GRANT SELECT ON sample_statistics TO anon, authenticated;
GRANT SELECT ON daily_download_stats TO anon, authenticated;