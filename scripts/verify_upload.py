#!/usr/bin/env python3
"""
Verify uploaded samples in Supabase.
Checks file accessibility, metadata consistency, and download functionality.
"""

import os
import sys
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client():
    """Get Supabase client."""
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not anon_key:
            print("❌ SUPABASE_URL or SUPABASE_ANON_KEY not set in .env")
            sys.exit(1)
        
        return create_client(url, anon_key)
    except ImportError:
        print("❌ supabase package not installed. Run: pip install supabase")
        sys.exit(1)

def verify_database_connection(client) -> bool:
    """Verify database connection and table structure."""
    print("🔗 Verifying database connection...")
    
    try:
        # Check if samples table exists and has data
        response = client.table('samples').select('id', count='exact').limit(1).execute()
        
        print(f"✅ Database connected")
        print(f"📊 Total samples in database: {response.count}")
        
        if response.count == 0:
            print("⚠️  Database is empty - no samples found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def verify_storage_access(client) -> bool:
    """Verify storage bucket access."""
    print("\n📦 Verifying storage bucket...")
    
    try:
        # List buckets
        buckets = client.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        target_bucket = os.getenv('STORAGE_BUCKET', 'beat-sensei-samples')
        
        if target_bucket not in bucket_names:
            print(f"❌ Storage bucket '{target_bucket}' not found")
            print(f"Available buckets: {bucket_names}")
            return False
        
        print(f"✅ Storage bucket '{target_bucket}' exists")
        
        # Check bucket is public
        # Note: This requires service role key for detailed bucket info
        print("⚠️  Note: Verify bucket is set to 'Public' in Supabase Dashboard → Storage")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage verification failed: {e}")
        return False

def verify_sample_files(client, limit: int = 10) -> Dict[str, Any]:
    """Verify sample files are accessible via URLs."""
    print(f"\n🔍 Verifying sample files (checking {limit} samples)...")
    
    try:
        # Get some samples from database
        response = client.table('samples').select('id, filename, file_url, file_size').limit(limit).execute()
        
        if not response.data:
            print("❌ No samples found in database")
            return {'checked': 0, 'accessible': 0, 'failed': 0, 'errors': []}
        
        results = {
            'checked': 0,
            'accessible': 0,
            'failed': 0,
            'errors': []
        }
        
        for sample in response.data:
            results['checked'] += 1
            file_url = sample['file_url']
            filename = sample['filename']
            
            try:
                # Make HEAD request to check file accessibility
                head_response = requests.head(file_url, timeout=10)
                
                if head_response.status_code == 200:
                    # Check content type
                    content_type = head_response.headers.get('content-type', '')
                    if content_type.startswith('audio/'):
                        results['accessible'] += 1
                        print(f"  ✅ {filename}: Accessible ({content_type})")
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"{filename}: Wrong content type: {content_type}")
                        print(f"  ⚠️  {filename}: Wrong content type: {content_type}")
                else:
                    results['failed'] += 1
                    results['errors'].append(f"{filename}: HTTP {head_response.status_code}")
                    print(f"  ❌ {filename}: HTTP {head_response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                results['failed'] += 1
                results['errors'].append(f"{filename}: {str(e)}")
                print(f"  ❌ {filename}: {e}")
        
        return results
        
    except Exception as e:
        print(f"❌ Sample verification failed: {e}")
        return {'checked': 0, 'accessible': 0, 'failed': 0, 'errors': [str(e)]}

def verify_metadata_consistency(client, limit: int = 5) -> Dict[str, Any]:
    """Verify metadata consistency between expected and actual."""
    print(f"\n📋 Verifying metadata consistency (checking {limit} samples)...")
    
    try:
        # Get samples with metadata
        response = client.table('samples').select('id, filename, bpm, key, tags, file_size').limit(limit).execute()
        
        results = {
            'checked': 0,
            'complete': 0,
            'incomplete': 0,
            'warnings': []
        }
        
        for sample in response.data:
            results['checked'] += 1
            
            warnings = []
            filename = sample['filename']
            
            # Check for essential metadata
            if not sample.get('bpm'):
                warnings.append("Missing BPM")
            
            if not sample.get('key'):
                warnings.append("Missing key")
            
            if not sample.get('tags') or len(sample['tags']) == 0:
                warnings.append("No tags")
            
            if warnings:
                results['incomplete'] += 1
                results['warnings'].append(f"{filename}: {', '.join(warnings)}")
                print(f"  ⚠️  {filename}: {', '.join(warnings)}")
            else:
                results['complete'] += 1
                print(f"  ✅ {filename}: Metadata complete")
        
        return results
        
    except Exception as e:
        print(f"❌ Metadata verification failed: {e}")
        return {'checked': 0, 'complete': 0, 'incomplete': 0, 'warnings': [str(e)]}

def verify_search_functionality(client) -> bool:
    """Verify search functionality works."""
    print("\n🔎 Verifying search functionality...")
    
    try:
        # Test simple search
        response = client.table('samples').select('id, filename').limit(3).execute()
        
        if not response.data:
            print("⚠️  No samples to test search")
            return False
        
        # Get a sample to test search with
        sample = response.data[0]
        filename = sample['filename']
        
        # Extract a word from filename for search
        words = filename.replace('_', ' ').replace('-', ' ').split()
        if words:
            search_term = words[0].lower()
            
            # Try to search for this term
            search_response = client.table('samples').select('id, filename').ilike('filename', f'%{search_term}%').limit(3).execute()
            
            if search_response.data:
                print(f"✅ Search works (found {len(search_response.data)} results for '{search_term}')")
                return True
            else:
                print(f"⚠️  Search returned no results for '{search_term}'")
                return False
        
        print("⚠️  Could not extract search term from filename")
        return False
        
    except Exception as e:
        print(f"❌ Search verification failed: {e}")
        return False

def generate_report(
    db_ok: bool,
    storage_ok: bool,
    files_result: Dict[str, Any],
    metadata_result: Dict[str, Any],
    search_ok: bool
) -> bool:
    """Generate verification report."""
    print("\n" + "=" * 60)
    print("📊 VERIFICATION REPORT")
    print("=" * 60)
    
    overall_success = True
    
    # Database
    print(f"\n📁 DATABASE: {'✅ OK' if db_ok else '❌ FAILED'}")
    if not db_ok:
        overall_success = False
    
    # Storage
    print(f"📦 STORAGE: {'✅ OK' if storage_ok else '❌ FAILED'}")
    if not storage_ok:
        overall_success = False
    
    # Files
    print(f"\n🎵 FILE ACCESSIBILITY:")
    print(f"  Checked: {files_result['checked']} files")
    print(f"  Accessible: {files_result['accessible']} files")
    print(f"  Failed: {files_result['failed']} files")
    
    if files_result['failed'] > 0:
        overall_success = False
        print(f"\n  ❌ File access issues:")
        for error in files_result['errors'][:3]:  # Show first 3 errors
            print(f"    - {error}")
        if len(files_result['errors']) > 3:
            print(f"    ... and {len(files_result['errors']) - 3} more")
    
    # Metadata
    print(f"\n📋 METADATA COMPLETENESS:")
    print(f"  Checked: {metadata_result['checked']} samples")
    print(f"  Complete: {metadata_result['complete']} samples")
    print(f"  Incomplete: {metadata_result['incomplete']} samples")
    
    if metadata_result['incomplete'] > 0:
        print(f"\n  ⚠️  Metadata warnings:")
        for warning in metadata_result['warnings'][:3]:
            print(f"    - {warning}")
        if len(metadata_result['warnings']) > 3:
            print(f"    ... and {len(metadata_result['warnings']) - 3} more")
    
    # Search
    print(f"\n🔎 SEARCH FUNCTIONALITY: {'✅ OK' if search_ok else '⚠️  ISSUES'}")
    if not search_ok:
        overall_success = False
    
    print("\n" + "=" * 60)
    
    if overall_success:
        print("🎉 VERIFICATION PASSED - System is ready!")
        return True
    else:
        print("⚠️  VERIFICATION FAILED - Check issues above")
        return False

def main():
    print("🔧 Beat Sensei Upload Verification")
    print("=" * 60)
    
    # Get Supabase client
    client = get_supabase_client()
    
    # Run verifications
    db_ok = verify_database_connection(client)
    storage_ok = verify_storage_access(client)
    
    if not db_ok or not storage_ok:
        print("\n❌ Cannot proceed - fix database or storage issues first")
        sys.exit(1)
    
    files_result = verify_sample_files(client, limit=10)
    metadata_result = verify_metadata_consistency(client, limit=5)
    search_ok = verify_search_functionality(client)
    
    # Generate report
    all_ok = generate_report(db_ok, storage_ok, files_result, metadata_result, search_ok)
    
    if not all_ok:
        print("\n💡 Recommendations:")
        if files_result['failed'] > 0:
            print("  • Check storage bucket is set to 'Public'")
            print("  • Verify file URLs in database are correct")
        if metadata_result['incomplete'] > 0:
            print("  • Consider re-uploading with better metadata extraction")
        print("  • Run: python scripts/validate_samples.py <directory> to check source files")
        
        sys.exit(1)
    
    print("\n✅ System verified and ready for use!")
    print("\nNext steps:")
    print("1. Test chatbot: python -m beat_sensei.cli chat")
    print("2. Type 'kicks' or 'search [term]' in chatbot")
    print("3. Share your SUPABASE_URL with users")

if __name__ == '__main__':
    main()