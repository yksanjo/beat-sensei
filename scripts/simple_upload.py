#!/usr/bin/env python3
"""
Simple sample upload script for Beat Sensei.
Uploads audio files from Desktop/samples to Supabase.

Requirements:
    pip install supabase python-dotenv tqdm

Usage:
    export SUPABASE_URL=your_supabase_url
    export SUPABASE_SERVICE_KEY=your_service_key
    python simple_upload.py /Users/yoshikondo/Desktop/samples
"""

import os
import sys
import re
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from tqdm import tqdm

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("Error: supabase not installed. Install with: pip install supabase")
    SUPABASE_AVAILABLE = False
    sys.exit(1)

# Audio file extensions to process
AUDIO_EXTENSIONS = {'.wav', '.mp3', '.aiff', '.aif', '.flac', '.m4a', '.ogg'}

def calculate_file_hash(filepath: Path) -> str:
    """Calculate MD5 hash of file for duplicate detection."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def extract_metadata_from_filename(filename: str) -> Dict[str, Any]:
    """Extract metadata from filename patterns."""
    filename_lower = filename.lower()
    metadata = {
        'bpm': None,
        'key': None,
        'genre': None,
    }
    
    # Extract BPM
    bpm_patterns = [
        r'(\d{2,3})\s*bpm',
        r'bpm\s*(\d{2,3})',
        r'[-_](\d{2,3})[-_]',
    ]
    
    for pattern in bpm_patterns:
        match = re.search(pattern, filename_lower)
        if match:
            try:
                bpm = int(match.group(1))
                if 60 <= bpm <= 200:  # Reasonable BPM range
                    metadata['bpm'] = bpm
                    break
            except (ValueError, IndexError):
                pass
    
    # Extract key
    key_patterns = [
        r'\b([A-G][#b]?)\s*(m|min|minor|maj|major)?\b',
        r'\b([A-G][#b]?)(m|min|maj)?\b',
    ]
    
    for pattern in key_patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            note = match.group(1).upper()
            quality = match.group(2) if len(match.groups()) > 1 else None
            if quality and quality.lower() in ['m', 'min', 'minor']:
                metadata['key'] = f"{note}m"
            else:
                metadata['key'] = note
            break
    
    return metadata

def scan_directory(root_dir: Path) -> List[Dict[str, Any]]:
    """Scan directory for audio files and extract metadata."""
    samples = []
    
    # Get all audio files
    audio_files = []
    for ext in AUDIO_EXTENSIONS:
        audio_files.extend(list(root_dir.rglob(f'*{ext}')))
        audio_files.extend(list(root_dir.rglob(f'*{ext.upper()}')))
    
    print(f"Found {len(audio_files)} audio files")
    
    for filepath in tqdm(audio_files, desc="Scanning files"):
        if filepath.name.startswith('.'):
            continue
        
        # Skip files larger than 50MB
        file_size = filepath.stat().st_size
        if file_size > 50 * 1024 * 1024:  # 50MB
            print(f"  Skipping {filepath.name} (too large: {file_size / 1024 / 1024:.1f}MB)")
            continue
        
        filename = filepath.stem
        file_hash = calculate_file_hash(filepath)
        
        # Extract metadata from filename
        filename_metadata = extract_metadata_from_filename(filename)
        
        # Create sample record
        sample = {
            'filename': filepath.name,
            'filepath': str(filepath),
            'file_hash': file_hash,
            'file_size': file_size,
            'title': filename.replace('_', ' ').replace('-', ' ').title(),
            'bpm': filename_metadata.get('bpm'),
            'key': filename_metadata.get('key'),
        }
        
        samples.append(sample)
    
    return samples

def upload_to_supabase(samples: List[Dict[str, Any]], bucket_name: str = "beat-sensei-samples", 
                       dry_run: bool = False) -> Dict[str, Any]:
    """Upload samples to Supabase Storage and Database."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        print("Error: Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables")
        sys.exit(1)
    
    client = create_client(url, key)
    
    print(f"\nPreparing to upload {len(samples)} samples to bucket '{bucket_name}'...")
    
    results = {
        'uploaded': 0,
        'skipped': 0,
        'errors': 0,
        'duplicates': 0,
        'sample_ids': []
    }
    
    # Upload each sample
    for sample in tqdm(samples, desc="Uploading samples"):
        filepath = Path(sample['filepath'])
        
        if dry_run:
            print(f"[DRY RUN] Would upload: {sample['filename']}")
            continue
        
        try:
            # Check if sample already exists by hash
            existing = client.table('samples').select('id').eq('file_hash', sample['file_hash']).execute()
            if existing.data:
                results['duplicates'] += 1
                print(f"  Skipping duplicate: {sample['filename']}")
                continue
            
            # Upload file to storage
            storage_path = f"samples/{filepath.name}"
            
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            # Upload to storage
            client.storage.from_(bucket_name).upload(
                storage_path,
                file_data,
                file_options={"content-type": "audio/wav"}
            )
            
            # Get public URL
            file_url = client.storage.from_(bucket_name).get_public_url(storage_path)
            
            # Insert metadata into database
            db_record = {
                'filename': sample['filename'],
                'file_url': file_url,
                'title': sample['title'],
                'bpm': sample['bpm'],
                'key': sample['key'],
                'file_size': sample['file_size'],
                'file_hash': sample['file_hash'],
                'download_count': 0,
                'upload_date': datetime.now().isoformat(),
            }
            
            response = client.table('samples').insert(db_record).execute()
            
            if response.data:
                results['uploaded'] += 1
                results['sample_ids'].append(response.data[0]['id'])
            
        except Exception as e:
            results['errors'] += 1
            print(f"  Error uploading {sample['filename']}: {e}")
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_upload.py <directory> [--dry-run]")
        sys.exit(1)
    
    root_dir = Path(sys.argv[1])
    dry_run = '--dry-run' in sys.argv
    
    if not root_dir.exists():
        print(f"Error: Directory not found: {root_dir}")
        sys.exit(1)
    
    print(f"Scanning {root_dir}...")
    samples = scan_directory(root_dir)
    
    print(f"\nFound {len(samples)} samples")
    print("Sample preview:")
    for s in samples[:5]:
        print(f"  - {s['filename']} (BPM: {s['bpm']}, Key: {s['key']})")
    
    if dry_run:
        print("\n[DRY RUN MODE - no uploads will happen]")
    
    confirm = input("\nProceed with upload? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    results = upload_to_supabase(samples, dry_run=dry_run)
    
    print(f"\nUpload complete!")
    print(f"  Uploaded: {results['uploaded']}")
    print(f"  Duplicates skipped: {results['duplicates']}")
    print(f"  Errors: {results['errors']}")

if __name__ == '__main__':
    main()