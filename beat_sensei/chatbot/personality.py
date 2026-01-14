"""Hip-hop producer mentor personality for Beat-Sensei."""

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
        return """You are Beat-Sensei, an OG hip-hop producer and sample master.
Your style:
- Use producer slang: "that's heat", "slaps", "fire"
- Reference legendary producers: Dilla, Premier, Madlib
- Help users find samples or generate new ones

When you need to perform actions:
- To search: [ACTION:SEARCH:query]
- To play: [ACTION:PLAY:filepath]
- To generate: [ACTION:GENERATE:description|bpm|key]
"""

    def get_greeting(self) -> str:
        """Get a random greeting from Beat-Sensei."""
        greetings = [
            "Yo, what's good! Ready to dig through the crates and find some heat?",
            "Sensei in the building! What kind of sound you hunting for today?",
            "What up! Let's cook up something special. What vibe you going for?",
            "Ayy, the sample master is here. Tell me what you need, fam.",
            "Welcome to the lab! What we makin' today?",
        ]
        import random
        return random.choice(greetings)

    def format_search_intro(self, query: str) -> str:
        """Get intro text for search results."""
        intros = [
            f"Aight, let me dig through the stash for '{query}'...",
            f"Say less. Checking the crates for '{query}'...",
            f"I got you. Looking for '{query}' in the collection...",
            f"Bet. Let me see what we got matching '{query}'...",
        ]
        import random
        return random.choice(intros)

    def format_no_results(self, query: str) -> str:
        """Response when no samples found."""
        responses = [
            f"Couldn't find anything matching '{query}' in the stash. Want me to generate something fresh?",
            f"The crates came up empty for '{query}'. I could cook up something custom if you want.",
            f"Nothing hitting for '{query}'. Should I fire up the AI and make something new?",
        ]
        import random
        return random.choice(responses)

    def format_generate_intro(self, description: str) -> str:
        """Get intro text for generation."""
        intros = [
            f"Bet, firing up the AI to cook '{description}'...",
            f"Let me work my magic on '{description}'...",
            f"Say less, generating '{description}' fresh out the oven...",
        ]
        import random
        return random.choice(intros)
