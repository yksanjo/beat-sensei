# Beat Sensei Supabase Setup - Complete Guide

## Step 1: Create Supabase Project

1. **Sign up/Login** at [supabase.com](https://supabase.com)
2. **Create New Project**:
   - Name: `beat-sensei-samples`
   - Database Password: Generate and SAVE IT
   - Region: Choose closest to you
   - Pricing Plan: **Free**
3. Wait 1-2 minutes for project creation

## Step 2: Get API Credentials

1. Go to **Project Settings** → **API**
2. Copy these 3 values:
   - **Project URL**: `https://xxxxxxxxxxxx.supabase.co`
   - **anon/public key**: Starts with `eyJ...`
   - **service_role key**: Starts with `eyJ...`

## Step 3: Configure Environment

1. Edit `./beat-sensei/.env` file:
   ```bash
   nano ./beat-sensei/.env
   ```
2. Replace placeholders with your actual values:
   ```
   SUPABASE_URL=https://your-actual-project.supabase.co
   SUPABASE_ANON_KEY=eyJ_your_actual_anon_key
   SUPABASE_SERVICE_KEY=eyJ_your_actual_service_key
   ```

## Step 4: Create Database Schema

1. Go to **Supabase Dashboard** → **SQL Editor**
2. Copy the SQL from `simple_schema.sql` and paste it
3. Click **RUN** to execute

## Step 5: Create Storage Bucket

**Option A: Using Dashboard (Recommended)**
1. Go to **Storage** → **Create New Bucket**
2. Name: `beat-sensei-samples`
3. Settings:
   - ✅ Public bucket
   - File size limit: 50MB
   - Allowed MIME types: `audio/*`
4. Click **Create Bucket**

**Option B: Using SQL** (already included in simple_schema.sql)

## Step 6: Upload Your Samples

1. **Navigate to beat-sensei directory**:
   ```bash
   cd ./beat-sensei
   ```

2. **Test your samples** (dry run):
   ```bash
   python scripts/simple_upload.py ../Desktop/samples --dry-run
   ```

3. **Actually upload**:
   ```bash
   python scripts/simple_upload.py ../Desktop/samples
   ```

## Step 7: Test the Setup

1. **Test connection**:
   ```bash
   python test_connection.py
   ```

2. **Test chatbot**:
   ```bash
   python -m beat_sensei.cli chat
   ```
   Then type: `kicks` or `search dark trap`

## Step 8: Share with Users

Users need to configure their CLI with:

```bash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_ANON_KEY=your-anon-key
```

Or create a `~/.beat-sensei/config.json`:
```json
{
  "supabase_url": "https://your-project.supabase.co",
  "supabase_anon_key": "your-anon-key"
}
```

## Troubleshooting

### "Could not connect to Supabase"
- Check `.env` file credentials
- Verify project is active in Supabase dashboard
- Test with: `curl https://your-project.supabase.co/rest/v1/`

### "Storage bucket not found"
- Create bucket in Storage section
- Ensure it's set to "Public"

### "Permission denied" on upload
- You need `SUPABASE_SERVICE_KEY` (not anon key)
- Service key has admin privileges

### Samples not playing
- Storage bucket must be "Public"
- Check file URLs in database

## Next Steps

1. **Upload more samples** from different folders
2. **Test search functionality** in chatbot
3. **Share your project URL** with other users
4. **Monitor usage** in Supabase dashboard

## Support

- Supabase Docs: https://supabase.com/docs
- Beat Sensei GitHub: (your repo link)
- Community: (your community link)