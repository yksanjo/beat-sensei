# Beat Sensei - Supabase Backend Setup Guide

## Complete Supabase Backend Infrastructure

This guide provides everything you need to set up the Beat Sensei backend on Supabase.

## 1. Database Schema

The complete SQL schema is in `supabase_schema.sql`. This includes:

### Tables:
- `samples` - Main sample metadata
- `sample_metadata` - Extended audio analysis metadata  
- `user_preferences` - User preferences for recommendations
- `recommendations` - User-sample interaction tracking
- `api_keys` - CLI authentication and rate limiting
- `download_logs` - Download analytics

### Features:
- Full-text search with PostgreSQL vectors
- Row Level Security (RLS) policies
- Automatic timestamp updates
- Recommendation engine functions
- Trending samples calculation
- Advanced search functions

## 2. Storage Bucket Setup

### Create Storage Bucket:
```bash
# Using Supabase Dashboard:
1. Go to Storage → Create New Bucket
2. Name: "beat-sensei-samples"
3. Set as Public
4. File size limit: 50MB
5. Allowed MIME types: audio/*

# Or using SQL:
SELECT storage.create_bucket(
  'beat-sensei-samples',
  '{"public": true, "file_size_limit": 52428800, "allowed_mime_types": ["audio/*"]}'
);
```

### Configure CORS for CLI Access:
```sql
-- Update CORS configuration
UPDATE storage.buckets
SET cors_origins = ARRAY['*']
WHERE name = 'beat-sensei-samples';
```

## 3. Upload Scripts

### Simple Upload Script (`scripts/simple_upload.py`):
```bash
# Install dependencies
pip install supabase python-dotenv tqdm

# Set environment variables
export SUPABASE_URL=your_project_url
export SUPABASE_SERVICE_KEY=your_service_role_key

# Run upload
python scripts/simple_upload.py /Users/yoshikondo/Desktop/samples
```

### Enhanced Upload with Audio Analysis:
```bash
# Install audio analysis dependencies
pip install librosa soundfile

# Run enhanced upload
python scripts/upload_with_audio_analysis.py /Users/yoshikondo/Desktop/samples
```

## 4. Edge Functions

### Available Edge Functions:
1. **get-sample-recommendations** - Personalized recommendations
2. **search-samples** - Full-text search with filters
3. **get-trending-samples** - Trending/popular samples
4. **get-samples-by-filter** - Advanced filtering

### Deploy Edge Functions:
```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Deploy each function
supabase functions deploy get-sample-recommendations
supabase functions deploy search-samples
supabase functions deploy get-trending-samples
supabase functions deploy get-samples-by-filter
```

## 5. Environment Variables

### Required Environment Variables:
```bash
# For CLI/Upload Scripts
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# For Edge Functions (set in Supabase Dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## 6. CLI Integration

### Example CLI Client (`cli_integration_example.py`):
```python
# Install dependencies
pip install supabase python-dotenv rich typer requests

# Set environment variables
export SUPABASE_URL=your_project_url
export SUPABASE_ANON_KEY=your_anon_key
export BEAT_SENSEI_API_KEY=your_api_key

# Run CLI commands
python cli_integration_example.py search --query "hiphop" --bpm-range "80-120"
python cli_integration_example.py trending --timeframe week --limit 10
python cli_integration_example.py download sample-uuid-here --output ./samples
```

### API Key Generation:
```sql
-- Generate API key for CLI
INSERT INTO api_keys (name, key_hash, user_id, rate_limit_per_hour)
VALUES (
  'CLI User',
  crypt('generated-api-key-here', gen_salt('bf')),
  'user-id-here',
  1000
);
```

## 7. CDN Configuration

### Supabase CDN Setup:
1. **Enable CDN** in Supabase Dashboard → Storage → Settings
2. **Cache Headers** for audio files:
   - Cache-Control: public, max-age=31536000, immutable
   - Content-Type: audio/*
3. **Global Distribution**: Supabase CDN automatically distributes to:
   - North America (us-east-1, us-west-2)
   - Europe (eu-west-1, eu-central-1)
   - Asia Pacific (ap-southeast-1)

### Optimize for Low Latency:
```sql
-- Set cache headers for storage bucket
UPDATE storage.buckets
SET public = true,
    file_size_limit = 52428800,
    allowed_mime_types = ARRAY['audio/*']
WHERE name = 'beat-sensei-samples';
```

## 8. Initial Upload Process

### Step-by-Step Upload:
1. **Prepare Samples Directory**:
   ```bash
   # Check your samples
   ls -la /Users/yoshikondo/Desktop/samples/
   ```

2. **Run Initial Scan**:
   ```bash
   python scripts/simple_upload.py /Users/yoshikondo/Desktop/samples --dry-run
   ```

3. **Upload Samples**:
   ```bash
   python scripts/simple_upload.py /Users/yoshikondo/Desktop/samples
   ```

4. **Verify Upload**:
   ```sql
   -- Check uploaded samples
   SELECT COUNT(*) as total_samples,
          SUM(file_size) as total_size_mb,
          AVG(bpm) as avg_bpm
   FROM samples;
   ```

## 9. Testing the Backend

### Test Edge Functions:
```bash
# Test search function
curl -X POST https://your-project.supabase.co/functions/v1/search-samples \
  -H "Authorization: Bearer your-anon-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "hiphop", "limit": 5}'

# Test recommendations
curl -X POST https://your-project.supabase.co/functions/v1/get-sample-recommendations \
  -H "Authorization: Bearer your-anon-key" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "limit": 10}'
```

### Test Storage Access:
```bash
# Get public URL for a sample
curl https://your-project.supabase.co/storage/v1/object/public/beat-sensei-samples/sample-file.wav
```

## 10. Monitoring and Analytics

### Database Views:
```sql
-- Sample statistics
SELECT * FROM sample_statistics;

-- Daily download stats
SELECT * FROM daily_download_stats;

-- Trending samples
SELECT * FROM get_trending_samples(10);
```

### Rate Limiting:
- API keys have rate limits (default: 100 requests/hour)
- Download logs track usage patterns
- RLS policies prevent unauthorized access

## 11. Troubleshooting

### Common Issues:

1. **Upload Fails - File Too Large**:
   - Check file size limit (50MB)
   - Compress or split large files

2. **Authentication Errors**:
   - Verify SUPABASE_SERVICE_KEY has proper permissions
   - Check RLS policies

3. **Storage Access Denied**:
   - Ensure bucket is public
   - Verify CORS settings

4. **Edge Function Timeouts**:
   - Increase timeout in function configuration
   - Optimize database queries with indexes

### Performance Tips:
1. Create appropriate indexes for common queries
2. Use connection pooling for high traffic
3. Implement caching for frequently accessed samples
4. Monitor database performance with Supabase Analytics

## 12. Security Considerations

### Best Practices:
1. **Never expose service role key in client-side code**
2. **Use API keys for CLI authentication**
3. **Implement rate limiting per API key**
4. **Regularly rotate API keys**
5. **Monitor download logs for suspicious activity**
6. **Keep Supabase project updated**

### Data Protection:
- User preferences are private (RLS protected)
- Download logs are service-role only
- API keys are hashed in database
- Public read access for samples only

## Support

For issues or questions:
1. Check Supabase Dashboard for error logs
2. Review Edge Function logs in Supabase
3. Test with smaller dataset first
4. Consult Supabase documentation

This backend provides a scalable, secure foundation for the Beat Sensei CLI tool with global CDN distribution, advanced search capabilities, and personalized recommendations.