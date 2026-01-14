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

            output = replicate.run(
                self.MODEL_ID,
                input={
                    "prompt": prompt,
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
