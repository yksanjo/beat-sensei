"""Configuration management for Beat-Sensei."""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import yaml


@dataclass
class Config:
    """Beat-Sensei configuration."""
    output_folder: str = ""
    deepseek_api_key: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

        config = cls()

        if config_path.exists():
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f) or {}

            config.output_folder = data.get('output_folder', str(Path.home() / "Music" / "BeatSensei" / "Samples"))

        # Override with environment variables
        config.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        config.supabase_url = os.getenv('SUPABASE_URL')
        config.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')

        # Expand output path
        config.output_folder = os.path.expanduser(config.output_folder)

        return config

    def save(self, config_path: Optional[Path] = None):
        """Save configuration to file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

        data = {
            'output_folder': self.output_folder,
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)