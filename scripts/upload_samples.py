#!/usr/bin/env python3
"""
Upload samples from local directory to Supabase.

Usage:
    export SUPABASE_URL=your_url
    export SUPABASE_SERVICE_KEY=your_service_key
    python scripts/upload_samples.py /Users/yoshikondo/Downloads/beat_sensei
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import mimetypes


# Sample categories based on folder/filename
# Priority: loop category first (for sample_loop folder)
CATEGORY_KEYWORDS = {
    'loop': ['loop', 'loops', 'sample_loop', 'sample loop', 'sample-loop', 'melody', 'chord', 'progression', 'phrase'],
    'kick': ['kick', 'kicks', 'kik'],
    'snare': ['snare', 'snares', 'snr', 'rim'],
    'hat': ['hat', 'hats', 'hihat', 'hi-hat', 'hh', 'open hat', 'closed hat'],
    '808': ['808', '808s', 'sub', 'subbass'],
    'clap': ['clap', 'claps'],
    'bass': ['bass', 'basses'],
    'perc': ['perc', 'percussion', 'shaker', 'tambourine', 'conga', 'bongo'],
    'fx': ['fx', 'sfx', 'effect', 'riser', 'impact', 'transition'],
    'vocal': ['vocal', 'vocals', 'vox', 'voice'],
}

# Mood/style tags based on filename
MOOD_KEYWORDS = {
    'dark': ['dark', 'evil', 'sinister', 'grim', 'horror', 'moody'],
    'hard': ['hard', 'aggressive', 'heavy', 'loud', 'distorted'],
    'soft': ['soft', 'gentle', 'mellow', 'smooth', 'warm', 'chill'],
    'sexy': ['sexy', 'sensual', 'sultry', 'seductive'],
    'trap': ['trap', 'drill', 'plugg'],
    'r&b': ['r&b', 'rnb', 'soul', 'neo-soul'],
    'lo-fi': ['lo-fi', 'lofi', 'vinyl', 'crackle'],
    'classic': ['classic', 'vintage', 'old', 'retro', 'boom', 'bap'],
    'crispy': ['crispy', 'crisp', 'clean', 'sharp'],
    'punchy': ['punchy', 'punch', 'knock', 'hit'],
    'acoustic': ['acoustic', 'organic', 'natural', 'live'],
    'electronic': ['electronic', 'synth', 'digital'],
}


def detect_category(filepath: Path, filename: str) -> str:
    """Detect sample category from path and filename."""
    # Check folder names first
    path_lower = str(filepath.parent).lower()
    name_lower = filename.lower()
    combined = f"{path_lower}/{name_lower}"

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in combined:
                return category

    return 'other'


def detect_tags(filepath: Path, filename: str) -> List[str]:
    """Extract tags from filename and path."""
    tags = []
    combined = f"{str(filepath.parent).lower()}/{filename.lower()}"

    # Check mood keywords
    for mood, keywords in MOOD_KEYWORDS.items():
        for keyword in keywords:
            if keyword in combined:
                tags.append(mood)
                break

    # Extract pack name as tag
    pack_name = filepath.parent.parent.name if filepath.parent.parent else filepath.parent.name
    if pack_name and pack_name != 'beat_sensei':
        tags.append(pack_name.lower().replace(' ', '-'))

    return list(set(tags))  # Remove duplicates


def detect_bpm(filename: str) -> Optional[int]:
    """Try to detect BPM from filename."""
    patterns = [
        r'(\d{2,3})\s*bpm',
        r'bpm\s*(\d{2,3})',
        r'[-_](\d{2,3})[-_]',
    ]

    for pattern in patterns:
        match = re.search(pattern, filename.lower())
        if match:
            bpm = int(match.group(1))
            if 60 <= bpm <= 200:  # Reasonable BPM range
                return bpm
    return None


def detect_key(filename: str) -> Optional[str]:
    """Try to detect musical key from filename."""
    # Pattern: C, C#, Db, Am, A minor, etc.
    pattern = r'\b([A-G][#b]?)\s*(m|min|minor|maj|major)?\b'
    match = re.search(pattern, filename, re.IGNORECASE)
    if match:
        note = match.group(1).upper()
        quality = match.group(2)
        if quality and quality.lower() in ['m', 'min', 'minor']:
            return f"{note}m"
        return note
    return None


def scan_samples(root_dir: Path) -> List[Dict[str, Any]]:
    """Scan directory for audio samples and extract metadata."""
    samples = []
    audio_extensions = {'.wav', '.mp3', '.aiff', '.aif', '.flac', '.m4a', '.ogg'}

    for filepath in root_dir.rglob('*'):
        if filepath.suffix.lower() not in audio_extensions:
            continue

        if filepath.name.startswith('.'):
            continue

        filename = filepath.stem
        category = detect_category(filepath, filename)
        tags = detect_tags(filepath, filename)

        # Get pack name from parent folder
        relative = filepath.relative_to(root_dir)
        pack_name = relative.parts[0] if relative.parts else 'Unknown'

        sample = {
            'name': filename,
            'category': category,
            'pack_name': pack_name,
            'file_path': str(filepath),
            'tags': tags,
            'bpm': detect_bpm(filename),
            'key': detect_key(filename),
            'file_size': filepath.stat().st_size,
        }

        samples.append(sample)

    return samples


def upload_to_supabase(samples: List[Dict[str, Any]], dry_run: bool = False):
    """Upload samples to Supabase Storage and Database."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')  # Need service key for uploads

    if not url or not key:
        print("Error: Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables")
        sys.exit(1)

    try:
        from supabase import create_client
    except ImportError:
        print("Error: Install supabase package: pip install supabase")
        sys.exit(1)

    client = create_client(url, key)

    print(f"\nUploading {len(samples)} samples...")

    success_count = 0
    error_count = 0

    for i, sample in enumerate(samples):
        filepath = Path(sample['file_path'])

        if dry_run:
            print(f"[DRY RUN] Would upload: {sample['name']} ({sample['category']})")
            continue

        try:
            # 1. Upload file to storage
            storage_path = f"{sample['pack_name']}/{sample['category']}/{filepath.name}"

            with open(filepath, 'rb') as f:
                file_data = f.read()

            # Upload to storage bucket "samples"
            storage_result = client.storage.from_('samples').upload(
                storage_path,
                file_data,
                file_options={"content-type": mimetypes.guess_type(filepath.name)[0] or "audio/wav"}
            )

            # Get public URL
            file_url = client.storage.from_('samples').get_public_url(storage_path)

            # 2. Insert metadata into database
            db_record = {
                'name': sample['name'],
                'category': sample['category'],
                'pack_name': sample['pack_name'],
                'file_url': file_url,
                'file_path': storage_path,
                'tags': sample['tags'],
                'bpm': sample['bpm'],
                'key': sample['key'],
                'file_size': sample['file_size'],
            }

            client.table('samples').insert(db_record).execute()

            success_count += 1
            if (i + 1) % 50 == 0:
                print(f"  Uploaded {i + 1}/{len(samples)}...")

        except Exception as e:
            error_count += 1
            print(f"  Error uploading {sample['name']}: {e}")

    print(f"\nDone! Uploaded: {success_count}, Errors: {error_count}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_samples.py <directory> [--dry-run]")
        sys.exit(1)

    root_dir = Path(sys.argv[1])
    dry_run = '--dry-run' in sys.argv

    if not root_dir.exists():
        print(f"Error: Directory not found: {root_dir}")
        sys.exit(1)

    print(f"Scanning {root_dir}...")
    samples = scan_samples(root_dir)

    print(f"\nFound {len(samples)} samples:")
    categories = {}
    for s in samples:
        cat = s['category']
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    print("\nSample previews:")
    for s in samples[:5]:
        print(f"  - {s['name']} [{s['category']}] tags={s['tags']}")

    if dry_run:
        print("\n[DRY RUN MODE - no uploads will happen]")

    confirm = input("\nProceed with upload? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

    upload_to_supabase(samples, dry_run=dry_run)


if __name__ == '__main__':
    main()
