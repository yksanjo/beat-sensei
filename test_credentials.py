#!/usr/bin/env python3
"""Test Supabase credentials."""

import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
anon_key = os.getenv('SUPABASE_ANON_KEY')
service_key = os.getenv('SUPABASE_SERVICE_KEY')

print("Checking environment variables...")
print(f"SUPABASE_URL: {'✓ Set' if url and url != 'https://your-project-id.supabase.co' else '✗ NOT SET or using placeholder'}")
print(f"SUPABASE_ANON_KEY: {'✓ Set' if anon_key and anon_key != 'your-anon-key-here' else '✗ NOT SET or using placeholder'}")
print(f"SUPABASE_SERVICE_KEY: {'✓ Set' if service_key and service_key != 'your-service-role-key-here' else '✗ NOT SET or using placeholder'}")

if url == 'https://your-project-id.supabase.co':
    print("\n❌ ERROR: You need to update .env file with your actual Supabase credentials!")
    print("\nSteps:")
    print("1. Go to Supabase Dashboard → Settings → API")
    print("2. Copy your Project URL")
    print("3. Copy your anon/public key")
    print("4. Copy your service_role key")
    print("5. Edit ./beat-sensei/.env with these values")
    exit(1)

print("\n✅ Environment variables look good!")
print("\nNext: Run the SQL schema in Supabase SQL Editor")