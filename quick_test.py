#!/usr/bin/env python3
"""Quick test for Supabase setup."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_env_vars():
    """Test environment variables."""
    print("🔍 Testing environment variables...")
    
    url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    errors = []
    
    if not url or url == 'https://your-project-id.supabase.co':
        errors.append("SUPABASE_URL not set or using placeholder")
    
    if not anon_key or anon_key == 'your-anon-key-here':
        errors.append("SUPABASE_ANON_KEY not set or using placeholder")
    
    if not service_key or service_key == 'your-service-role-key-here':
        errors.append("SUPABASE_SERVICE_KEY not set or using placeholder")
    
    if errors:
        print("❌ Errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✅ Environment variables OK")
    return True

def test_supabase_connection():
    """Test connection to Supabase."""
    print("\n🔗 Testing Supabase connection...")
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        client = create_client(url, anon_key)
        
        # Test connection by getting tables
        response = client.table('samples').select('id', count='exact').limit(1).execute()
        
        print(f"✅ Connected to Supabase!")
        print(f"📊 Sample count: {response.count}")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_storage():
    """Test storage bucket."""
    print("\n📦 Testing storage bucket...")
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        client = create_client(url, service_key)
        
        # List buckets
        buckets = client.storage.list_buckets()
        
        bucket_names = [b.name for b in buckets]
        
        if 'beat-sensei-samples' in bucket_names:
            print("✅ Storage bucket 'beat-sensei-samples' exists")
            return True
        else:
            print("❌ Storage bucket 'beat-sensei-samples' not found")
            print(f"Available buckets: {bucket_names}")
            return False
            
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False

def main():
    print("🚀 Beat Sensei Supabase Setup Test")
    print("=" * 40)
    
    # Test 1: Environment variables
    if not test_env_vars():
        print("\n💡 Fix your .env file first!")
        sys.exit(1)
    
    # Test 2: Supabase connection
    if not test_supabase_connection():
        print("\n💡 Check your credentials and database schema")
        sys.exit(1)
    
    # Test 3: Storage
    test_storage()
    
    print("\n" + "=" * 40)
    print("🎉 Setup looks good!")
    print("\nNext steps:")
    print("1. Upload samples: python scripts/simple_upload.py ../Desktop/samples")
    print("2. Test chatbot: python -m beat_sensei.cli chat")
    print("3. Type 'kicks' or 'search dark trap' in chatbot")

if __name__ == '__main__':
    main()