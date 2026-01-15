# Beat-Sensei

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Your AI Music Production Mentor - Create original tracks, browse curated samples, and level up your skills.

```
 ____  _____    _  _____   ____  _____ _   _ ____  _____ ___
| __ )| ____|  / \|_   _| / ___|| ____| \ | / ___|| ____|_ _|
|  _ \|  _|   / _ \ | |   \___ \|  _| |  \| \___ \|  _|  | |
| |_) | |___ / ___ \| |    ___) | |___| |\  |___) | |___ | |
|____/|_____/_/   \_\_|   |____/|_____|_| \_|____/|_____|___|
```

## Features

- **Instant Beat Generation** - Create tracks immediately with local beat generator
- **AI Music Generation** - Optional: Create original tracks with Soundraw AI (5 free/day)
- **Curated Sample Library** - Browse 1,500+ hand-picked samples (kicks, snares, 808s, etc.)
- **Production Mentor** - Get real advice from an experienced producer personality
- **Learn While You Create** - Tips and guidance built into every interaction
- **Free Sample Packs** - Download ready-to-use drum kits and sounds

## Quick Start

### Install

```bash
pip install git+https://github.com/yksanjo/beat-sensei.git
```

### Set Up (Optional - works out of the box!)

```bash
# For AI generation (optional - get key at soundraw.io)
export SOUNDRAW_API_TOKEN=your_soundraw_key

# For sample library (optional - get free account at supabase.com)
export SUPABASE_URL=your_project_url
export SUPABASE_ANON_KEY=your_anon_key
```

**Beat-Sensei works immediately without any setup!** The local beat generator creates tracks right away. Add API keys for enhanced features.

### Start Creating

```bash
beat-sensei
```

## Usage

### Interactive Chat

```
$ beat-sensei

Sensei: Yo, what's good! Ready to make some heat today?

You: kicks

Sensei: Here's some kicks from the library:

1. kick - abyssal (kick) [dark]
2. kick - boom (kick) [punchy]
3. kick - classic (kick) [trap]
...

Type a number to preview, or describe what else you need.

You: make dark trap high energy

Sensei: Aight, cooking up 'dark trap high energy' for you...

Done! Your track (Dark, Hip Hop) is ready.

Related samples: 808 - Grime, snare - plugg, hat - tick
(type 'play 1' to preview)

(4 generations left today)
```

### Commands

| Command | Description |
|---------|-------------|
| `make <description>` | Generate a track (5 free/day) |
| `kicks` / `snares` / `808s` / `hats` | Browse samples by category |
| `search <query>` | Search sample library |
| `play <number>` | Preview a sample |
| `random` | Get random samples |
| `options` | See moods/genres |
| `help` | Show help |
| `download <pack>` | Download sample packs |
| `scan <directory>` | Scan directory for samples |

### CLI Commands

```bash
beat-sensei                           # Start interactive chat
beat-sensei generate "dark trap"      # Quick generate track
beat-sensei options                   # See generation options
beat-sensei config                    # View settings and status
beat-sensei library                   # Check sample library status
beat-sensei samples "kick"            # Search sample library
beat-sensei download all              # Download free sample packs
beat-sensei scan ~/Music/Samples      # Scan directory for audio samples
```

## Sample Library

Curated collection of 1,500+ production-ready samples:

- **Kicks** - Punchy, boomy, trap, acoustic
- **Snares** - Crispy, rimshots, layered
- **808s** - Heavy subs, distorted, clean
- **Hats** - Open, closed, shakers
- **Claps** - Layered, snappy, reverb
- **Percs** - Shakers, toms, fx

All samples are hand-picked and tagged by mood (dark, hard, soft, trap, classic, etc.)

## Tiers

### Free
- 5 AI generations per day
- 30-second tracks
- Full sample library access
- Production advice

### Pro ($20/month)
- 50 generations per day
- 5-minute tracks
- Priority support

## Environment Variables

```bash
# Required for AI generation
export SOUNDRAW_API_TOKEN=your_key

# Required for sample library
export SUPABASE_URL=your_project_url
export SUPABASE_ANON_KEY=your_anon_key

# Optional (uses built-in by default)
export DEEPSEEK_API_KEY=your_key
```

## Admin: Upload Samples

To upload your curated samples to Supabase:

```bash
# Set service key (not anon key)
export SUPABASE_SERVICE_KEY=your_service_key

# Run upload script
python scripts/upload_samples.py /path/to/samples --dry-run  # Preview
python scripts/upload_samples.py /path/to/samples            # Upload
```

## Database Schema

Run this SQL in your Supabase dashboard:

```sql
-- See beat_sensei/database/supabase_client.py for full schema
CREATE TABLE samples (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    pack_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    bpm INTEGER,
    key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create storage bucket: "samples" (public)
```

## License

MIT License
