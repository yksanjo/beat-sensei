"""Audio player for terminal preview."""

import os
import sys
import threading
from pathlib import Path
from typing import Optional


class SamplePlayer:
    """Play audio samples in the terminal."""

    def __init__(self):
        self._current_file: Optional[str] = None
        self._is_playing = False
        self._player_thread: Optional[threading.Thread] = None
        self._pygame_initialized = False

    def _init_pygame(self):
        """Initialize pygame mixer (lazy loading)."""
        if not self._pygame_initialized:
            try:
                # Suppress pygame welcome message
                os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
                import pygame
                pygame.mixer.init()
                self._pygame_initialized = True
            except ImportError:
                pass

    def play(self, filepath: str) -> bool:
        """Play an audio file."""
        filepath = Path(filepath)
        if not filepath.exists():
            return False

        self._init_pygame()

        try:
            import pygame

            # Stop any current playback
            self.stop()

            self._current_file = str(filepath)
            pygame.mixer.music.load(str(filepath))
            pygame.mixer.music.play()
            self._is_playing = True
            return True

        except ImportError:
            # Fallback to afplay on macOS
            return self._play_with_afplay(str(filepath))
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False

    def _play_with_afplay(self, filepath: str) -> bool:
        """Fallback player using macOS afplay."""
        import subprocess
        try:
            self.stop()
            self._current_file = filepath
            self._player_thread = threading.Thread(
                target=lambda: subprocess.run(['afplay', filepath], capture_output=True)
            )
            self._player_thread.start()
            self._is_playing = True
            return True
        except Exception:
            return False

    def stop(self):
        """Stop current playback."""
        try:
            import pygame
            if self._pygame_initialized:
                pygame.mixer.music.stop()
        except ImportError:
            # Kill any afplay process
            import subprocess
            subprocess.run(['pkill', '-f', 'afplay'], capture_output=True)

        self._is_playing = False
        self._current_file = None

    def pause(self):
        """Pause current playback."""
        try:
            import pygame
            if self._pygame_initialized and self._is_playing:
                pygame.mixer.music.pause()
                self._is_playing = False
        except ImportError:
            pass

    def resume(self):
        """Resume paused playback."""
        try:
            import pygame
            if self._pygame_initialized:
                pygame.mixer.music.unpause()
                self._is_playing = True
        except ImportError:
            pass

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        try:
            import pygame
            if self._pygame_initialized:
                return pygame.mixer.music.get_busy()
        except ImportError:
            pass
        return self._is_playing

    def get_current_file(self) -> Optional[str]:
        """Get the currently playing file."""
        return self._current_file

    def set_volume(self, volume: float):
        """Set playback volume (0.0 to 1.0)."""
        try:
            import pygame
            if self._pygame_initialized:
                pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        except ImportError:
            pass


def play_preview(filepath: str, duration: float = 5.0):
    """Quick preview function - plays for specified duration then stops."""
    import time

    player = SamplePlayer()
    if player.play(filepath):
        time.sleep(duration)
        player.stop()
        return True
    return False
