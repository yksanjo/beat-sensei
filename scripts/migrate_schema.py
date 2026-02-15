#!/usr/bin/env python3
"""
Migration script for Supabase schema updates.
Safely applies schema changes without data loss.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client(use_service_key: bool = False):
    """Get Supabase client with appropriate key."""
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        
        if use_service_key:
            key = os.getenv('SUPABASE_SERVICE_KEY')
            key_type = "service role"
        else:
            key = os.getenv('SUPABASE_ANON_KEY')
            key_type = "anon"
        
        if not url or not key:
            print(f"❌ SUPABASE_URL or SUPABASE_{'SERVICE' if use_service_key else 'ANON'}_KEY not set")
            sys.exit(1)
        
        print(f"🔑 Using {key_type} key for migration")
        return create_client(url, key)
    except ImportError:
        print("❌ supabase package not installed. Run: pip install supabase")
        sys.exit(1)

def check_current_schema(client) -> Dict[str, Any]:
    """Check current database schema."""
    print("🔍 Checking current schema...")
    
    try:
        # Check for existing tables
        tables_to_check = ['samples', 'sample_tags', 'user_downloads', 'user_favorites', 'usage_limits']
        
        existing_tables = []
        missing_tables = []
        
        for table in tables_to_check:
            try:
                # Try to select from table
                response = client.table(table).select('count', count='exact').limit(1).execute()
                existing_tables.append(table)
                print(f"  ✅ {table}: exists ({response.count} rows)")
            except Exception:
                missing_tables.append(table)
                print(f"  ❌ {table}: missing")
        
        return {
            'existing_tables': existing_tables,
            'missing_tables': missing_tables,
            'is_simple_schema': 'samples' in existing_tables and len(existing_tables) == 1
        }
        
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return {'existing_tables': [], 'missing_tables': [], 'is_simple_schema': False}

def backup_data(client, tables: List[str]) -> bool:
    """Backup data before migration (conceptual - in production, use Supabase backups)."""
    print("\n💾 Data backup (conceptual)...")
    print("⚠️  In production, use Supabase Dashboard → Backups or pg_dump")
    print("   For this migration, we'll preserve existing data")
    return True

def apply_simple_schema(client) -> bool:
    """Apply the simple schema (initial setup)."""
    print("\n📝 Applying simple schema...")
    
    try:
        # Read simple schema SQL
        schema_path = Path(__file__).parent.parent / 'simple_schema.sql'
        if not schema_path.exists():
            print(f"❌ Schema file not found: {schema_path}")
            return False
        
        with open(schema_path, 'r') as f:
            sql = f.read()
        
        print(f"📄 Read schema from: {schema_path.name}")
        print("⚠️  Note: You need to run this SQL in Supabase SQL Editor")
        print("\nSteps:")
        print("1. Go to Supabase Dashboard → SQL Editor")
        print("2. Copy the SQL from simple_schema.sql")
        print("3. Click RUN")
        print("4. Create storage bucket in Storage section")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to read schema: {e}")
        return False

def apply_enhanced_schema(client) -> bool:
    """Apply enhanced schema with new tables."""
    print("\n🚀 Applying enhanced schema...")
    
    try:
        # Read enhanced schema SQL
        schema_path = Path(__file__).parent.parent / 'enhanced_schema.sql'
        if not schema_path.exists():
            print(f"❌ Schema file not found: {schema_path}")
            return False
        
        with open(schema_path, 'r') as f:
            sql = f.read()
        
        print(f"📄 Read schema from: {schema_path.name}")
        print("📊 This will add:")
        print("  • sample_tags table (normalized tags)")
        print("  • user_downloads table (track downloads)")
        print("  • user_favorites table (user favorites)")
        print("  • usage_limits table (tier management)")
        print("  • api_usage table (rate limiting)")
        print("  • Indexes and functions")
        
        print("\n⚠️  IMPORTANT: This migration:")
        print("  1. Preserves existing samples data")
        print("  2. Adds new tables alongside existing ones")
        print("  3. May take a few minutes")
        
        confirm = input("\nProceed with enhanced schema? (y/N): ")
        if confirm.lower() != 'y':
            print("Migration cancelled")
            return False
        
        print("⚠️  Note: You need to run this SQL in Supabase SQL Editor")
        print("\nSteps:")
        print("1. Go to Supabase Dashboard → SQL Editor")
        print("2. Copy the SQL from enhanced_schema.sql")
        print("3. Click RUN")
        print("4. Wait for completion")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to read schema: {e}")
        return False

def migrate_data_to_enhanced_schema(client) -> bool:
    """Migrate data from simple to enhanced schema."""
    print("\n🔄 Migrating data to enhanced schema...")
    
    try:
        # Check if we have samples data
        response = client.table('samples').select('id, tags').limit(1).execute()
        
        if not response.data:
            print("⚠️  No samples data to migrate")
            return True
        
        print("📊 Found samples data")
        print("💡 Data migration steps (if needed):")
        print("  1. Tags from samples.tags[] → sample_tags table")
        print("  2. Download counts → user_downloads table")
        print("  3. This happens automatically via application logic")
        
        return True
        
    except Exception as e:
        print(f"❌ Data migration check failed: {e}")
        return False

def verify_migration(client) -> bool:
    """Verify migration was successful."""
    print("\n✅ Verifying migration...")
    
    try:
        # Check all expected tables exist
        expected_tables = ['samples', 'sample_tags', 'user_downloads', 'user_favorites', 'usage_limits']
        
        all_tables_exist = True
        for table in expected_tables:
            try:
                client.table(table).select('count', count='exact').limit(1).execute()
                print(f"  ✅ {table}: exists")
            except Exception:
                print(f"  ⚠️  {table}: missing (may be expected for simple schema)")
                all_tables_exist = False
        
        # Check samples table has data
        samples_response = client.table('samples').select('id', count='exact').limit(1).execute()
        print(f"  📊 samples: {samples_response.count} rows")
        
        if samples_response.count == 0:
            print("  ⚠️  samples table is empty")
        
        return all_tables_exist
        
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False

def main():
    print("🚀 Beat Sensei Schema Migration")
    print("=" * 60)
    
    # Get client with service key (needed for schema changes)
    client = get_supabase_client(use_service_key=True)
    
    # Check current schema
    schema_info = check_current_schema(client)
    
    print(f"\n📊 Current state:")
    print(f"  Existing tables: {len(schema_info['existing_tables'])}")
    print(f"  Missing tables: {len(schema_info['missing_tables'])}")
    print(f"  Is simple schema: {schema_info['is_simple_schema']}")
    
    # Determine migration path
    if len(schema_info['existing_tables']) == 0:
        print("\n🎯 No schema detected - initial setup needed")
        print("\nOptions:")
        print("  1. Simple schema (basic samples table)")
        print("  2. Enhanced schema (full features)")
        
        choice = input("\nChoose schema (1 or 2): ")
        
        if choice == '1':
            success = apply_simple_schema(client)
        elif choice == '2':
            success = apply_enhanced_schema(client)
        else:
            print("❌ Invalid choice")
            sys.exit(1)
    
    elif schema_info['is_simple_schema']:
        print("\n🎯 Simple schema detected - upgrade to enhanced schema")
        
        confirm = input("\nUpgrade to enhanced schema? (y/N): ")
        if confirm.lower() != 'y':
            print("Migration cancelled")
            sys.exit(0)
        
        # Backup (conceptual)
        backup_data(client, ['samples'])
        
        # Apply enhanced schema
        success = apply_enhanced_schema(client)
        
        if success:
            # Migrate data
            migrate_data_to_enhanced_schema(client)
    
    else:
        print("\n🎯 Enhanced schema or custom schema detected")
        print("💡 Schema appears to be already set up")
        
        # Verify migration
        success = verify_migration(client)
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Migration instructions ready!")
        print("\nNext steps:")
        print("1. Run the SQL in Supabase SQL Editor")
        print("2. Verify with: python scripts/verify_upload.py")
        print("3. Test system functionality")
    else:
        print("\n❌ Migration preparation failed")
        sys.exit(1)

if __name__ == '__main__':
    main()