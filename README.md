# Beat-Sensei

Your AI Sample Master - A terminal chatbot for beat production.

```
 ____  _____    _  _____   ____  _____ _   _ ____  _____ ___
| __ )| ____|  / \|_   _| / ___|| ____| \ | / ___|| ____|_ _|
|  _ \|  _|   / _ \ | |   \___ \|  _| |  \| \___ \|  _|  | |
| |_) | |___ / ___ \| |    ___) | |___| |\  |___) | |___ | |
|____/|_____/_/   \_\_|   |____/|_____|_| \_|____/|_____|___|
```

Beat-Sensei is a hip-hop producer mentor chatbot that helps you discover samples from your local library and generate new ones using AI.

## Features

- **Smart Sample Search** - Find samples by description ("dusty soul chops", "dark 808 bass")
- **Audio Preview** - Play samples directly in your terminal
- **AI Generation** - Create custom samples using MusicGen (Pro tier)
- **Hip-Hop Mentor** - Get advice from an OG producer personality
- **Local Library Indexing** - Scan and organize your sample folders

## Quick Start

```bash
# Install
cd beat-sensei
pip install -e ".[full]"

# Scan your sample folder
beat-sensei scan ~/Downloads/beat\ sensei

# Start chatting
beat-sensei
```

## Commands

### Interactive Mode

```bash
beat-sensei              # Start chat
beat-sensei --scan <folder>  # Scan folder before starting
```

### Quick Commands

```bash
beat-sensei scan <folder>     # Index a sample folder
beat-sensei search "query"    # Quick search
beat-sensei play <file>       # Play a file
beat-sensei generate "desc"   # Generate sample (Pro)
beat-sensei config            # View configuration
```

### In-Chat Commands

| Command | Description |
|---------|-------------|
| `search <query>` | Search for samples |
| `play <number>` | Play from search results |
| `stop` | Stop playback |
| `generate <desc>` | Generate new sample (Pro) |
| `random` | Get random inspiration |
| `help` | Show help |
| `quit` | Exit |

## Configuration

Configuration is stored in `config/config.yaml`:

```yaml
sample_folders:
  - /Users/you/Downloads/beat sensei

output_folder: ~/Music/BeatSensei/Generated

preferences:
  default_bpm: 90
  audio_format: wav
```

## Environment Variables

For AI features, set these in your shell or `.env` file:

```bash
# For AI sample generation (Pro)
export REPLICATE_API_TOKEN=your_token_here

# For enhanced chatbot (optional)
export OPENAI_API_KEY=your_key_here
```

## Tiers

### Free
- Unlimited local sample search
- Audio preview
- Sample analysis

### Pro ($19/month)
- AI-powered sample generation
- 100 generations/month
- Commercial licensing

## Sample Organization

Beat-Sensei auto-categorizes samples:
- **drums** - kicks, snares, hats, percussion
- **bass** - 808s, sub bass, bass lines
- **melody** - synths, keys, guitars, leads
- **vocal** - vocals, chops, choirs
- **fx** - risers, impacts, transitions
- **loop** - full loops and beats
- **sample** - general samples and chops

## Example Session

```
$ beat-sensei

 BEAT-SENSEI v1.0
 Your AI Sample Master | Hip-Hop Edition

 Sample Library: 847 samples indexed
 Tier: Free (Search & Preview)

Sensei: Yo, what's good! Ready to dig through the crates?

You: I need something dusty for a boom bap beat

Sensei: Classic vibes, I respect that. Let me check the stash...

Found Samples:
 # | Filename                    | BPM | Key     | Category
---+-----------------------------+-----+---------+---------
 1 | soul_chop_dusty_Am.wav      | 92  | A minor | sample
 2 | vinyl_loop_vintage.wav      | 88  | D minor | loop
 3 | jazz_piano_warm.wav         | 95  | G major | melody

You: play 1

Sensei: Let's hear what we got...
Now playing: soul_chop_dusty_Am.wav

You: that's fire! generate something similar but darker

Sensei: Bet, firing up the AI...
Done! Saved to: ~/Music/BeatSensei/Generated/dark_soul_Am_001.wav
```

## License

MIT License
