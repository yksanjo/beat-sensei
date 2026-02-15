-- Simple Schema for Beat Sensei Sample Library
-- Run this in Supabase SQL Editor first

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

-- 2. Enable Row Level Security (RLS)
ALTER TABLE samples ENABLE ROW LEVEL SECURITY;

-- 3. Create policy for public read access
CREATE POLICY "Allow public read access to samples"
ON samples FOR SELECT
TO public
USING (true);

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_samples_bpm ON samples(bpm);
CREATE INDEX IF NOT EXISTS idx_samples_genre ON samples(genre);
CREATE INDEX IF NOT EXISTS idx_samples_key ON samples(key);
CREATE INDEX IF NOT EXISTS idx_samples_tags ON samples USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_samples_upload_date ON samples(upload_date);
CREATE INDEX IF NOT EXISTS idx_samples_download_count ON samples(download_count);

-- 5. Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 6. Create trigger for updated_at
CREATE TRIGGER update_samples_updated_at
    BEFORE UPDATE ON samples
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 7. Create storage bucket (if needed)
-- Note: You'll also need to create the bucket in Storage section
SELECT storage.create_bucket(
    'beat-sensei-samples',
    '{"public": true, "file_size_limit": 52428800, "allowed_mime_types": ["audio/*"]}'
);