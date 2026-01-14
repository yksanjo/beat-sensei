"""ASCII art animations for Beat-Sensei."""

import time
import sys
import threading
from typing import Optional

# Kung Fu stick figure fight animation frames
KUNGFU_FRAMES = [
    # Frame 1 - Face off
    r"""
                    BEAT-SENSEI DOJO
    ==========================================

           O                           O
          /|\                         /|\
          / \                         / \

         "Ready..."              "Let's go!"
    """,
    # Frame 2 - Fighter 1 kicks
    r"""
                    BEAT-SENSEI DOJO
    ==========================================

           O                           O
          /|\__                       /|\
          /                           / \

         "Hyaa!"                 "Whoa!"
    """,
    # Frame 3 - Fighter 2 blocks
    r"""
                    BEAT-SENSEI DOJO
    ==========================================

           O        *BLOCK*            O
          /|\         <>__            \|/
          / \                          |

         "Nice!"                "Too slow!"
    """,
    # Frame 4 - Fighter 2 counter punches
    r"""
                    BEAT-SENSEI DOJO
    ==========================================

           O                           O
           |\_______*POW*_________    /|
          / \                         / \

         "Oof!"                  "Take that!"
    """,
    # Frame 5 - Both jump
    r"""
                    BEAT-SENSEI DOJO
    ==========================================

           O                           O
         \_|_/       *CLASH*        \_|_/
                       ><

          "Ora!"                 "Ora ora!"
    """,
    # Frame 6 - Spinning kicks
    r"""
                    BEAT-SENSEI DOJO
    ==========================================

           O__                       __O
           |      ~WHOOOOSH~          |
          /|                          |\

      "Spinning..."            "...kick!"
    """,
    # Frame 7 - Fighter 1 uppercut
    r"""
                    BEAT-SENSEI DOJO
    ==========================================

           O    *UPPERCUT*             O
          /|/                          |
          / \                         /|\

      "Shoryuken!"               "Ahhh!"
    """,
    # Frame 8 - Fighter 2 recovers
    r"""
                    BEAT-SENSEI DOJO
    ==========================================

           O                           O
          \|/     ~respect~          \|/
          / \                         / \

       "Good one..."          "You too fam"
    """,
    # Frame 9 - Both bow
    r"""
                    BEAT-SENSEI DOJO
    ==========================================

           O                           O
          _|_         <3              _|_
          / \                         / \

        "Respect"               "Always"
    """,
    # Frame 10 - Ready again
    r"""
                    BEAT-SENSEI DOJO
    ==========================================

           O                           O
          /|\      ROUND 2!           /|\
          / \                         / \

       "Again?"                "Let's GO!"
    """,
]

# Alternative: DJ/Producer themed animation
DJ_FRAMES = [
    r"""
      ___________________________
     |  ___   BEAT-SENSEI   ___  |
     | |   |  Loading...   |   | |
     | |___|    ♪ ♫ ♪     |___| |
     |  O                    O   |
     | /|\   *scratches*   /|\  |
     | / \                 / \  |
     |___________________________|
            [  TURNTABLES  ]
    """,
    r"""
      ___________________________
     |  ___   BEAT-SENSEI   ___  |
     | |   |  Loading...   |   | |
     | |___|   ♫ ♪ ♫      |___| |
     |   O                  O    |
     |  /|>  *wikka wikka* <|\   |
     |  / \                / \   |
     |___________________________|
            [  TURNTABLES  ]
    """,
    r"""
      ___________________________
     |  ___   BEAT-SENSEI   ___  |
     | |   |  Loading...   |   | |
     | |___|  ♪ ♫ ♪ ♫     |___| |
     |  \O/     *DROP*     \O/   |
     |   |    ~~~BASS~~~    |    |
     |  / \                / \   |
     |___________________________|
            [  TURNTABLES  ]
    """,
]

# Simple loading animation
LOADING_FRAMES = [
    "🥋 Loading samples... |",
    "🥋 Loading samples... /",
    "🥋 Loading samples... -",
    "🥋 Loading samples... \\",
]


class KungFuAnimation:
    """Animated ASCII art display for loading screens."""

    def __init__(self, style: str = "kungfu"):
        if style == "kungfu":
            self.frames = KUNGFU_FRAMES
        elif style == "dj":
            self.frames = DJ_FRAMES
        else:
            self.frames = LOADING_FRAMES

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.frame_delay = 0.8 if style == "kungfu" else 0.5

    def _clear_lines(self, n: int):
        """Move cursor up and clear lines."""
        for _ in range(n):
            sys.stdout.write('\033[A')  # Move up
            sys.stdout.write('\033[K')  # Clear line

    def _animate(self):
        """Animation loop."""
        frame_idx = 0
        prev_lines = 0

        while self._running:
            frame = self.frames[frame_idx % len(self.frames)]

            # Clear previous frame
            if prev_lines > 0:
                self._clear_lines(prev_lines)

            # Print new frame
            print(frame)
            prev_lines = frame.count('\n') + 1

            frame_idx += 1
            time.sleep(self.frame_delay)

    def start(self):
        """Start the animation in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the animation."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None


def show_kungfu_battle(duration: float = 5.0):
    """Show kung fu animation for a specified duration."""
    anim = KungFuAnimation(style="kungfu")
    anim.start()
    time.sleep(duration)
    anim.stop()


def animate_with_callback(callback, style: str = "kungfu"):
    """Run a callback while showing animation."""
    anim = KungFuAnimation(style=style)
    anim.start()
    try:
        result = callback()
    finally:
        anim.stop()
    return result


# Simple progress bar with kung fu messages
KUNGFU_MESSAGES = [
    "Training your samples...",
    "Mastering the art of beats...",
    "Channeling the rhythm...",
    "Focusing your chi...",
    "The way of the sample...",
    "Discipline brings fire beats...",
    "Patience, young producer...",
    "The beat drops when ready...",
    "Wax on, wax off the beat...",
    "Finding inner groove...",
]


def get_random_kungfu_message() -> str:
    """Get a random kung fu themed loading message."""
    import random
    return random.choice(KUNGFU_MESSAGES)
