# Beat-Sensei

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Your Sample Library Curator - Find the perfect sounds for your productions.

```
 ____  _____    _  _____   ____  _____ _   _ ____  _____ ___
| __ )| ____|  / \|_   _| / ___|| ____| \ | / ___|| ____|_ _|
|  _ \|  _|   / _ \ | |   \___ \|  _| |  \| \___ \|  _|  | |
| |_) | |___ / ___ \| |    ___) | |___| |\  |___) | |___ | |
|____/|_____/_/   \_\_|   |____/|_____|_| \_|____/|_____|___
```

## Features

- **Sample Library Curator** - Expert recommendations for kicks, snares, hats, 808s, and loops
- **Smart Search** - Find samples by mood, genre, or style
- **Production-Ready Sounds** - All samples are high-quality WAV files
- **Sample Loop Focus** - Specialized curation for complete musical phrases
- **Free Tier** - Full access to sample recommendations
- **Easy Setup** - Connect your Supabase sample library in minutes

## Quick Start

### Install

```bash
pip install git+https://github.com/yksanjo/beat-sensei.git
```

### Set Up Your Sample Library

```bash
# Create a free Supabase project at supabase.com
# Get your URL and anon key from Project Settings > API

export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_ANON_KEY=eyJ...

# Check connection
beat-sensei library
```

### Start Finding Sounds

```bash
beat-sensei                           # Start interactive chat
beat-sensei samples "dark trap"       # Search samples
beat-sensei samples --category loop   # Browse loops
beat-sensei samples --category kick   # Browse kicks
```

## Usage

### Interactive Chat

```
$ beat-sensei

Sensei: Yo, what's good! Ready to dig through the sample library? What sound you need?

You: dark trap kicks

Sensei: Searching for dark trap kicks... Found 8 kicks with that sinister low-end. Perfect for drill or dark trap production.

1. **Kick - Abyssal** (kick)
   Tags: dark, trap, heavy
   Pack: Dark Trap Kit

2. **Kick - Boom** (kick)
   Tags: punchy, dark, 808
   Pack: Drill Essentials

Type 'play 1' to preview the first sample, or give me another search.
```

### Commands

| Command | Description |
|---------|-------------|
| `kicks` / `snares` / `808s` / `hats` / `loops` | Browse samples by category |
| `search <query>` | Search sample library |
| `play <number>` | Preview a sample |
| `random` | Get random samples for inspiration |
| `help` | Show help |

### CLI Commands

```bash
beat-sensei                           # Start interactive chat
beat-sensei samples "dark trap"       # Search sample library
beat-sensei samples --category loop   # Browse loops
beat-sensei samples --category kick --limit 5  # Browse kicks
beat-sensei library                   # Check library status
beat-sensei config                    # View settings
```

## Sample Library

Curated collection of production-ready samples:

- **Kicks** - Punchy, boomy, trap, acoustic
- **Snares** - Crispy, rimshots, layered, claps
- **Hats** - Open, closed, shakers, patterns
- **808s** - Heavy subs, distorted, clean, melodic
- **Loops** - Complete musical phrases, chord progressions, melodies
- **Percs** - Shakers, toms, fx

All samples are tagged by mood (dark, hard, soft, sexy, etc.) and genre (trap, drill, R&B, lo-fi, etc.)

## Setup Instructions

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and sign up
2. Click "New Project"
3. Enter project details and create

### 2. Get API Credentials
1. In your project dashboard, go to **Settings > API**
2. Copy:
   - **Project URL**: `https://xxxxxxxxxxxx.supabase.co`
   - **anon/public key**: Starts with `eyJ...`
   - **service_role key**: (Keep secret! For uploads only)

### 3. Set Environment Variables
```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc)
export SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
export SUPABASE_ANON_KEY=eyJ...
export SUPABASE_SERVICE_KEY=eyJ...  # For uploads only
```

### 4. Create Database Schema
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

-- Allow public read access
CREATE POLICY "Samples are publicly readable"
ON samples FOR SELECT
TO public
USING (true);
```

### 5. Create Storage Bucket
1. Go to **Storage > Create new bucket**
2. Name: `samples`
3. **IMPORTANT**: Check "Public bucket"
4. Click "Create bucket"

### 6. Upload Your Samples
```bash
# Make sure service key is set
export SUPABASE_SERVICE_KEY=your_service_key

# Upload samples
python scripts/upload_samples.py /path/to/your/sample_loop/folder
```

## Sample Organization

For best results, organize your samples like this:

```
sample_loop/
├── Dark Trap Loops/
│   ├── Loop - Dark Melody.wav
│   ├── Loop - Sinister Chords.wav
│   └── Loop - Aggressive 808.wav
├── R&B Drill Loops/
│   ├── Loop - Sexy Chord Progression.wav
│   └── Loop - Smooth Melody.wav
└── Lo-fi Loops/
    ├── Loop - Jazzy Chords.wav
    └── Loop - Chill Melody.wav
```

The upload script will:
- Use folder names as pack names
- Detect "loop" category from folder/filename
- Extract tags from keywords
- Upload to Supabase Storage
- Add metadata to database

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

## License

MIT License