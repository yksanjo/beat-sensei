#!/bin/bash

# Beat Sensei Supabase Setup Script
# This script helps set up the Supabase backend for Beat Sensei

set -e

echo "🎵 Beat Sensei Supabase Setup"
echo "=============================="

# Check for required tools
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        exit 1
    fi
}

echo "Checking dependencies..."
check_command python3
check_command pip3
check_command curl
check_command jq

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install supabase python-dotenv tqdm rich typer requests librosa soundfile numpy

# Check for .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found."
    echo "Please copy .env.example to .env and fill in your Supabase credentials."
    echo ""
    echo "You can get your credentials from:"
    echo "1. Go to Supabase Dashboard → Settings → API"
    echo "2. Copy Project URL (SUPABASE_URL)"
    echo "3. Copy anon/public key (SUPABASE_ANON_KEY)"
    echo "4. Copy service_role key (SUPABASE_SERVICE_KEY)"
    echo ""
    read -p "Do you want to create .env file now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your credentials."
        exit 0
    else
        echo "Please create .env file manually and run this script again."
        exit 1
    fi
fi

# Load environment variables
source .env

# Test Supabase connection
echo "Testing Supabase connection..."
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ SUPABASE_URL or SUPABASE_ANON_KEY not set in .env"
    exit 1
fi

# Test connection with curl
response=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "apikey: $SUPABASE_ANON_KEY" \
    -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
    "$SUPABASE_URL/rest/v1/")

if [ "$response" != "200" ]; then
    echo "❌ Failed to connect to Supabase. HTTP code: $response"
    echo "Please check your credentials in .env"
    exit 1
fi

echo "✅ Successfully connected to Supabase!"

# Create storage bucket if it doesn't exist
echo "Checking storage bucket..."
bucket_response=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "apikey: $SUPABASE_SERVICE_KEY" \
    -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" \
    "$SUPABASE_URL/storage/v1/bucket/$STORAGE_BUCKET")

if [ "$bucket_response" != "200" ]; then
    echo "Storage bucket '$STORAGE_BUCKET' not found."
    read -p "Do you want to create it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating storage bucket..."
        curl -X POST "$SUPABASE_URL/storage/v1/bucket" \
            -H "apikey: $SUPABASE_SERVICE_KEY" \
            -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" \
            -H "Content-Type: application/json" \
            -d "{
                \"name\": \"$STORAGE_BUCKET\",
                \"id\": \"$STORAGE_BUCKET\",
                \"public\": true,
                \"file_size_limit\": $((MAX_FILE_SIZE_MB * 1024 * 1024)),
                \"allowed_mime_types\": [\"audio/*\"]
            }"
        echo "✅ Storage bucket created!"
    fi
else
    echo "✅ Storage bucket exists!"
fi

# Execute SQL schema
echo "Setting up database schema..."
if [ -f "supabase_schema.sql" ]; then
    echo "Executing SQL schema..."
    # Note: In production, you would use the Supabase SQL Editor or migrations
    echo "Please execute the SQL in supabase_schema.sql manually in:"
    echo "Supabase Dashboard → SQL Editor"
    echo ""
    echo "Or use the Supabase CLI:"
    echo "supabase db reset"
else
    echo "❌ supabase_schema.sql not found!"
    exit 1
fi

# Create upload script executable
chmod +x scripts/simple_upload.py
chmod +x scripts/upload_with_audio_analysis.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Execute the SQL schema in supabase_schema.sql"
echo "2. Deploy Edge Functions (see README_SUPABASE_SETUP.md)"
echo "3. Upload your samples:"
echo "   python scripts/simple_upload.py /path/to/your/samples"
echo ""
echo "For detailed instructions, see README_SUPABASE_SETUP.md"

# Create a test script
cat > test_connection.py << 'EOF'
#!/usr/bin/env python3
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')

if not url or not key:
    print("❌ Environment variables not set")
    exit(1)

try:
    supabase = create_client(url, key)
    
    # Test connection by getting sample count
    response = supabase.table('samples').select('id', count='exact').execute()
    
    print(f"✅ Connection successful!")
    print(f"📊 Sample count: {response.count}")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
EOF

chmod +x test_connection.py
echo ""
echo "You can test your connection with: python test_connection.py"