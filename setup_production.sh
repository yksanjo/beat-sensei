#!/bin/bash

# Beat Sensei Production Setup Script
# Complete setup for enterprise-ready sample library

set -e

echo "🚀 Beat Sensei Production Setup"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_step() { echo -e "\n${YELLOW}▶ $1${NC}"; }

# Check for required tools
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

print_step "1. Checking dependencies..."
check_command python3
check_command pip3

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
    print_warning "Python 3.8+ recommended (found $PYTHON_VERSION)"
fi

print_step "2. Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

source venv/bin/activate

print_step "3. Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dependencies installed"

print_step "4. Checking environment configuration..."
if [ ! -f ".env" ]; then
    print_error ".env file not found"
    echo ""
    echo "Please create .env file from .env.example:"
    echo "  cp .env.example .env"
    echo ""
    echo "Then edit .env with your Supabase credentials:"
    echo "  1. SUPABASE_URL from Supabase Dashboard → Settings → API"
    echo "  2. SUPABASE_ANON_KEY (public key)"
    echo "  3. SUPABASE_SERVICE_KEY (private key)"
    echo ""
    exit 1
fi

# Check if .env has placeholder values
if grep -q "your-project-id.supabase.co" .env || \
   grep -q "your-anon-key-here" .env || \
   grep -q "your-service-role-key-here" .env; then
    print_error ".env file contains placeholder values"
    echo ""
    echo "Please update .env with your actual Supabase credentials"
    exit 1
fi

print_success "Environment configured"

print_step "5. Testing Supabase connection..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

url = os.getenv('SUPABASE_URL')
anon_key = os.getenv('SUPABASE_ANON_KEY')

if not url or not anon_key:
    print('❌ Missing credentials in .env')
    exit(1)

print(f'✅ Credentials found')
print(f'   URL: {url}')
"

print_step "6. Database schema setup..."
echo ""
echo "📋 You need to set up the database schema in Supabase:"
echo ""
echo "Option A: Simple schema (basic features)"
echo "  1. Go to Supabase Dashboard → SQL Editor"
echo "  2. Copy contents of simple_schema.sql"
echo "  3. Click RUN"
echo ""
echo "Option B: Enhanced schema (production features)"
echo "  1. Go to Supabase Dashboard → SQL Editor"
echo "  2. Copy contents of enhanced_schema.sql"
echo "  3. Click RUN"
echo "  4. This adds user tracking, analytics, and tier management"
echo ""
read -p "Have you set up the database schema? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Please set up database schema before continuing"
    echo "You can run the migration script later:"
    echo "  python scripts/migrate_schema.py"
fi

print_step "7. Storage bucket setup..."
echo ""
echo "📦 You need to create a storage bucket in Supabase:"
echo ""
echo "1. Go to Supabase Dashboard → Storage"
echo "2. Click 'Create New Bucket'"
echo "3. Name: beat-sensei-samples"
echo "4. Settings:"
echo "   - ✅ Public bucket"
echo "   - File size limit: 50MB"
echo "   - Allowed MIME types: audio/*"
echo "5. Click 'Create Bucket'"
echo ""
read -p "Have you created the storage bucket? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Please create storage bucket before uploading samples"
fi

print_step "8. Sample preparation..."
echo ""
echo "🎵 You have 53 audio files in ./Desktop/samples/"
echo ""
echo "Recommended workflow:"
echo "  1. Validate files: python scripts/validate_samples.py ../Desktop/samples"
echo "  2. Organize files: python scripts/organize_samples.py ../Desktop/samples --dry-run"
echo "  3. Then execute: python scripts/organize_samples.py ../Desktop/samples --execute"
echo "  4. Upload organized files"
echo ""
read -p "Do you want to validate your samples now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python scripts/validate_samples.py ../Desktop/samples
fi

print_step "9. Upload strategy..."
echo ""
echo "📤 Recommended upload approach:"
echo ""
echo "PHASE 1: Test with one sample"
echo "  python scripts/simple_upload.py ../Desktop/samples --limit 1"
echo "  python scripts/verify_upload.py"
echo ""
echo "PHASE 2: Upload by category"
echo "  python scripts/simple_upload.py ./organized_samples/kicks"
echo "  python scripts/verify_upload.py"
echo ""
echo "PHASE 3: Bulk upload"
echo "  python scripts/simple_upload.py ./organized_samples"
echo "  python scripts/verify_upload.py"
echo ""

print_step "10. Testing..."
echo ""
echo "🔧 After upload, test the system:"
echo ""
echo "1. Verify upload: python scripts/verify_upload.py"
echo "2. Test chatbot: python -m beat_sensei.cli chat"
echo "   Commands to try:"
echo "   - 'kicks' or 'snares' (browse categories)"
echo "   - 'search dark trap' (search)"
echo "   - 'random' (get random samples)"
echo "3. Test API: python scripts/test_connection.py"
echo ""

print_step "11. Production considerations..."
echo ""
echo "🏢 For enterprise/B2B use:"
echo ""
echo "1. Rate limiting: Configure in .env"
echo "   RATE_LIMIT_PER_HOUR=1000"
echo "   RATE_LIMIT_PER_MINUTE=60"
echo ""
echo "2. CDN: Enable in Supabase Dashboard → Storage → Settings"
echo ""
echo "3. Monitoring:"
echo "   - Supabase Dashboard → Logs"
echo "   - Storage usage"
echo "   - Database performance"
echo ""
echo "4. Backup strategy:"
echo "   - Supabase automated backups"
echo "   - Export sample metadata regularly"
echo ""

print_step "12. User onboarding..."
echo ""
echo "👥 To share with users:"
echo ""
echo "Users need these environment variables:"
echo "  export SUPABASE_URL=https://your-project.supabase.co"
echo "  export SUPABASE_ANON_KEY=your-anon-key"
echo ""
echo "Or create ~/.beat-sensei/config.json:"
echo '  {'
echo '    "supabase_url": "https://your-project.supabase.co",'
echo '    "supabase_anon_key": "your-anon-key"'
echo '  }'
echo ""

echo "=========================================="
print_success "Setup instructions complete!"
echo ""
echo "📚 Documentation:"
echo "  - SCRIPTS_README.md - Detailed script usage"
echo "  - SETUP_GUIDE.md - Step-by-step guide"
echo "  - README_SUPABASE_SETUP.md - Supabase specifics"
echo ""
echo "🚀 Next steps:"
echo "  1. Set up database schema in Supabase SQL Editor"
echo "  2. Create storage bucket"
echo "  3. Validate and organize your samples"
echo "  4. Test upload with one sample"
echo "  5. Bulk upload and verify"
echo ""
echo "💡 Tip: Use the scripts in this order:"
echo "  validate → organize → upload → verify → test"
echo ""

# Create a quick reference card
cat > QUICK_REFERENCE.md << 'EOF'
# Quick Reference

## Essential Commands

### Validation & Organization
python scripts/validate_samples.py ../Desktop/samples
python scripts/organize_samples.py ../Desktop/samples --execute

### Upload
python scripts/simple_upload.py ./organized_samples --limit 1  # Test
python scripts/simple_upload.py ./organized_samples             # Bulk

### Verification
python scripts/verify_upload.py
python -m beat_sensei.cli chat

### Database
python scripts/migrate_schema.py

## Key Files
- `.env` - Supabase credentials
- `simple_schema.sql` - Basic database schema
- `enhanced_schema.sql` - Production schema
- `requirements.txt` - Python dependencies

## Troubleshooting
1. Check .env credentials
2. Verify storage bucket is Public
3. Run verify_upload.py
4. Check Supabase Dashboard logs
EOF

print_success "Quick reference created: QUICK_REFERENCE.md"
echo ""
echo "🎵 Happy sampling!"