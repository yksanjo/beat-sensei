#!/usr/bin/env python3
"""
Organize audio samples into categorized folder structure.
Helps with better metadata extraction and user experience.
"""

import os
import sys
import shutil
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Category mapping based on filename patterns
CATEGORY_PATTERNS = {
    'kicks': [
        r'\b(kick|kicks|kik|bd|bass.?drum)\b',
        r'kick.*\.(wav|mp3|aiff)$',
    ],
    'snares': [
        r'\b(snare|snares|snr|sd|snare.?drum)\b',
        r'snare.*\.(wav|mp3|aiff)$',
    ],
    'hats': [
        r'\b(hat|hats|hi.?hat|hh|cymbal)\b',
        r'hat.*\.(wav|mp3|aiff)$',
    ],
    'claps': [
        r'\b(clap|claps|hand.?clap)\b',
        r'clap.*\.(wav|mp3|aiff)$',
    ],
    '808s': [
        r'\b(808|808s|sub|sub.?bass)\b',
        r'808.*\.(wav|mp3|aiff)$',
    ],
    'bass': [
        r'\b(bass|basses|bassline|sub)\b',
        r'bass.*\.(wav|mp3|aiff)$',
    ],
    'percussion': [
        r'\b(perc|percussion|shaker|tambourine|conga|bongo|tom|timbal)\b',
        r'perc.*\.(wav|mp3|aiff)$',
    ],
    'fx': [
        r'\b(fx|sfx|effect|riser|impact|transition|sweep|noise|reverse)\b',
        r'fx.*\.(wav|mp3|aiff)$',
        r'rise.*\.(wav|mp3|aiff)$',
        r'sweep.*\.(wav|mp3|aiff)$',
    ],
    'vocals': [
        r'\b(vocal|vocals|vox|voice|chant|sing|choir|spoken)\b',
        r'vocal.*\.(wav|mp3|aiff)$',
    ],
    'loops': [
        r'\b(loop|loops|melody|chord|progression|phrase|riff|arp|sequence)\b',
        r'loop.*\.(wav|mp3|aiff)$',
        r'melody.*\.(wav|mp3|aiff)$',
        r'chord.*\.(wav|mp3|aiff)$',
    ],
    'textures': [
        r'\b(pad|texture|atmos|ambient|drone|soundscape)\b',
        r'pad.*\.(wav|mp3|aiff)$',
        r'texture.*\.(wav|mp3|aiff)$',
    ],
}

# Mood/style patterns for subcategorization
MOOD_PATTERNS = {
    'dark': [r'\b(dark|evil|sinister|grim|horror|moody|brooding)\b'],
    'trap': [r'\b(trap|drill|plugg|atlanta|migos)\b'],
    'house': [r'\b(house|deep.?house|tech.?house|garage)\b'],
    'techno': [r'\b(techno|berlin|detroit|industrial)\b'],
    'ambient': [r'\b(ambient|atmospheric|ethereal|floaty)\b'],
    'acoustic': [r'\b(acoustic|organic|natural|live|real)\b'],
    'vintage': [r'\b(vintage|retro|old|classic|70s|80s|90s|analog)\b'],
    'clean': [r'\b(clean|crisp|sharp|clear|pristine)\b'],
    'distorted': [r'\b(distorted|crunch|dirty|gritty|fuzzy)\b'],
    'bright': [r'\b(bright|shiny|sparkly|glitter)\b'],
    'warm': [r'\b(warm|cozy|soft|mellow|smooth)\b'],
    'aggressive': [r'\b(aggressive|hard|heavy|intense|powerful)\b'],
}

def detect_category(filename: str) -> str:
    """Detect sample category from filename."""
    filename_lower = filename.lower()
    
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                return category
    
    return 'uncategorized'

def detect_moods(filename: str) -> List[str]:
    """Detect mood tags from filename."""
    filename_lower = filename.lower()
    moods = []
    
    for mood, patterns in MOOD_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                moods.append(mood)
                break  # Only add each mood once
    
    return moods

def extract_bpm_key(filename: str) -> Dict[str, Any]:
    """Extract BPM and key from filename."""
    metadata = {'bpm': None, 'key': None}
    
    # Extract BPM
    bpm_patterns = [
        r'(\d{2,3})\s*bpm',
        r'bpm\s*(\d{2,3})',
        r'[-_](\d{2,3})[-_]',
        r'\((\d{2,3})\s*[A-G#b]',  # Pattern like "(120 Am)"
    ]
    
    for pattern in bpm_patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
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
    
    return metadata

def clean_filename(filename: str) -> str:
    """Clean filename for better organization."""
    # Remove common unwanted characters
    cleaned = filename
    
    # Replace spaces with underscores
    cleaned = cleaned.replace(' ', '_')
    
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remove special characters (keep alphanumeric, underscore, dash, dot)
    cleaned = re.sub(r'[^\w\-\.]', '', cleaned)
    
    # Ensure it ends with extension
    if not cleaned.lower().endswith(('.wav', '.mp3', '.aiff', '.aif', '.flac')):
        # Keep original extension
        ext = ''.join(Path(filename).suffixes)
        cleaned = cleaned + ext.lower()
    
    return cleaned

def analyze_directory(directory: Path) -> Dict[str, Any]:
    """Analyze all audio files in directory."""
    audio_extensions = {'.wav', '.mp3', '.aiff', '.aif', '.flac', '.m4a', '.ogg'}
    
    results = {
        'total_files': 0,
        'by_category': {},
        'by_mood': {},
        'files': [],
        'suggestions': []
    }
    
    for filepath in directory.iterdir():
        if filepath.is_file() and filepath.suffix.lower() in audio_extensions:
            results['total_files'] += 1
            
            filename = filepath.stem
            category = detect_category(filename)
            moods = detect_moods(filename)
            metadata = extract_bpm_key(filename)
            cleaned_name = clean_filename(filepath.name)
            
            # Update category counts
            results['by_category'][category] = results['by_category'].get(category, 0) + 1
            
            # Update mood counts
            for mood in moods:
                results['by_mood'][mood] = results['by_mood'].get(mood, 0) + 1
            
            # Store file info
            file_info = {
                'original': filepath.name,
                'cleaned': cleaned_name,
                'category': category,
                'moods': moods,
                'bpm': metadata['bpm'],
                'key': metadata['key'],
                'path': filepath,
            }
            results['files'].append(file_info)
    
    # Generate suggestions
    uncategorized_count = results['by_category'].get('uncategorized', 0)
    if uncategorized_count > results['total_files'] * 0.2:
        results['suggestions'].append(
            f"Many files ({uncategorized_count}) are uncategorized. "
            "Consider renaming files to include category keywords."
        )
    
    return results

def organize_files(directory: Path, output_dir: Path, dry_run: bool = True) -> Dict[str, Any]:
    """Organize files into categorized folder structure."""
    print(f"\n📁 Organizing files from: {directory}")
    print(f"📁 Output directory: {output_dir}")
    
    if dry_run:
        print("🚧 DRY RUN MODE - no files will be moved")
    
    # Analyze directory
    analysis = analyze_directory(directory)
    
    # Create output directory
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    organized_count = 0
    skipped_count = 0
    
    for file_info in analysis['files']:
        original_path = file_info['path']
        category = file_info['category']
        
        # Create category directory
        category_dir = output_dir / category
        if not dry_run:
            category_dir.mkdir(exist_ok=True)
        
        # Create destination path
        dest_path = category_dir / file_info['cleaned']
        
        if dry_run:
            print(f"  📄 {original_path.name}")
            print(f"    → {category}/{file_info['cleaned']}")
            if file_info['bpm']:
                print(f"    BPM: {file_info['bpm']}")
            if file_info['key']:
                print(f"    Key: {file_info['key']}")
            if file_info['moods']:
                print(f"    Moods: {', '.join(file_info['moods'])}")
            print()
        else:
            # Check if destination already exists
            if dest_path.exists():
                print(f"  ⚠️  Skipping (exists): {dest_path}")
                skipped_count += 1
            else:
                # Copy file
                shutil.copy2(original_path, dest_path)
                print(f"  ✅ Copied: {category}/{file_info['cleaned']}")
                organized_count += 1
    
    return {
        'total': analysis['total_files'],
        'organized': organized_count,
        'skipped': skipped_count,
        'analysis': analysis,
        'output_dir': output_dir,
    }

def print_report(results: Dict[str, Any], dry_run: bool):
    """Print organization report."""
    analysis = results['analysis']
    
    print("\n" + "=" * 60)
    print("📊 ORGANIZATION REPORT")
    print("=" * 60)
    
    print(f"\n📁 Source files: {analysis['total_files']}")
    print(f"📁 Organized: {results['organized']}")
    print(f"📁 Skipped: {results['skipped']}")
    
    print(f"\n📈 By Category:")
    for category, count in sorted(analysis['by_category'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / analysis['total_files'] * 100) if analysis['total_files'] > 0 else 0
        print(f"  {category:15} {count:3} files ({percentage:.1f}%)")
    
    if analysis['by_mood']:
        print(f"\n🎭 By Mood:")
        for mood, count in sorted(analysis['by_mood'].items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / analysis['total_files'] * 100) if analysis['total_files'] > 0 else 0
            print(f"  {mood:15} {count:3} files ({percentage:.1f}%)")
    
    if analysis['suggestions']:
        print(f"\n💡 Suggestions:")
        for suggestion in analysis['suggestions']:
            print(f"  • {suggestion}")
    
    print("\n" + "=" * 60)
    
    if dry_run:
        print("🚧 This was a DRY RUN")
        print(f"\nTo actually organize files, run:")
        print(f"  python organize_samples.py {results['analysis']['files'][0]['path'].parent} --execute")
    else:
        print(f"✅ Files organized in: {results['output_dir']}")
        print(f"\nNext steps:")
        print(f"  1. Review organized files")
        print(f"  2. Upload: python scripts/simple_upload.py {results['output_dir']}")
        print(f"  3. Verify: python scripts/verify_upload.py")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize audio samples into categorized folders')
    parser.add_argument('directory', help='Directory containing audio samples')
    parser.add_argument('--output', '-o', default='./organized_samples',
                       help='Output directory (default: ./organized_samples)')
    parser.add_argument('--execute', '-x', action='store_true',
                       help='Actually organize files (default: dry run)')
    parser.add_argument('--clean-names', '-c', action='store_true',
                       help='Clean filenames during organization')
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    output_dir = Path(args.output)
    
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        sys.exit(1)
    
    print("🎵 Beat Sensei Sample Organizer")
    print("=" * 60)
    
    # Analyze first
    print("🔍 Analyzing samples...")
    analysis = analyze_directory(directory)
    
    print(f"\n📊 Found {analysis['total_files']} audio files")
    print(f"📈 Categories detected:")
    for category, count in sorted(analysis['by_category'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {category}: {count} files")
    
    if analysis['total_files'] == 0:
        print("❌ No audio files found")
        sys.exit(1)
    
    # Organize
    results = organize_files(directory, output_dir, dry_run=not args.execute)
    
    # Print report
    print_report(results, dry_run=not args.execute)

if __name__ == '__main__':
    main()