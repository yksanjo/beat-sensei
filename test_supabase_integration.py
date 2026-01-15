#!/usr/bin/env python3
"""
Test script for Beat-Sensei Supabase integration.

This script tests the connection to Supabase and verifies that the
sample library integration is working correctly.

Usage:
    python test_supabase_integration.py
"""

import os
import sys
from pathlib import Path

# Add the beat_sensei module to the path
sys.path.insert(0, str(Path(__file__).parent))

from beat_sensei.database.supabase_client import SampleDatabase
from beat_sensei.utils.config import Config


def test_config_loading():
    """Test that configuration loads correctly."""
    print("🔧 Testing configuration loading...")
    
    config = Config.load()
    
    # Check required environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not getattr(config, var.lower(), None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\nTo set them up:")
        print("1. Create a Supabase project at https://supabase.com")
        print("2. Get your URL and anon key from Project Settings > API")
        print("3. Run:")
        print(f"   export SUPABASE_URL=your_project_url")
        print(f"   export SUPABASE_ANON_KEY=your_anon_key")
        print("\nOr add them to a .env file in the beat-sensei directory.")
        return False
    
    print(f"✅ Configuration loaded successfully")
    print(f"   Supabase URL: {config.supabase_url[:30]}...")
    print(f"   Supabase Key: {config.supabase_anon_key[:20]}...")
    return True


def test_supabase_connection():
    """Test connection to Supabase."""
    print("\n🔌 Testing Supabase connection...")
    
    config = Config.load()
    db = SampleDatabase(url=config.supabase_url, key=config.supabase_anon_key)
    
    if not db.is_available():
        print("❌ Could not connect to Supabase")
        print("   Check your URL and API key")
        return False
    
    print("✅ Connected to Supabase successfully")
    return True


def test_database_schema():
    """Test that the database schema exists."""
    print("\n🗄️  Testing database schema...")
    
    config = Config.load()
    db = SampleDatabase(url=config.supabase_url, key=config.supabase_anon_key)
    
    # Try to get categories to see if table exists
    categories = db.get_categories()
    
    if categories is None:
        print("❌ Could not access database table")
        print("   Make sure you've created the 'samples' table")
        return False
    
    print(f"✅ Database schema is accessible")
    print(f"   Found {len(categories)} categories")
    
    if categories:
        for category, count in sorted(categories.items()):
            print(f"   - {category}: {count} samples")
    
    return True


def test_sample_search():
    """Test sample search functionality."""
    print("\n🔍 Testing sample search...")
    
    config = Config.load()
    db = SampleDatabase(url=config.supabase_url, key=config.supabase_anon_key)
    
    # Test search
    samples = db.search("kick", limit=3)
    
    if not samples:
        print("⚠️  No samples found in search")
        print("   This is OK if your library is empty")
        print("   Run 'python scripts/upload_samples.py /path/to/samples' to add samples")
        return True  # Not a failure, just empty library
    
    print(f"✅ Search works - found {len(samples)} samples")
    for i, sample in enumerate(samples, 1):
        print(f"   {i}. {sample.name} ({sample.category})")
    
    return True


def test_category_filtering():
    """Test category filtering."""
    print("\n🏷️  Testing category filtering...")
    
    config = Config.load()
    db = SampleDatabase(url=config.supabase_url, key=config.supabase_anon_key)
    
    # Test getting by category
    kicks = db.get_by_category("kick", limit=2)
    
    if not kicks:
        print("⚠️  No kicks found")
        print("   This is OK if your library is empty")
        return True
    
    print(f"✅ Category filtering works - found {len(kicks)} kicks")
    for i, kick in enumerate(kicks, 1):
        print(f"   {i}. {kick.name}")
    
    return True


def test_recommendation_engine():
    """Test the recommendation engine."""
    print("\n🤖 Testing recommendation engine...")
    
    config = Config.load()
    db = SampleDatabase(url=config.supabase_url, key=config.supabase_anon_key)
    
    # Test recommendations for different prompts
    test_prompts = [
        "dark trap drums",
        "chill lo-fi",
        "hard techno",
        "boom bap hip hop",
    ]
    
    for prompt in test_prompts:
        recommendations = db.recommend_for_prompt(prompt, limit=3)
        
        if recommendations:
            print(f"✅ '{prompt}': Found {len(recommendations)} recommendations")
            # Show categories of recommendations
            categories = set(s.category for s in recommendations)
            print(f"   Categories: {', '.join(categories)}")
        else:
            print(f"⚠️  '{prompt}': No recommendations (library might be empty)")
    
    return True


def test_cli_commands():
    """Test that CLI commands work."""
    print("\n💻 Testing CLI commands...")
    
    # Test importing CLI module
    try:
        from beat_sensei.cli import app
        print("✅ CLI module imports successfully")
    except ImportError as e:
        print(f"❌ Failed to import CLI module: {e}")
        return False
    
    # Test that we can create a sensei instance
    try:
        from beat_sensei.chatbot.sensei import BeatSensei
        from beat_sensei.auth.tiers import TierManager
        
        tier_manager = TierManager()
        sensei = BeatSensei(
            tier_manager=tier_manager,
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY"),
        )
        print("✅ BeatSensei instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create BeatSensei: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("🧪 Beat-Sensei Supabase Integration Test")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_config_loading),
        ("Supabase Connection", test_supabase_connection),
        ("Database Schema", test_database_schema),
        ("Sample Search", test_sample_search),
        ("Category Filtering", test_category_filtering),
        ("Recommendation Engine", test_recommendation_engine),
        ("CLI Commands", test_cli_commands),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✨ All tests passed! Supabase integration is working correctly.")
        print("\nNext steps:")
        print("1. Add samples: python scripts/upload_samples.py /path/to/samples")
        print("2. Check library: beat-sensei library")
        print("3. Search samples: beat-sensei samples 'kick'")
        print("4. Start chat: beat-sensei")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("\nCommon issues:")
        print("1. Missing environment variables")
        print("2. Incorrect Supabase URL or API key")
        print("3. Database table not created")
        print("4. Storage bucket not set to public")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)