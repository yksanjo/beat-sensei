"""Replicate API client for AI sample generation."""

import os
from pathlib import Path
from typing import Optional
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


class ReplicateGenerator:
    """Generate audio samples using Replicate's MusicGen API."""

    MODEL_ID = "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb"

    def __init__(self, api_token: Optional[str] = None, output_dir: Optional[Path] = None):
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        self.output_dir = output_dir or Path.home() / "Music" / "BeatSensei" / "Generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        """Check if the generator is configured and available."""
        return bool(self.api_token)

    def generate(
        self,
        prompt: str,
        duration: float = 8.0,
        model_version: str = "stereo-large",
        temperature: float = 1.0,
        top_k: int = 250,
        top_p: float = 0.0,
        classifier_free_guidance: int = 3,
    ) -> GenerationResult:
        """Generate an audio sample from a text description."""
        if not self.is_available():
            return GenerationResult(
                success=False,
                error="Replicate API token not configured. Set REPLICATE_API_TOKEN or upgrade to Pro.",
                prompt=prompt
            )

        try:
            import replicate
            
            # Format the prompt for better music generation
            formatted_prompt = self._format_prompt(prompt, duration)

            output = replicate.run(
                self.MODEL_ID,
                input={
                    "prompt": formatted_prompt,
                    "model_version": model_version,
                    "duration": int(duration),
                    "temperature": temperature,
                    "top_k": top_k,
                    "top_p": top_p,
                    "classifier_free_guidance": classifier_free_guidance,
                    "output_format": "wav",
                    "normalization_strategy": "peak",
                }
            )

            # Download the generated audio
            if output:
                filepath = self._save_output(output, prompt)
                return GenerationResult(
                    success=True,
                    filepath=str(filepath),
                    prompt=prompt,
                    duration=duration
                )
            else:
                return GenerationResult(
                    success=False,
                    error="No output received from API",
                    prompt=prompt
                )

        except ImportError:
            return GenerationResult(
                success=False,
                error="replicate package not installed. Run: pip install replicate",
                prompt=prompt
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e),
                prompt=prompt
            )

    def _format_prompt(self, user_prompt: str, duration: float) -> str:
        """Format user prompt for optimal music generation."""
        user_prompt_lower = user_prompt.lower()
        
        # Check for specific genres to apply specialized prompts
        if any(word in user_prompt_lower for word in ['drill', 'r&b', 'rnb', 'sexy', 'smooth']):
            # Use the specialized R&B Drill prompt
            bpm = 145  # Middle of 140-150 BPM range
            
            # Calculate bars based on duration and BPM
            # 4 beats per bar, 60 seconds per minute
            seconds_per_bar = 240 / bpm  # 4 beats * 60 seconds / bpm
            bars = int(duration / seconds_per_bar)
            
            return f"""Create a {bars}-bar R&B drill sample loop with the following characteristics:

MUSICAL ELEMENTS:
- Genre: Sexy Drill (R&B-influenced drill)
- Tempo: {bpm} BPM (standard drill tempo)
- Chord Progression: Use smooth R&B progressions (examples: vi-IV-I-V or ii-V-I-vi in minor keys)
- Drum Pattern: Hard-hitting drill drums with syncopated hi-hats, snappy snares on 2 and 4, and rolling 808 patterns
- Bass: Heavy, distorted 808 bass with melodic slides and sustained notes
- Atmosphere: Sensual, dark, and moody with sultry undertones

LOOP REQUIREMENTS:
- Exact duration: {bars} bars (calculate based on BPM for seamless looping)
- Perfect loop points: Ensure the ending note/rhythm transitions smoothly back to the beginning
- No fade-ins or fade-outs
- Maintain consistent energy throughout to enable seamless repetition

PRODUCTION STYLE:
- Mix: Bass-heavy with clear melodic elements
- Texture: Layered but not cluttered - producers need room to add vocals/instruments
- Reference sound: Blend of Pop Smoke's melodic sensibility with Brent Faiyaz's R&B smoothness

USER REQUEST: {user_prompt}"""
        
        # For trap/hip-hop
        elif any(word in user_prompt_lower for word in ['trap', 'hip hop', 'hiphop', '808', 'bass']):
            return f"""Create a professional {user_prompt} track with:
- Heavy 808 bass with distortion and slides
- Crisp trap drums with rolling hi-hats
- Dark atmospheric melodies
- Perfectly mixed for modern hip-hop production
- Ready to use as a beat foundation"""
        
        # For lo-fi
        elif any(word in user_prompt_lower for word in ['lo-fi', 'lofi', 'chill', 'relax', 'study']):
            return f"""Create a {user_prompt} track with:
- Warm, vinyl crackle texture
- Simple jazz or soul chord progressions
- Laid-back drum groove with swing
- Melancholy piano or guitar melodies
- Subtle atmospheric pads
- Perfect for studying or relaxing"""
        
        # Default prompt for other genres
        else:
            return f"""Create a professional music sample: {user_prompt}
- High quality production
- Clear mix with balanced frequencies
- Suitable for music production
- Ready to use in a DAW"""

    def _save_output(self, output_url: str, prompt: str) -> Path:
        """Download and save the generated audio."""
        import urllib.request

        # Create filename from prompt
        safe_prompt = "".join(c if c.isalnum() or c in ' -_' else '' for c in prompt)
        safe_prompt = safe_prompt[:50].strip().replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_prompt}_{timestamp}.wav"

        filepath = self.output_dir / filename
        urllib.request.urlretrieve(output_url, filepath)

        return filepath

    def build_prompt(
        self,
        description: str,
        bpm: Optional[int] = None,
        key: Optional[str] = None,
        style: Optional[str] = None,
        instrument: Optional[str] = None,
    ) -> str:
        """Build an optimized prompt for MusicGen."""
        parts = [description]

        if style:
            parts.append(f"{style} style")
        if instrument:
            parts.append(f"featuring {instrument}")
        if bpm:
            parts.append(f"{bpm} BPM")
        if key:
            parts.append(f"in {key}")

        parts.append("high quality, studio recording")

        return ", ".join(parts)


class MockGenerator:
    """Mock generator for testing without API."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path.home() / "Music" / "BeatSensei" / "Generated"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Simulate generation (for testing UI)."""
        import time
        time.sleep(2)  # Simulate API delay

        return GenerationResult(
            success=True,
            filepath=str(self.output_dir / "mock_sample.wav"),
            prompt=prompt,
            duration=8.0
        )
