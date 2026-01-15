"""Local beat generator for Beat-Sensei - creates simple beats without external APIs."""

import os
import random
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import numpy as np

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    from scipy import signal
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


@dataclass
class GenerationResult:
    """Result of a track generation."""
    success: bool
    filepath: Optional[str] = None
    error: Optional[str] = None
    mood: Optional[str] = None
    genre: Optional[str] = None
    duration: float = 0.0


class LocalBeatGenerator:
    """Simple beat generator that creates basic drum patterns without external APIs."""
    
    # Simple drum samples (synthesized)
    SAMPLE_RATE = 44100
    
    # Beat patterns for different genres
    BEAT_PATTERNS = {
        'trap': {
            'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            'hat': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        },
        'hiphop': {
            'kick': [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
            'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            'hat': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        },
        'house': {
            'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            'clap': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            'hat': [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        },
        'lo-fi': {
            'kick': [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            'hat': [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        }
    }
    
    # Mood/Genre mapping
    MOOD_GENRE_MAP = {
        'dark': 'trap',
        'hard': 'trap',
        'aggressive': 'trap',
        'chill': 'lo-fi',
        'soft': 'lo-fi',
        'peaceful': 'lo-fi',
        'groovy': 'house',
        'funky': 'hiphop',
        'classic': 'hiphop',
        'boom bap': 'hiphop',
    }
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the local beat generator."""
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path.home() / "Music" / "BeatSensei" / "LocalBeats"
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if we can generate audio
        self.can_generate = SOUNDFILE_AVAILABLE and SCIPY_AVAILABLE
        
        if not self.can_generate:
            print("Note: Local beat generation requires 'soundfile' and 'scipy' packages.")
            print("Install with: pip install soundfile scipy")
    
    def is_available(self) -> bool:
        """Check if local generator is available."""
        return self.can_generate
    
    def generate(self, prompt: str, duration: float = 30.0) -> GenerationResult:
        """Generate a simple beat based on the prompt."""
        if not self.can_generate:
            return GenerationResult(
                success=False,
                error="Local beat generation requires 'soundfile' and 'scipy' packages. Install with: pip install soundfile scipy"
            )
        
        # Parse prompt for mood/genre
        prompt_lower = prompt.lower()
        detected_genre = self._detect_genre(prompt_lower)
        detected_mood = self._detect_mood(prompt_lower)
        
        # Create beat
        try:
            audio = self._create_beat(detected_genre, duration)
            
            # Save file
            filename = f"beat_{detected_genre}_{int(random.random() * 1000)}.wav"
            filepath = self.output_dir / filename
            
            sf.write(filepath, audio, self.SAMPLE_RATE)
            
            return GenerationResult(
                success=True,
                filepath=str(filepath),
                mood=detected_mood,
                genre=detected_genre,
                duration=duration
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                error=f"Failed to generate beat: {str(e)}"
            )
    
    def _detect_genre(self, prompt: str) -> str:
        """Detect genre from prompt."""
        # Check for specific genres
        for genre in ['trap', 'hiphop', 'house', 'techno', 'lo-fi', 'drill', 'dubstep']:
            if genre in prompt:
                return genre
        
        # Check for mood-based genre mapping
        for mood, genre in self.MOOD_GENRE_MAP.items():
            if mood in prompt:
                return genre
        
        # Default to trap
        return 'trap'
    
    def _detect_mood(self, prompt: str) -> str:
        """Detect mood from prompt."""
        moods = ['dark', 'hard', 'aggressive', 'chill', 'soft', 'peaceful', 'groovy', 'funky']
        for mood in moods:
            if mood in prompt:
                return mood
        
        return 'neutral'
    
    def _create_beat(self, genre: str, duration: float) -> np.ndarray:
        """Create a simple beat audio."""
        # Get or create pattern
        if genre in self.BEAT_PATTERNS:
            pattern = self.BEAT_PATTERNS[genre]
        else:
            pattern = self.BEAT_PATTERNS['trap']
        
        # Calculate timing
        bpm = 120  # Default BPM
        beats_per_second = bpm / 60
        beat_duration = 1 / beats_per_second
        samples_per_beat = int(self.SAMPLE_RATE * beat_duration)
        
        # Create empty track
        total_samples = int(self.SAMPLE_RATE * duration)
        track = np.zeros(total_samples)
        
        # Add kick drum
        if 'kick' in pattern:
            kick_sound = self._create_kick_sound()
            self._add_pattern(track, pattern['kick'], kick_sound, samples_per_beat)
        
        # Add snare/clap
        if 'snare' in pattern:
            snare_sound = self._create_snare_sound()
            self._add_pattern(track, pattern['snare'], snare_sound, samples_per_beat)
        elif 'clap' in pattern:
            clap_sound = self._create_clap_sound()
            self._add_pattern(track, pattern['clap'], clap_sound, samples_per_beat)
        
        # Add hi-hat
        if 'hat' in pattern:
            hat_sound = self._create_hat_sound()
            self._add_pattern(track, pattern['hat'], hat_sound, samples_per_beat)
        
        # Normalize
        if np.max(np.abs(track)) > 0:
            track = track / np.max(np.abs(track)) * 0.8
        
        return track
    
    def _create_kick_sound(self) -> np.ndarray:
        """Create a simple kick drum sound."""
        duration = 0.1  # seconds
        samples = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, endpoint=False)
        
        # Exponential decay
        freq = 80 * np.exp(-15 * t)
        kick = 0.5 * np.sin(2 * np.pi * freq * t)
        
        # Apply envelope
        envelope = np.exp(-20 * t)
        kick *= envelope
        
        return kick
    
    def _create_snare_sound(self) -> np.ndarray:
        """Create a simple snare drum sound."""
        duration = 0.1
        samples = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, endpoint=False)
        
        # White noise with pitch
        noise = np.random.normal(0, 0.5, samples)
        tone = 0.3 * np.sin(2 * np.pi * 200 * t * np.exp(-10 * t))
        
        snare = noise + tone
        
        # Apply envelope
        envelope = np.exp(-25 * t)
        snare *= envelope
        
        return snare
    
    def _create_clap_sound(self) -> np.ndarray:
        """Create a simple clap sound."""
        duration = 0.05
        samples = int(self.SAMPLE_RATE * duration)
        
        # Multiple noise bursts
        clap = np.zeros(samples)
        for offset in [0, 0.005, 0.01]:
            offset_samples = int(offset * self.SAMPLE_RATE)
            if offset_samples < samples:
                burst = np.random.normal(0, 0.3, samples - offset_samples)
                clap[offset_samples:] += burst
        
        # Apply envelope
        t = np.linspace(0, duration, samples, endpoint=False)
        envelope = np.exp(-40 * t)
        clap *= envelope
        
        return clap
    
    def _create_hat_sound(self) -> np.ndarray:
        """Create a simple hi-hat sound."""
        duration = 0.02
        samples = int(self.SAMPLE_RATE * duration)
        
        # High-frequency noise
        hat = np.random.normal(0, 0.2, samples)
        
        # Apply sharp envelope
        t = np.linspace(0, duration, samples, endpoint=False)
        envelope = np.exp(-100 * t)
        hat *= envelope
        
        return hat
    
    def _add_pattern(self, track: np.ndarray, pattern: List[int], sound: np.ndarray, 
                    samples_per_beat: int) -> None:
        """Add a drum pattern to the track."""
        sound_len = len(sound)
        
        for i, hit in enumerate(pattern):
            if hit:
                start_sample = i * samples_per_beat
                end_sample = start_sample + sound_len
                
                if end_sample <= len(track):
                    track[start_sample:end_sample] += sound
    
    @staticmethod
    def get_available_genres() -> List[str]:
        """Get list of available genres."""
        return list(LocalBeatGenerator.BEAT_PATTERNS.keys())
    
    @staticmethod
    def get_available_moods() -> List[str]:
        """Get list of available moods."""
        return list(LocalBeatGenerator.MOOD_GENRE_MAP.keys())


# Simple fallback if audio libraries aren't available
class SimpleBeatGenerator:
    """Even simpler generator that just creates text descriptions."""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
    
    def is_available(self) -> bool:
        """Always available - creates descriptions only."""
        return True
    
    def generate(self, prompt: str, duration: float = 30.0) -> GenerationResult:
        """Generate a beat description (no actual audio)."""
        prompt_lower = prompt.lower()
        
        # Simple genre detection
        genres = ['trap', 'hiphop', 'house', 'lo-fi', 'techno', 'drill']
        detected_genre = 'hiphop'
        for genre in genres:
            if genre in prompt_lower:
                detected_genre = genre
                break
        
        # Create a text file with beat description
        filename = f"beat_idea_{detected_genre}_{int(random.random() * 1000)}.txt"
        filepath = self.output_dir / filename
        
        beat_description = f"""Beat Idea: {prompt}

Genre: {detected_genre}
Duration: {duration}s

Drum Pattern:
- Kick: on 1, 3, 5, 7 (four-on-the-floor)
- Snare: on 2, 4, 6, 8
- Hi-hat: steady 8th notes

Suggested Samples:
- Kick: punchy 808
- Snare: crisp trap snare  
- Hi-hat: closed hat with slight swing

Next Steps:
1. Load this pattern in your DAW
2. Add bassline in key of C minor
3. Layer with atmospheric pads
4. Add vocal chops or samples

Pro Tip: Try varying the velocity of hi-hats for more human feel."""

        with open(filepath, 'w') as f:
            f.write(beat_description)
        
        return GenerationResult(
            success=True,
            filepath=str(filepath),
            mood='creative',
            genre=detected_genre,
            duration=duration
        )