# Supabase Sample Library Setup Guide

This guide will help you set up your own Supabase sample library for Beat-Sensei.

## Why Use Supabase?

- **Free tier available** - Perfect for personal use
- **Fast and reliable** - Global CDN for audio files
- **Easy to manage** - Web dashboard for viewing/editing samples
- **Scalable** - Can handle thousands of samples

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up
2. Click "New Project"
3. Enter project details:
   - **Name**: `beat-sensei-samples` (or your preferred name)
   - **Database Password**: Save this somewhere secure
   - **Region**: Choose closest to you
4. Click "Create new project" (takes 1-2 minutes)

## Step 2: Get API Credentials

1. In your project dashboard, go to **Settings > API**
2. Copy these values:
   - **Project URL**: `https://xxxxxxxxxxxx.supabase.co`
   - **anon/public key**: Starts with `eyJ...`
   - **service_role key**: (Keep this secret! For uploads only)

## Step 3: Set Up Environment Variables

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc, or ~/.env file)
export SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
export SUPABASE_ANON_KEY=eyJ...
export SUPABASE_SERVICE_KEY=eyJ...  # For uploads only
```

Or create a `.env` file in the beat-sensei directory:
```bash
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
```

## Step 4: Create Database Schema

Run this SQL in **Supabase Dashboard > SQL Editor**:

```sql
-- Samples table
CREATE TABLE IF NOT EXISTS samples (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    pack_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_path TEXT,
    tags TEXT[] DEFAULT '{}',
    bpm INTEGER,
    key TEXT,
    mood TEXT,
    duration_ms INTEGER,
    file_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast search
CREATE INDEX IF NOT EXISTS idx_samples_category ON samples(category);
CREATE INDEX IF NOT EXISTS idx_samples_tags ON samples USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_samples_name ON samples(name);
CREATE INDEX IF NOT EXISTS idx_samples_pack ON samples(pack_name);

-- Enable Row Level Security
ALTER TABLE samples ENABLE ROW LEVEL SECURITY;

-- Allow public read access (samples are public)
CREATE POLICY "Samples are publicly readable"
ON samples FOR SELECT
TO public
USING (true);
```

## Step 5: Create Storage Bucket

1. Go to **Storage > Create new bucket**
2. Name: `samples`
3. **IMPORTANT**: Check "Public bucket" (so samples can be accessed)
4. Click "Create bucket"

## Step 6: Upload Your Samples

```bash
# Make sure service key is set
export SUPABASE_SERVICE_KEY=your_service_key

# Preview what will be uploaded
python scripts/upload_samples.py /path/to/your/samples --dry-run

# Actually upload
python scripts/upload_samples.py /path/to/your/samples
```

The script will:
- Scan all audio files (WAV, MP3, AIFF, FLAC, etc.)
- Auto-detect category from filename/folder
- Extract tags from filename
- Upload to Supabase Storage
- Add metadata to database

## Step 7: Verify Setup

```bash
# Check library status
beat-sensei library

# Search samples
beat-sensei samples "kick"
beat-sensei samples --category 808
beat-sensei samples --category kick --limit 5

# In interactive mode, you can now:
# - Type "kicks", "snares", etc. to browse
# - Type "search dark trap" to find samples
# - Get sample recommendations after generating tracks
```

## Troubleshooting

### "Could not connect to Supabase"
- Check your `SUPABASE_URL` and `SUPABASE_ANON_KEY`
- Make sure you're using the **anon key**, not service key
- Verify your project is active in Supabase dashboard

### "Library is empty"
- Run the upload script with your samples
- Check that storage bucket "samples" exists and is public
- Verify database table "samples" was created

### "Permission denied" on upload
- You need `SUPABASE_SERVICE_KEY` for uploads (not anon key)
- Service key has admin privileges

### Samples not playing
- Storage bucket must be set to "Public"
- Check file URLs in database: they should be accessible

## Sample Organization Tips

For best results, organize your samples like this:

```
My Samples/
├── Kick Pack/
│   ├── Kick - Dark.wav
│   ├── Kick - Punchy.wav
│   └── Kick - Trap.wav
├── Snare Pack/
│   ├── Snare - Crispy.wav
│   └── Snare - Layered.wav
└── 808 Pack/
    ├── 808 - Clean.wav
    └── 808 - Distorted.wav
```

The script will:
- Use folder names as pack names
- Detect category from keywords in path/filename
- Extract tags from keywords

## Advanced: Custom Categories

You can edit `scripts/upload_samples.py` to add custom categories:

```python
CATEGORY_KEYWORDS = {
    'kick': ['kick', 'kicks', 'kik'],
    'snare': ['snare', 'snares', 'snr', 'rim'],
    # Add your own:
    'vocal': ['vocal', 'vocals', 'vox', 'voice'],
    'fx': ['fx', 'sfx', 'effect', 'riser'],
}
```

## Need Help?

- Check Supabase documentation: https://supabase.com/docs
- Join the Beat-Sensei community
- Open an issue on GitHub