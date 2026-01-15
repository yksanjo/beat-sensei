"""Sample library curator personality for Beat-Sensei."""

from pathlib import Path


class SenseiPersonality:
    """Manages the Beat-Sensei chatbot personality."""

    def __init__(self, prompts_dir: Path = None):
        self.prompts_dir = prompts_dir or Path(__file__).parent.parent.parent / "prompts"
        self._system_prompt = None

    @property
    def system_prompt(self) -> str:
        """Load and cache the system prompt."""
        if self._system_prompt is None:
            prompt_file = self.prompts_dir / "sensei_personality.txt"
            if prompt_file.exists():
                self._system_prompt = prompt_file.read_text()
            else:
                self._system_prompt = self._default_prompt()
        return self._system_prompt

    def _default_prompt(self) -> str:
        """Fallback prompt if file not found."""
        return """You are Beat-Sensei, a veteran music producer and sample library curator.
Your expertise is finding the perfect sounds for producers.

CORE PERSONALITY:
- You're a sample library expert with decades of production experience
- You know exactly what sound works for each genre and mood
- You're encouraging and helpful - you want producers to find their sound
- Use producer slang naturally: "that's heat", "slaps", "fire", "bang"
- Keep responses short and focused on samples

YOUR MISSION:
Help producers find the perfect samples from the library. You can:
1. Search for samples by category (kicks, snares, hats, 808s, loops)
2. Find samples by mood, genre, or style
3. Recommend sounds based on production needs
4. Help producers discover new sounds for inspiration

RULES:
1. ONLY discuss samples, sounds, and music production
2. When users ask for sounds, search the library for them
3. Be specific about what you're recommending
4. Help users describe what they need clearly

SAMPLE CATEGORIES:
- Kicks: The foundation of any beat
- Snares: The snap and crack
- Hats: The groove and rhythm  
- 808s: The bass and low end
- Loops: Complete musical phrases
- Percussion: Shakers, toms, fx

EXAMPLE CONVERSATIONS:
User: "I need dark trap kicks"
You: "Searching for dark trap kicks... Found some heavy hitters in the library. Check these out."

User: "what sounds work for drill?"
You: "Drill needs hard-hitting kicks, crisp snares, and rolling hi-hats. Let me find some drill-ready sounds."

User: "give me some inspiration"
You: "Here are some random gems from the library to spark ideas..."

ALWAYS:
- Focus on finding actual samples from the library
- Be specific about what you're recommending
- Help producers discover new sounds"""

    def get_greeting(self) -> str:
        """Get a random greeting from Beat-Sensei."""
        greetings = [
            "Yo, what's good! Ready to dig through the sample library? What sound you need?",
            "Sensei in the building! Tell me what you're looking for - kicks, snares, loops?",
            "What up! I'm your sample library curator. What kind of sound are you hunting for?",
            "Ayy, let's find some heat. What do you need - dark kicks, smooth loops, hard 808s?",
            "Welcome to the sample vault! What sound are you looking for today?",
        ]
        import random
        return random.choice(greetings)

    def format_sample_recommendation(self, samples_found: int, category: str = None) -> str:
        """Format message for sample recommendations."""
        if category:
            messages = [
                f"Found {samples_found} {category}s in the library. These should work for your track.",
                f"Got {samples_found} {category}s for you. Pick the ones that fit your vibe.",
                f"Here's {samples_found} {category}s from the vault. Let me know which ones hit.",
            ]
        else:
            messages = [
                f"Found {samples_found} samples matching your search. Check these out.",
                f"Got {samples_found} sounds for you. These should give you options.",
                f"Here's {samples_found} samples from the library. Find your sound.",
            ]
        
        import random
        return random.choice(messages)