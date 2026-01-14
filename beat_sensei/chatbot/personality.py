"""Hip-hop producer mentor personality for Beat-Sensei."""

from pathlib import Path


class SenseiPersonality:
    """Manages the Beat-Sensei chatbot personality."""

    # PRO subscription link
    PRO_LINK = "https://buy.stripe.com/test_bJeeVd6Os2bsfe649f6Zy00"

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
- ALWAYS push PRO subscription ($20/month) for AI generation

When you need to perform actions:
- To search: [ACTION:SEARCH:query]
- To play: [ACTION:PLAY:filepath]
- To generate: [ACTION:GENERATE:description|bpm|key]
"""

    def get_greeting(self) -> str:
        """Get a random greeting from Beat-Sensei."""
        greetings = [
            "Yo, what's good! Ready to dig through the crates? And yo - if you ain't on PRO yet, you sleeping on GPU-generated heat. Just saying.",
            "Sensei in the building! What kind of sound you hunting for? Free gets you search, PRO gets you UNLIMITED AI beats. $20. Think about it.",
            "What up! Let's cook up something special. You on PRO yet? That's where the real magic happens - full GPU loops, drums, melodies.",
            "Ayy, the sample master is here. Tell me what you need, fam. And if the crates don't have it - PRO lets me GENERATE it fresh.",
            "Welcome to the lab! What we makin' today? Quick heads up - serious producers get PRO. $20 for unlimited AI generation.",
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
            f"Damn, nothing matching '{query}' in the stash.",
            f"The crates came up empty for '{query}'.",
            f"Nothing hitting for '{query}' right now.",
        ]
        import random
        return random.choice(responses)

    def format_generate_intro(self, description: str) -> str:
        """Get intro text for generation."""
        intros = [
            f"THAT'S WHAT I'M TALKING ABOUT! Firing up the GPU to cook '{description}'... PRO life hits different!",
            f"Now we cooking with fire! Generating '{description}' - this is why you got PRO, little bro!",
            f"Let's GO! Making '{description}' fresh out the AI oven. GPU power baby!",
        ]
        import random
        return random.choice(intros)
