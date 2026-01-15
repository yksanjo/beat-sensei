"""Soundraw API client for AI music generation."""

import os
import urllib.request
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GenerationResult:
    """Result of an AI generation."""
    success: bool
    filepath: Optional[str] = None
    error: Optional[str] = None
    prompt: Optional[str] = None
    duration: Optional[float] = None
    mood: Optional[str] = None
    genre: Optional[str] = None


# Available Soundraw parameters
MOODS = [
    "Angry", "Busy & Frantic", "Dark", "Dreamy", "Elegant", "Happy",
    "Hopeful", "Humorous", "Light", "Love", "Mysterious", "Neutral",
    "Peaceful", "Playful", "Powerful", "Sad", "Scary", "Serious",
    "Sexy", "Sporty", "Suspenseful", "Unearthly", "Upbeat", "Warm"
]

GENRES = [
    "Acoustic", "Ambient", "Blues", "Classical", "Corporate", "Country",
    "Drum and Bass", "Electronic", "Folk", "Funk", "Hip Hop", "House",
    "Indie", "Jazz", "Latin", "Lo-fi", "Metal", "Pop", "R&B",
    "Reggae", "Rock", "Soul"
]

THEMES = [
    "Action", "Advertising", "Cinematic", "Comedy", "Corporate",
    "Documentary", "Drama", "Fashion", "Film Score", "Gaming",
    "Horror", "Inspirational", "Kids", "Meditation", "Nature",
    "News", "Podcast", "Romance", "Sci-Fi", "Sports", "Technology",
    "Travel", "Vlog", "Wedding & Romance"
]

ENERGY_LEVELS = ["Very Low", "Low", "Medium", "High", "Very High"]


class SoundrawGenerator:
    """Generate music using Soundraw API."""

    API_URL = "https://soundraw.io/api/v2/musics/compose"

    def __init__(self, api_token: Optional[str] = None, output_dir: Optional[Path] = None):
        self.api_token = api_token or os.getenv("SOUNDRAW_API_TOKEN")
        self.output_dir = output_dir or Path.home() / "Music" / "BeatSensei" / "Generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Track generations for rate limiting (free tier)
        self._generation_count = 0
        self._max_free_generations = 5  # Daily limit for free users

    def is_available(self) -> bool:
        """Check if the generator is configured and available."""
        return bool(self.api_token)

    def get_remaining_free_generations(self) -> int:
        """Get remaining free generations for today."""
        return max(0, self._max_free_generations - self._generation_count)

    def _parse_prompt_to_params(self, prompt: str) -> dict:
        """Parse a natural language prompt into Soundraw API parameters."""
        prompt_lower = prompt.lower()

        # Default parameters
        params = {
            "mood": "Neutral",
            "genres": "Hip Hop",
            "themes": "Vlog",
            "energy_levels": "Medium",
            "length": 30  # 30 seconds for free tier
        }

        # Detect mood from prompt
        mood_keywords = {
            "dark": "Dark", "sad": "Sad", "melancholy": "Sad",
            "happy": "Happy", "upbeat": "Upbeat", "energetic": "Upbeat",
            "chill": "Peaceful", "relaxed": "Peaceful", "calm": "Peaceful",
            "aggressive": "Angry", "hard": "Angry", "intense": "Powerful",
            "dreamy": "Dreamy", "ethereal": "Dreamy", "spacey": "Dreamy",
            "mysterious": "Mysterious", "eerie": "Mysterious",
            "hopeful": "Hopeful", "inspiring": "Hopeful", "uplifting": "Hopeful",
            "scary": "Scary", "horror": "Scary", "creepy": "Scary",
            "love": "Love", "romantic": "Love", "sexy": "Sexy", "sensual": "Sexy", "sultry": "Sexy",
            "playful": "Playful", "fun": "Playful", "bouncy": "Playful",
            "serious": "Serious", "epic": "Powerful", "cinematic": "Powerful",
            "moody": "Dark", "atmospheric": "Mysterious"
        }

        for keyword, mood in mood_keywords.items():
            if keyword in prompt_lower:
                params["mood"] = mood
                break

        # Detect genre from prompt
        genre_keywords = {
            "trap": "Hip Hop", "hip hop": "Hip Hop", "rap": "Hip Hop", "boom bap": "Hip Hop",
            "drill": "Hip Hop",  # Drill is a subgenre of hip hop
            "lo-fi": "Lo-fi", "lofi": "Lo-fi", "study": "Lo-fi",
            "electronic": "Electronic", "edm": "Electronic", "synth": "Electronic",
            "jazz": "Jazz", "smooth": "Jazz",
            "rock": "Rock", "guitar": "Rock",
            "r&b": "R&B", "rnb": "R&B", "soul": "Soul",
            "funk": "Funk", "funky": "Funk", "groovy": "Funk",
            "ambient": "Ambient", "atmospheric": "Ambient",
            "classical": "Classical", "orchestra": "Classical",
            "pop": "Pop", "mainstream": "Pop",
            "house": "House", "techno": "House", "dance": "House",
            "drum and bass": "Drum and Bass", "dnb": "Drum and Bass",
            "reggae": "Reggae", "dub": "Reggae",
            "metal": "Metal", "heavy": "Metal"
        }

        for keyword, genre in genre_keywords.items():
            if keyword in prompt_lower:
                params["genres"] = genre
                break

        # Detect energy level
        energy_keywords = {
            "chill": "Low", "relaxed": "Low", "mellow": "Low", "calm": "Very Low",
            "mid": "Medium", "moderate": "Medium",
            "high energy": "High", "energetic": "High", "hype": "High",
            "intense": "Very High", "aggressive": "Very High", "hard": "Very High"
        }

        for keyword, energy in energy_keywords.items():
            if keyword in prompt_lower:
                params["energy_levels"] = energy
                break

        # Detect theme
        theme_keywords = {
            "cinematic": "Cinematic", "movie": "Film Score", "film": "Film Score",
            "game": "Gaming", "gaming": "Gaming",
            "podcast": "Podcast", "talk": "Podcast",
            "vlog": "Vlog", "youtube": "Vlog",
            "meditation": "Meditation", "yoga": "Meditation",
            "workout": "Sports", "gym": "Sports", "exercise": "Sports",
            "horror": "Horror", "scary": "Horror",
            "comedy": "Comedy", "funny": "Comedy",
            "corporate": "Corporate", "business": "Corporate",
            "wedding": "Wedding & Romance", "romantic": "Romance"
        }

        for keyword, theme in theme_keywords.items():
            if keyword in prompt_lower:
                params["themes"] = theme
                break

        return params

    def generate(
        self,
        prompt: str,
        duration: float = 30.0,
        mood: Optional[str] = None,
        genre: Optional[str] = None,
        energy: Optional[str] = None,
        theme: Optional[str] = None
    ) -> GenerationResult:
        """Generate music from a text description or explicit parameters."""
        if not self.is_available():
            return GenerationResult(
                success=False,
                error="Soundraw API token not configured. Set SOUNDRAW_API_TOKEN environment variable.",
                prompt=prompt
            )

        try:
            import requests
        except ImportError:
            return GenerationResult(
                success=False,
                error="requests package not installed. Run: pip install requests",
                prompt=prompt
            )

        # Parse prompt or use explicit parameters
        params = self._parse_prompt_to_params(prompt)

        # Override with explicit parameters if provided
        if mood and mood in MOODS:
            params["mood"] = mood
        if genre and genre in GENRES:
            params["genres"] = genre
        if energy and energy in ENERGY_LEVELS:
            params["energy_levels"] = energy
        if theme and theme in THEMES:
            params["themes"] = theme

        params["length"] = int(duration)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                self.API_URL,
                headers=headers,
                json=params,
                timeout=60
            )

            if response.status_code != 200:
                return GenerationResult(
                    success=False,
                    error=f"API error: {response.status_code} - {response.text}",
                    prompt=prompt
                )

            data = response.json()

            if "error" in data:
                return GenerationResult(
                    success=False,
                    error=data["error"],
                    prompt=prompt
                )

            # Download the generated audio
            m4a_url = data.get("m4a_url")
            if not m4a_url:
                return GenerationResult(
                    success=False,
                    error="No audio URL in response",
                    prompt=prompt
                )

            filepath = self._save_output(m4a_url, prompt, params)
            self._generation_count += 1

            return GenerationResult(
                success=True,
                filepath=str(filepath),
                prompt=prompt,
                duration=duration,
                mood=params["mood"],
                genre=params["genres"]
            )

        except requests.exceptions.Timeout:
            return GenerationResult(
                success=False,
                error="Request timed out. Try again.",
                prompt=prompt
            )
        except requests.exceptions.RequestException as e:
            return GenerationResult(
                success=False,
                error=f"Network error: {str(e)}",
                prompt=prompt
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e),
                prompt=prompt
            )

    def _save_output(self, audio_url: str, prompt: str, params: dict) -> Path:
        """Download and save the generated audio."""
        # Create descriptive filename
        safe_prompt = "".join(c if c.isalnum() or c in ' -_' else '' for c in prompt)
        safe_prompt = safe_prompt[:30].strip().replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mood = params.get("mood", "").replace(" ", "_")
        genre = params.get("genres", "").replace(" ", "_")

        filename = f"{safe_prompt}_{mood}_{genre}_{timestamp}.m4a"
        filepath = self.output_dir / filename

        urllib.request.urlretrieve(audio_url, filepath)

        return filepath

    def build_prompt(
        self,
        description: str,
        bpm: Optional[int] = None,
        key: Optional[str] = None,
        style: Optional[str] = None,
        instrument: Optional[str] = None,
    ) -> str:
        """Build an optimized prompt for generation."""
        parts = [description]

        if style:
            parts.append(f"{style} style")
        if instrument:
            parts.append(f"featuring {instrument}")
        if bpm:
            parts.append(f"{bpm} BPM")
        if key:
            parts.append(f"in {key}")

        return ", ".join(parts)

    @staticmethod
    def get_available_moods() -> List[str]:
        """Get list of available moods."""
        return MOODS.copy()

    @staticmethod
    def get_available_genres() -> List[str]:
        """Get list of available genres."""
        return GENRES.copy()

    @staticmethod
    def get_available_themes() -> List[str]:
        """Get list of available themes."""
        return THEMES.copy()

    @staticmethod
    def get_available_energy_levels() -> List[str]:
        """Get list of available energy levels."""
        return ENERGY_LEVELS.copy()


class MockSoundrawGenerator:
    """Mock generator for testing without API."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path.home() / "Music" / "BeatSensei" / "Generated"
        self._generation_count = 0

    def is_available(self) -> bool:
        return True

    def get_remaining_free_generations(self) -> int:
        return 5 - self._generation_count

    def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Simulate generation (for testing UI)."""
        import time
        time.sleep(2)  # Simulate API delay

        self._generation_count += 1

        return GenerationResult(
            success=True,
            filepath=str(self.output_dir / "mock_sample.m4a"),
            prompt=prompt,
            duration=30.0,
            mood="Dark",
            genre="Hip Hop"
        )
