#!/usr/bin/env python3
"""
Validate audio samples before upload.
Checks file formats, extracts metadata, and suggests organization.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import mimetypes

# Supported audio formats
SUPPORTED_EXTENSIONS = {'.wav', '.mp3', '.aiff', '.aif', '.flac', '.m4a', '.ogg'}
MAX_FILE_SIZE_MB = 50

def check_file_format(filepath: Path) -> Tuple[bool, str]:
    """Check if file is a valid audio format."""
    ext = filepath.suffix.lower()
    
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported format: {ext}"
    
    # Check file size
    file_size_mb = filepath.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return False, f"File too large: {file_size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)"
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type and not mime_type.startswith('audio/'):
        return False, f"Not an audio file: {mime_type}"
    
    return True, "OK"

def extract_metadata_from_filename(filename: str) -> Dict[str, Any]:
    """Extract BPM, key, and tags from filename."""
    metadata = {
        'bpm': None,
        'key': None,
        'tags': [],
        'category': 'other'
    }
    
    filename_lower = filename.lower()
    
    # Extract BPM
    bpm_patterns = [
        r'(\d{2,3})\s*bpm',
        r'bpm\s*(\d{2,3})',
        r'[-_](\d{2,3})[-_]',
        r'\((\d{2,3})\s*[A-G]'  # Pattern like "(120 Am)"
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
        r'\((\d{2,3})\s*([A-G][#b]?m?)\)',  # Pattern like "(120 Am)"
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
    
    # Detect category from keywords
    category_keywords = {
        'kick': ['kick', 'kicks', 'kik', 'bd', 'bassdrum'],
        'snare': ['snare', 'snares', 'snr', 'sd', 'snaredrum'],
        'hat': ['hat', 'hats', 'hihat', 'hi-hat', 'hh', 'cymbal'],
        '808': ['808', '808s', 'sub', 'subbass', 'bass'],
        'clap': ['clap', 'claps', 'handclap'],
        'bass': ['bass', 'basses', 'bassline'],
        'perc': ['perc', 'percussion', 'shaker', 'tambourine', 'conga', 'bongo'],
        'fx': ['fx', 'sfx', 'effect', 'riser', 'impact', 'transition', 'sweep'],
        'vocal': ['vocal', 'vocals', 'vox', 'voice', 'chant', 'sing'],
        'loop': ['loop', 'loops', 'melody', 'chord', 'progression', 'phrase', 'riff'],
    }
    
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in filename_lower:
                metadata['category'] = category
                break
        if metadata['category'] != 'other':
            break
    
    # Extract tags from filename
    tag_keywords = {
        'dark': ['dark', 'evil', 'sinister', 'grim', 'horror', 'moody'],
        'trap': ['trap', 'drill', 'plugg', 'atlanta'],
        'house': ['house', 'deep house', 'tech house'],
        'techno': ['techno', 'berlin', 'detroit'],
        'dubstep': ['dubstep', 'brostep', 'wobble'],
        'ambient': ['ambient', 'atmospheric', 'pad', 'texture'],
        'acoustic': ['acoustic', 'organic', 'natural', 'live'],
        'electronic': ['electronic', 'synth', 'digital', 'analog'],
        'vintage': ['vintage', 'retro', 'old', 'classic', '70s', '80s', '90s'],
        'clean': ['clean', 'crisp', 'sharp', 'clear'],
        'distorted': ['distorted', 'crunch', 'dirty', 'gritty'],
    }
    
    for tag, keywords in tag_keywords.items():
        for keyword in keywords:
            if keyword in filename_lower:
                metadata['tags'].append(tag)
                break
    
    return metadata

def analyze_directory(directory: Path) -> Dict[str, Any]:
    """Analyze all audio files in directory."""
    results = {
        'total_files': 0,
        'valid_files': 0,
        'invalid_files': [],
        'by_category': {},
        'by_format': {},
        'suggestions': []
    }
    
    audio_files = []
    for ext in SUPPORTED_EXTENSIONS:
        audio_files.extend(list(directory.rglob(f'*{ext}')))
        audio_files.extend(list(directory.rglob(f'*{ext.upper()}')))
    
    results['total_files'] = len(audio_files)
    
    for filepath in audio_files:
        is_valid, message = check_file_format(filepath)
        
        if is_valid:
            results['valid_files'] += 1
            
            # Extract metadata
            metadata = extract_metadata_from_filename(filepath.stem)
            
            # Count by category
            category = metadata['category']
            results['by_category'][category] = results['by_category'].get(category, 0) + 1
            
            # Count by format
            ext = filepath.suffix.lower()
            results['by_format'][ext] = results['by_format'].get(ext, 0) + 1
            
        else:
            results['invalid_files'].append({
                'file': filepath.name,
                'reason': message
            })
    
    # Generate suggestions
    if results['by_category'].get('other', 0) > results['valid_files'] * 0.3:
        results['suggestions'].append(
            "Many files categorized as 'other'. Consider renaming files to include "
            "category keywords (kick, snare, bass, etc.)"
        )
    
    if not results['by_category'].get('loop', 0) and any('melody' in f.name.lower() for f in audio_files):
        results['suggestions'].append(
            "Files with 'melody' in name detected. Consider categorizing as 'loop'"
        )
    
    return results

def print_report(results: Dict[str, Any], directory: Path):
    """Print validation report."""
    print(f"\n📊 Sample Validation Report for: {directory}")
    print("=" * 60)
    
    print(f"\n📁 Total audio files: {results['total_files']}")
    print(f"✅ Valid files: {results['valid_files']}")
    print(f"❌ Invalid files: {len(results['invalid_files'])}")
    
    if results['invalid_files']:
        print("\n❌ Invalid files found:")
        for invalid in results['invalid_files'][:5]:  # Show first 5
            print(f"  - {invalid['file']}: {invalid['reason']}")
        if len(results['invalid_files']) > 5:
            print(f"  ... and {len(results['invalid_files']) - 5} more")
    
    print(f"\n📈 By Category:")
    for category, count in sorted(results['by_category'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / results['valid_files'] * 100) if results['valid_files'] > 0 else 0
        print(f"  {category:10} {count:3} files ({percentage:.1f}%)")
    
    print(f"\n🎵 By Format:")
    for fmt, count in sorted(results['by_format'].items()):
        percentage = (count / results['valid_files'] * 100) if results['valid_files'] > 0 else 0
        print(f"  {fmt:10} {count:3} files ({percentage:.1f}%)")
    
    if results['suggestions']:
        print(f"\n💡 Suggestions:")
        for suggestion in results['suggestions']:
            print(f"  • {suggestion}")
    
    print("\n" + "=" * 60)
    
    if results['valid_files'] == 0:
        print("❌ No valid audio files found!")
        return False
    
    if len(results['invalid_files']) > 0:
        print("⚠️  Some files may not upload correctly")
        return False
    
    print("✅ All files ready for upload!")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_samples.py <directory>")
        print("Example: python validate_samples.py ../Desktop/samples")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)
    
    print("🔍 Validating audio samples...")
    results = analyze_directory(directory)
    
    is_ready = print_report(results, directory)
    
    if is_ready:
        print("\n🎯 Ready for upload!")
        print(f"Run: python scripts/simple_upload.py {directory}")
    else:
        print("\n⚠️  Fix issues before uploading")
        sys.exit(1)

if __name__ == '__main__':
    main()