"""Configuration management for Beat-Sensei."""

import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
import yaml


@dataclass
class Config:
    """Beat-Sensei configuration."""
    sample_folders: List[str] = field(default_factory=list)
    output_folder: str = ""
    replicate_api_token: Optional[str] = None
    openai_api_key: Optional[str] = None
    default_bpm: int = 90
    audio_format: str = "wav"
    tier: str = "free"
    license_key: Optional[str] = None

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

        config = cls()

        if config_path.exists():
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f) or {}

            config.sample_folders = data.get('sample_folders', [])
            config.output_folder = data.get('output_folder', str(Path.home() / "Music" / "BeatSensei" / "Generated"))
            config.default_bpm = data.get('preferences', {}).get('default_bpm', 90)
            config.audio_format = data.get('preferences', {}).get('audio_format', 'wav')
            config.tier = data.get('tier', 'free')
            config.license_key = data.get('license_key')

        # Override with environment variables
        config.replicate_api_token = os.getenv('REPLICATE_API_TOKEN')
        config.openai_api_key = os.getenv('OPENAI_API_KEY')

        # Expand paths
        config.sample_folders = [os.path.expanduser(f) for f in config.sample_folders]
        config.output_folder = os.path.expanduser(config.output_folder)

        return config

    def save(self, config_path: Optional[Path] = None):
        """Save configuration to file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

        data = {
            'sample_folders': self.sample_folders,
            'output_folder': self.output_folder,
            'preferences': {
                'default_bpm': self.default_bpm,
                'audio_format': self.audio_format,
            },
            'tier': self.tier,
            'license_key': self.license_key,
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def add_sample_folder(self, folder: str):
        """Add a sample folder to the configuration."""
        folder = os.path.expanduser(folder)
        if folder not in self.sample_folders:
            self.sample_folders.append(folder)

    def get_sample_folders(self) -> List[Path]:
        """Get sample folders as Path objects."""
        return [Path(f) for f in self.sample_folders if Path(f).exists()]
