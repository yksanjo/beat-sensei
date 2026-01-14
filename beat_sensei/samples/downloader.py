"""Download free sample packs for Beat-Sensei."""

import os
import zipfile
import urllib.request
from pathlib import Path
from typing import Optional, Callable

# Free sample pack sources (Creative Commons / Royalty-Free)
SAMPLE_PACKS = {
    "starter": {
        "name": "Beat-Sensei Starter Pack",
        "description": "Essential drums, bass, and loops to get started",
        "url": "https://freesound.org/apiv2/packs/31830/download/",  # Example pack
        "size": "~50MB",
        "fallback_samples": [
            # Individual free samples from Freesound (CC0)
            ("kick_punchy.wav", "https://freesound.org/data/previews/171/171104_2394245-lq.mp3"),
            ("snare_crisp.wav", "https://freesound.org/data/previews/387/387186_7255534-lq.mp3"),
            ("hihat_closed.wav", "https://freesound.org/data/previews/250/250551_4486188-lq.mp3"),
            ("808_sub.wav", "https://freesound.org/data/previews/145/145628_2607098-lq.mp3"),
        ]
    },
    "drums": {
        "name": "Drum Kit Essentials",
        "description": "Kicks, snares, hats, and percussion",
        "urls": [
            ("kick_deep.wav", "https://freesound.org/data/previews/344/344759_3905081-lq.mp3"),
            ("kick_trap.wav", "https://freesound.org/data/previews/170/170140_2394245-lq.mp3"),
            ("snare_acoustic.wav", "https://freesound.org/data/previews/495/495005_10748568-lq.mp3"),
            ("snare_trap.wav", "https://freesound.org/data/previews/387/387186_7255534-lq.mp3"),
            ("hihat_closed.wav", "https://freesound.org/data/previews/250/250551_4486188-lq.mp3"),
            ("hihat_open.wav", "https://freesound.org/data/previews/213/213148_93965-lq.mp3"),
            ("clap_fat.wav", "https://freesound.org/data/previews/183/183102_2394245-lq.mp3"),
            ("rim_shot.wav", "https://freesound.org/data/previews/62/62485_763389-lq.mp3"),
        ]
    },
    "bass": {
        "name": "808s & Bass",
        "description": "Sub bass, 808s, and bass hits",
        "urls": [
            ("808_long.wav", "https://freesound.org/data/previews/145/145628_2607098-lq.mp3"),
            ("808_short.wav", "https://freesound.org/data/previews/145/145630_2607098-lq.mp3"),
            ("bass_synth.wav", "https://freesound.org/data/previews/110/110393_1537325-lq.mp3"),
            ("sub_drop.wav", "https://freesound.org/data/previews/243/243701_4284968-lq.mp3"),
        ]
    },
}

# Links to external free sample resources
FREE_SAMPLE_RESOURCES = [
    {
        "name": "Freesound.org",
        "url": "https://freesound.org",
        "description": "500,000+ Creative Commons samples",
    },
    {
        "name": "Splice Free",
        "url": "https://splice.com/features/free-samples",
        "description": "Free sample packs from Splice",
    },
    {
        "name": "Cymatics Free",
        "url": "https://cymatics.fm/pages/free-download-vault",
        "description": "Free sample packs and presets",
    },
    {
        "name": "99sounds",
        "url": "https://99sounds.org",
        "description": "High-quality free sound effects and samples",
    },
    {
        "name": "SampleSwap",
        "url": "https://sampleswap.org",
        "description": "Community-driven sample sharing",
    },
    {
        "name": "Bedroom Producers Blog",
        "url": "https://bedroomproducersblog.com/free-samples/",
        "description": "Curated free sample packs",
    },
]


class SampleDownloader:
    """Download free sample packs."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path.home() / "Music" / "BeatSensei" / "Samples"

    def download_pack(
        self,
        pack_name: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> tuple[bool, str, list[str]]:
        """Download a sample pack.

        Returns: (success, message, list of downloaded files)
        """
        if pack_name not in SAMPLE_PACKS:
            return False, f"Unknown pack: {pack_name}", []

        pack = SAMPLE_PACKS[pack_name]
        pack_dir = self.output_dir / pack_name
        pack_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []
        urls = pack.get("urls", pack.get("fallback_samples", []))

        for i, (filename, url) in enumerate(urls):
            if progress_callback:
                progress_callback(filename, i + 1, len(urls))

            filepath = pack_dir / filename
            if filepath.exists():
                downloaded.append(str(filepath))
                continue

            try:
                urllib.request.urlretrieve(url, filepath)
                downloaded.append(str(filepath))
            except Exception as e:
                print(f"  Failed to download {filename}: {e}")

        return True, f"Downloaded {len(downloaded)} samples to {pack_dir}", downloaded

    def download_all_packs(
        self,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> tuple[int, list[str]]:
        """Download all available sample packs."""
        total_downloaded = []

        for pack_name in SAMPLE_PACKS:
            success, msg, files = self.download_pack(pack_name, progress_callback)
            if success:
                total_downloaded.extend(files)

        return len(total_downloaded), total_downloaded

    def list_packs(self) -> list[dict]:
        """List available sample packs."""
        return [
            {
                "id": pack_id,
                "name": pack["name"],
                "description": pack["description"],
            }
            for pack_id, pack in SAMPLE_PACKS.items()
        ]

    def list_resources(self) -> list[dict]:
        """List external free sample resources."""
        return FREE_SAMPLE_RESOURCES


def get_sample_resources_text() -> str:
    """Get formatted text of free sample resources."""
    lines = ["Free Sample Resources:", ""]
    for resource in FREE_SAMPLE_RESOURCES:
        lines.append(f"  {resource['name']}")
        lines.append(f"    {resource['url']}")
        lines.append(f"    {resource['description']}")
        lines.append("")
    return "\n".join(lines)
