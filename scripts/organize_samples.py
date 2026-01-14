#!/usr/bin/env python3
"""Organize audio samples into categorized folders."""

import os
import shutil
from pathlib import Path
from typing import Dict, List

# Category keywords mapping
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    'drums': ['drum', 'kick', 'snare', 'hihat', 'hi-hat', 'hat', 'clap', 'perc', 'tom', 'cymbal', 'break', 'jerk'],
    'bass': ['bass', '808', 'sub', 'low-end'],
    'melody': ['melody', 'lead', 'synth', 'keys', 'piano', 'guitar', 'strings', 'pluck', 'chord'],
    'vocal': ['vocal', 'vox', 'voice', 'acapella', 'chant', 'choir', 'sing'],
    'fx': ['fx', 'effect', 'riser', 'sweep', 'impact', 'transition', 'foley'],
    'loops': ['loop', 'beat', 'groove', 'bpm'],
}

AUDIO_EXTENSIONS = {'.wav', '.mp3', '.aiff', '.aif', '.flac', '.m4a', '.ogg'}


def categorize_file(filename: str, filepath: str) -> str:
    """Determine the category for a file based on its name and path."""
    combined = (filename + " " + filepath).lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in combined:
                return category

    return 'samples'  # Default category


def organize_samples(source_dir: Path, dest_dir: Path, move: bool = False):
    """Organize samples from source directory into categorized folders."""
    source_dir = Path(source_dir)
    dest_dir = Path(dest_dir)

    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        return

    # Create category folders
    categories = list(CATEGORY_KEYWORDS.keys()) + ['samples', 'generated']
    for cat in categories:
        (dest_dir / cat).mkdir(parents=True, exist_ok=True)

    organized = 0
    skipped = 0

    # Find all audio files
    for item in source_dir.iterdir():
        if item.is_file() and item.suffix.lower() in AUDIO_EXTENSIONS:
            category = categorize_file(item.stem, str(item.parent))
            dest_path = dest_dir / category / item.name

            # Skip if already in destination
            if dest_path.exists():
                skipped += 1
                continue

            try:
                if move:
                    shutil.move(str(item), str(dest_path))
                else:
                    shutil.copy2(str(item), str(dest_path))
                organized += 1
                print(f"  [{category}] {item.name}")
            except Exception as e:
                print(f"  [ERROR] {item.name}: {e}")

    print(f"\nOrganized: {organized} files")
    print(f"Skipped: {skipped} files (already exist)")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Organize audio samples into categories")
    parser.add_argument("source", help="Source directory with audio files")
    parser.add_argument("--dest", "-d", help="Destination directory (default: source/organized)")
    parser.add_argument("--move", "-m", action="store_true", help="Move files instead of copying")

    args = parser.parse_args()

    source = Path(args.source).expanduser()
    dest = Path(args.dest).expanduser() if args.dest else source

    print(f"Organizing samples from: {source}")
    print(f"Destination: {dest}")
    print(f"Mode: {'Move' if args.move else 'Copy'}\n")

    organize_samples(source, dest, move=args.move)


if __name__ == "__main__":
    main()
