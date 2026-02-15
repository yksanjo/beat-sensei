# Beat Sensei - Scripts Overview

## 📁 Scripts Directory Structure

```
scripts/
├── validate_samples.py      # Validate audio files before upload
├── organize_samples.py      # Organize files into categories
├── simple_upload.py         # Basic upload to Supabase
├── upload_samples.py        # Advanced upload with metadata
├── verify_upload.py         # Verify upload success
├── migrate_schema.py        # Database schema migrations
└── README.md               # This file
```

## 🚀 Quick Start Workflow

### Phase 1: Preparation
```bash
# 1. Validate your samples
python scripts/validate_samples.py ../Desktop/samples

# 2. Organize into categories (optional but recommended)
python scripts/organize_samples.py ../Desktop/samples --dry-run
python scripts/organize_samples.py ../Desktop/samples --execute

# Output: ./organized_samples/ with categorized folders
```

### Phase 2: Setup & Upload
```bash
# 3. Set up Supabase (if not done)
#    - Create project at supabase.com
#    - Update .env with credentials
#    - Run SQL schema in Supabase SQL Editor

# 4. Test upload with ONE sample first
python scripts/simple_upload.py ./organized_samples/kicks --dry-run
python scripts/simple_upload.py ./organized_samples/kicks --limit 1

# 5. Verify the upload worked
python scripts/verify_upload.py

# 6. Bulk upload all samples
python scripts/simple_upload.py ./organized_samples
```

### Phase 3: Verification & Testing
```bash
# 7. Test chatbot integration
python -m beat_sensei.cli chat
# Type: kicks
# Type: search dark
# Type: random

# 8. Test with users
# Share your SUPABASE_URL and SUPABASE_ANON_KEY
```

## 📋 Script Details

### 1. `validate_samples.py`
**Purpose**: Check audio files before upload
```bash
python scripts/validate_samples.py <directory>
```
**Checks**:
- File formats (.wav, .mp3, .aiff, etc.)
- File size (< 50MB)
- Metadata extraction (BPM, key, tags)
- Organization suggestions

### 2. `organize_samples.py`
**Purpose**: Organize files into categorized folders
```bash
# Dry run (preview)
python scripts/organize_samples.py <directory> --dry-run

# Execute
python scripts/organize_samples.py <directory> --execute --output ./organized
```
**Creates structure**:
```
organized/
├── kicks/
├── snares/
├── hats/
├── 808s/
├── loops/
└── fx/
```

### 3. `simple_upload.py`
**Purpose**: Upload samples to Supabase
```bash
# Dry run
python scripts/simple_upload.py <directory> --dry-run

# Upload first 5 samples
python scripts/simple_upload.py <directory> --limit 5

# Full upload
python scripts/simple_upload.py <directory>
```
**Features**:
- Automatic metadata extraction
- Duplicate detection (by file hash)
- Progress bar with tqdm
- Error handling and retries

### 4. `upload_samples.py`
**Purpose**: Advanced upload with better metadata
```bash
python scripts/upload_samples.py <directory>
```
**Additional features**:
- Better category detection
- Mood tagging
- BPM/key extraction from audio analysis (if librosa installed)
- Organized storage paths

### 5. `verify_upload.py`
**Purpose**: Verify upload was successful
```bash
python scripts/verify_upload.py
```
**Checks**:
- Database connection
- Storage bucket access
- File URLs are accessible
- Metadata consistency
- Search functionality

### 6. `migrate_schema.py`
**Purpose**: Database schema migrations
```bash
python scripts/migrate_schema.py
```
**Options**:
- Initial schema setup
- Upgrade from simple to enhanced schema
- Schema verification

## 🎯 Best Practices

### 1. **Start Small**
```bash
# Test with one category first
python scripts/simple_upload.py ./organized_samples/kicks --limit 3
python scripts/verify_upload.py
```

### 2. **Use Dry Runs**
```bash
# Always dry run first
python scripts/validate_samples.py <dir>
python scripts/organize_samples.py <dir> --dry-run
python scripts/simple_upload.py <dir> --dry-run
```

### 3. **Organize Before Upload**
- Better organization = better metadata
- Categorized folders help with pack naming
- Clean filenames improve search

### 4. **Verify After Upload**
```bash
# Always verify
python scripts/verify_upload.py

# Test search
python -m beat_sensei.cli chat
> search kick
```

### 5. **Monitor Supabase Dashboard**
- Check Storage → `beat-sensei-samples` bucket
- Check Database → `samples` table
- Monitor API usage in Logs

## 🔧 Troubleshooting

### "File too large"
- Max file size: 50MB
- Compress or split large files
- Update `MAX_FILE_SIZE_MB` in `.env`

### "Storage bucket not found"
```bash
# Create bucket in Supabase Dashboard:
1. Go to Storage
2. Create New Bucket
3. Name: beat-sensei-samples
4. Set to Public
5. File size: 50MB
6. MIME types: audio/*
```

### "Permission denied"
- Need `SUPABASE_SERVICE_KEY` for uploads
- Anon key is for read-only access
- Check `.env` file has correct service key

### "No samples found in search"
- Verify metadata was extracted
- Check tags in database
- Re-upload with better filenames

## 📊 Sample Naming Convention

### Good Examples:
```
Kick_Dark_120BPM_Am.wav
Snare_Trap_Crispy.wav
808_Sub_Bass_Distorted.wav
Melody_Ambient_Pad_Cm.wav
FX_Riser_Dark_Sweep.wav
```

### Includes:
1. **Category**: Kick, Snare, 808, Melody, FX
2. **Descriptor**: Dark, Crispy, Distorted, Ambient
3. **BPM**: 120BPM (if applicable)
4. **Key**: Am, Cm, F# (if applicable)
5. **Format**: .wav, .mp3

## 🚀 Production Deployment Checklist

- [ ] `.env` file configured with production credentials
- [ ] Database schema deployed (`enhanced_schema.sql`)
- [ ] Storage bucket created and set to Public
- [ ] Samples uploaded and verified
- [ ] Chatbot tested with various queries
- [ ] Rate limits configured in `.env`
- [ ] CDN enabled in Supabase Storage settings
- [ ] Backup strategy in place (Supabase backups)
- [ ] Monitoring set up (Supabase logs, error tracking)

## 📞 Support

- **Validation issues**: Check file formats, sizes
- **Upload issues**: Verify `.env` credentials, storage bucket
- **Search issues**: Check metadata, re-upload with better names
- **Performance issues**: Check indexes, use CDN

## 🔄 Update Workflow

When adding new samples:
```bash
1. python scripts/validate_samples.py ./new_samples
2. python scripts/organize_samples.py ./new_samples --execute
3. python scripts/simple_upload.py ./organized_new_samples
4. python scripts/verify_upload.py
5. Test: python -m beat_sensei.cli chat
```