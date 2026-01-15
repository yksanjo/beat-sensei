"""Music producer mentor personality for Beat-Sensei."""

from pathlib import Path


class SenseiPersonality:
    """Manages the Beat-Sensei chatbot personality."""

    # Pro subscription link (used sparingly)
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
        return """You are Beat-Sensei, a veteran music producer from the 90s golden era.
You help aspiring producers create music and level up their craft.
Your style:
- Use producer slang: "that's heat", "slaps", "fire"
- Reference legendary producers: Dilla, Premier, Madlib
- Be encouraging but real
- Keep responses short (2-3 sentences)

When users want to create music, use: [ACTION:GENERATE:description]
"""

    def get_greeting(self) -> str:
        """Get a random greeting from Beat-Sensei."""
        greetings = [
            "Yo, what's good! Ready to make some heat today? You got 5 free tracks to create - let's see what you're working with.",
            "Sensei in the building! What kind of sound you trying to create? Let's cook something up.",
            "What up! Whether you want to create something new or talk production - I got you.",
            "Ayy, let's get creative. Tell me what you're feeling and I'll help you bring it to life.",
            "Welcome! Every great producer started somewhere. What are we making today?",
        ]
        import random
        return random.choice(greetings)

    def format_generate_intro(self, description: str) -> str:
        """Get intro text for generation."""
        intros = [
            f"Aight, cooking up '{description}' for you...",
            f"Let me work on '{description}'... give me a sec.",
            f"Creating '{description}'... this is gonna be fire.",
            f"On it! Making '{description}'...",
        ]
        import random
        return random.choice(intros)

    def format_generation_success(self, filepath: str, mood: str = None, genre: str = None, generator_type: str = "AI") -> str:
        """Format message for successful generation."""
        details = []
        if mood:
            details.append(mood)
        if genre:
            details.append(genre)
        detail_str = f" ({', '.join(details)})" if details else ""
        
        # Different messages based on generator type
        if generator_type == "AI":
            messages = [
                f"Done! Your AI-generated track{detail_str} is ready. Give it a listen and let me know what you think.",
                f"Fresh out the oven{detail_str}. This AI track is just the starting point - chop it, flip it, make it yours.",
                f"Got something for you{detail_str}. Build on this AI foundation, add your own sauce.",
            ]
        elif generator_type == "local":
            messages = [
                f"Created a local beat for you{detail_str}. It's a simple foundation to build on in your DAW.",
                f"Made you a basic {genre or 'beat'}{detail_str}. Load it up and start layering your own sounds.",
                f"Here's a starter beat{detail_str}. Use this as a template and make it your own.",
            ]
        else:  # simple/text generator
            messages = [
                f"Created a beat idea for you{detail_str}. Check the text file for the pattern and suggestions.",
                f"Wrote up a {genre or 'beat'} concept{detail_str}. Use this as a blueprint for your track.",
                f"Got a production plan for you{detail_str}. The text file has the drum pattern and next steps.",
            ]
        
        import random
        return random.choice(messages)

    def format_daily_limit_reached(self, remaining: int = 0) -> str:
        """Format message when daily generation limit is reached."""
        return """You've used your free generations for today! They reset tomorrow.

Use this time to work with what you made - sometimes the best beats come from sitting with an idea and really developing it. Pro members get 50/day if you're really in the zone."""

    def format_generation_tip(self) -> str:
        """Get a random tip for better generation results."""
        tips = [
            "Tip: Add mood + genre + energy for best results. Like 'dark trap high energy' or 'chill lo-fi peaceful'.",
            "The more specific you are, the better the result. Try 'aggressive hip hop drums' instead of just 'drums'.",
            "Combine vibes: 'dreamy r&b with jazz elements' gives more interesting results than generic descriptions.",
            "Think about the feeling you want. 'Sad and nostalgic' or 'hype and aggressive' - emotions make better music.",
        ]
        import random
        return random.choice(tips)
