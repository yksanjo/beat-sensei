"""Sample folder scanner and indexer for Beat-Sensei."""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class SampleMetadata:
    """Metadata for an audio sample."""
    filepath: str
    filename: str
    folder: str
    extension: str
    size_bytes: int
    duration: Optional[float] = None
    bpm: Optional[float] = None
    key: Optional[str] = None
    tags: List[str] = None
    category: Optional[str] = None
    indexed_at: str = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.indexed_at is None:
            self.indexed_at = datetime.now().isoformat()


class SampleScanner:
    """Scans folders for audio samples and builds an index."""

    AUDIO_EXTENSIONS = {'.wav', '.mp3', '.aiff', '.aif', '.flac', '.m4a', '.ogg'}

    def __init__(self, index_path: Path = None):
        self.index_path = index_path or Path.home() / ".beat-sensei" / "sample_index.json"
        self.samples: Dict[str, SampleMetadata] = {}
        self._load_index()

    def _load_index(self):
        """Load existing index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r') as f:
                    data = json.load(f)
                    for filepath, meta in data.items():
                        self.samples[filepath] = SampleMetadata(**meta)
            except (json.JSONDecodeError, KeyError):
                self.samples = {}

    def _save_index(self):
        """Save index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, 'w') as f:
            data = {fp: asdict(meta) for fp, meta in self.samples.items()}
            json.dump(data, f, indent=2)

    def scan_folder(self, folder: Path, analyze_audio: bool = False) -> List[SampleMetadata]:
        """Scan a folder recursively for audio files."""
        folder = Path(folder)
        if not folder.exists():
            return []

        new_samples = []
        for root, dirs, files in os.walk(folder):
            for filename in files:
                ext = Path(filename).suffix.lower()
                if ext in self.AUDIO_EXTENSIONS:
                    filepath = Path(root) / filename
                    if str(filepath) not in self.samples:
                        meta = self._create_metadata(filepath, analyze_audio)
                        self.samples[str(filepath)] = meta
                        new_samples.append(meta)

        self._save_index()
        return new_samples

    def _create_metadata(self, filepath: Path, analyze: bool = False) -> SampleMetadata:
        """Create metadata for a single audio file."""
        stat = filepath.stat()

        # Extract info from filename
        tags = self._extract_tags_from_filename(filepath.stem)
        bpm = self._extract_bpm_from_filename(filepath.stem)
        key = self._extract_key_from_filename(filepath.stem)
        category = self._guess_category(filepath.stem, str(filepath.parent))

        meta = SampleMetadata(
            filepath=str(filepath),
            filename=filepath.name,
            folder=str(filepath.parent),
            extension=filepath.suffix.lower(),
            size_bytes=stat.st_size,
            bpm=bpm,
            key=key,
            tags=tags,
            category=category,
        )

        if analyze:
            meta = self._analyze_audio(meta)

        return meta

    def _extract_tags_from_filename(self, filename: str) -> List[str]:
        """Extract descriptive tags from filename."""
        tags = []
        filename_lower = filename.lower()

        # Common descriptors
        descriptors = [
            'dark', 'bright', 'warm', 'cold', 'dusty', 'clean', 'dirty', 'vintage',
            'modern', 'lofi', 'hifi', 'punchy', 'soft', 'hard', 'heavy', 'light',
            'deep', 'high', 'low', 'mid', 'atmospheric', 'ambient', 'energetic',
            'chill', 'aggressive', 'smooth', 'rough', 'crispy', 'muddy', 'wet', 'dry',
            'soul', 'jazz', 'funk', 'rock', 'trap', 'boom', 'bap', 'drill', 'house',
            'techno', 'edm', 'pop', 'rnb', 'hip', 'hop', 'classical', 'orchestral'
        ]

        for desc in descriptors:
            if desc in filename_lower:
                tags.append(desc)

        return tags

    def _extract_bpm_from_filename(self, filename: str) -> Optional[float]:
        """Extract BPM from filename if present."""
        import re
        # Match patterns like "120bpm", "120-bpm", "120 bpm", "BPM120"
        patterns = [
            r'(\d{2,3})\s*bpm',
            r'bpm\s*(\d{2,3})',
            r'-(\d{2,3})-',
        ]
        filename_lower = filename.lower()
        for pattern in patterns:
            match = re.search(pattern, filename_lower)
            if match:
                bpm = float(match.group(1))
                if 40 <= bpm <= 300:
                    return bpm
        return None

    def _extract_key_from_filename(self, filename: str) -> Optional[str]:
        """Extract musical key from filename if present."""
        import re
        # Match patterns like "Am", "A minor", "C#maj", "Db major"
        key_pattern = r'([A-Ga-g][#b]?)\s*(minor|major|min|maj|m(?!i)|M)?'
        match = re.search(key_pattern, filename)
        if match:
            note = match.group(1).upper()
            quality = match.group(2)
            if quality:
                quality = quality.lower()
                if quality in ['minor', 'min', 'm']:
                    return f"{note} minor"
                elif quality in ['major', 'maj', 'M']:
                    return f"{note} major"
            return note
        return None

    def _guess_category(self, filename: str, folder: str) -> Optional[str]:
        """Guess the category/type of the sample."""
        combined = (filename + " " + folder).lower()

        categories = {
            'drums': ['drum', 'kick', 'snare', 'hihat', 'hi-hat', 'hat', 'clap', 'perc', 'tom', 'cymbal', 'break'],
            'bass': ['bass', '808', 'sub', 'low'],
            'melody': ['melody', 'lead', 'synth', 'keys', 'piano', 'guitar', 'strings', 'pluck'],
            'vocal': ['vocal', 'vox', 'voice', 'acapella', 'chant', 'choir'],
            'fx': ['fx', 'effect', 'riser', 'sweep', 'impact', 'transition', 'foley'],
            'loop': ['loop', 'beat', 'groove'],
            'oneshot': ['oneshot', 'one-shot', 'hit', 'stab'],
            'sample': ['sample', 'chop', 'flip'],
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in combined:
                    return category

        return 'sample'

    def _analyze_audio(self, meta: SampleMetadata) -> SampleMetadata:
        """Analyze audio file for BPM, key, duration (requires librosa)."""
        try:
            import librosa
            y, sr = librosa.load(meta.filepath, sr=None, duration=30)

            # Duration
            meta.duration = librosa.get_duration(y=y, sr=sr)

            # BPM detection if not already set
            if meta.bpm is None:
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                meta.bpm = float(tempo)

        except ImportError:
            pass
        except Exception:
            pass

        return meta

    def get_all_samples(self) -> List[SampleMetadata]:
        """Get all indexed samples."""
        return list(self.samples.values())

    def get_sample_count(self) -> int:
        """Get total number of indexed samples."""
        return len(self.samples)

    def clear_index(self):
        """Clear the sample index."""
        self.samples = {}
        if self.index_path.exists():
            self.index_path.unlink()
