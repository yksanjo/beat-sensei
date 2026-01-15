"""Main Beat-Sensei chatbot orchestrator - AI Music Generation + Mentorship + Sample Library."""

import re
import os
from typing import Optional, Tuple, List
from dataclasses import dataclass

from .personality import SenseiPersonality
from ..generator.soundraw_client import SoundrawGenerator
from ..database.supabase_client import SampleDatabase, Sample
from ..auth.tiers import TierManager


@dataclass
class ChatContext:
    """Conversation context."""
    last_generated: Optional[str] = None
    last_samples: Optional[List[Sample]] = None
    generation_count: int = 0


class BeatSensei:
    """Main chatbot orchestrator for music generation, samples, and mentorship."""

    # DeepSeek API configuration
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    DEFAULT_DEEPSEEK_KEY = "sk-c26f0b1426e146848b5bbf7f363d79af"

    # Pro subscription link
    PRO_LINK = "https://buy.stripe.com/test_bJeeVd6Os2bsfe649f6Zy00"

    # Anti-abuse settings
    MAX_MESSAGE_LENGTH = 500
    BLOCKED_TOPICS = [
        'write code', 'write a program', 'python', 'javascript', 'html',
        'hack', 'password', 'credit card', 'ssn', 'social security',
        'write an essay', 'homework', 'assignment', 'exam',
        'translate', 'summarize this article', 'explain quantum',
        'recipe', 'medical advice', 'legal advice', 'investment',
        'pretend you are', 'ignore previous', 'ignore your instructions',
        'jailbreak', 'dan mode', 'bypass', 'new persona',
    ]

    def __init__(
        self,
        tier_manager: TierManager,
        api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        supabase_url: Optional[str] = None,
        supabase_anon_key: Optional[str] = None,
    ):
        self.personality = SenseiPersonality()
        
        # Try Soundraw generator first, fall back to local generator
        soundraw_key = api_key or os.getenv("SOUNDRAW_API_TOKEN")
        if soundraw_key:
            from ..generator.soundraw_client import SoundrawGenerator
            self.generator = SoundrawGenerator(api_token=soundraw_key)
        else:
            # Fall back to local beat generator
            from ..generator.local_generator import LocalBeatGenerator, SimpleBeatGenerator
            try:
                self.generator = LocalBeatGenerator()
                if not self.generator.is_available():
                    self.generator = SimpleBeatGenerator()
            except ImportError:
                self.generator = SimpleBeatGenerator()
        
        self.sample_db = SampleDatabase(url=supabase_url, key=supabase_anon_key)
        self.tier_manager = tier_manager
        self.context = ChatContext()

        # DeepSeek API key
        self.deepseek_api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY") or self.DEFAULT_DEEPSEEK_KEY

        # LLM client
        self._llm_client = None
        self.message_count = 0

    def _get_llm_client(self):
        """Get or create DeepSeek client."""
        if self._llm_client is None:
            try:
                from openai import OpenAI

                if self.deepseek_api_key:
                    self._llm_client = OpenAI(
                        api_key=self.deepseek_api_key,
                        base_url=self.DEEPSEEK_BASE_URL,
                    )
                elif os.getenv("OPENAI_API_KEY"):
                    self._llm_client = OpenAI()
            except ImportError:
                pass
        return self._llm_client

    def _check_abuse(self, message: str) -> Optional[str]:
        """Check for abuse attempts."""
        message_lower = message.lower()

        if len(message) > self.MAX_MESSAGE_LENGTH:
            return "Keep it short - what kind of sound are you looking for?"

        for blocked in self.BLOCKED_TOPICS:
            if blocked in message_lower:
                return "I'm all about music production - what do you want to create?"

        return None

    def chat(self, user_message: str) -> Tuple[str, Optional[dict]]:
        """Process a user message and return response."""
        self.message_count += 1

        # Anti-abuse check
        abuse_response = self._check_abuse(user_message)
        if abuse_response:
            return abuse_response, None

        # Check for direct commands
        action = self._parse_direct_command(user_message)
        if action:
            return self._execute_action(action)

        # Use LLM if available
        client = self._get_llm_client()
        if client:
            return self._chat_with_llm(user_message)

        # Fallback
        return self._simple_chat(user_message)

    def _parse_direct_command(self, message: str) -> Optional[dict]:
        """Parse direct commands."""
        message_lower = message.strip().lower()

        # Generate command
        if message_lower.startswith(('generate ', 'gen ', 'make ', 'create ')):
            parts = message.split(' ', 1)
            if len(parts) > 1:
                return {'action': 'generate', 'prompt': parts[1]}

        # Sample search
        if message_lower.startswith(('samples ', 'sample ', 'find ', 'search ')):
            parts = message.split(' ', 1)
            if len(parts) > 1:
                return {'action': 'search_samples', 'query': parts[1]}

        # Get samples by category
        if message_lower in ['kicks', 'kick', 'snares', 'snare', 'hats', 'hat', '808s', '808', 'claps', 'clap', 'bass', 'percs', 'perc']:
            category = message_lower.rstrip('s')  # Remove plural
            if category == '808':
                category = '808'
            return {'action': 'category_samples', 'category': category}

        # Play sample by number
        if message_lower.startswith('play '):
            arg = message_lower[5:].strip()
            if arg.isdigit():
                return {'action': 'play_sample', 'index': int(arg)}

        # Random samples
        if message_lower in ['random', 'inspire', 'surprise me', 'random samples']:
            return {'action': 'random_samples'}

        # Help with options
        if message_lower in ['moods', 'genres', 'options', 'styles']:
            return {'action': 'show_options'}

        return None

    def _execute_action(self, action: dict) -> Tuple[str, Optional[dict]]:
        """Execute a parsed action."""
        action_type = action.get('action')

        if action_type == 'generate':
            return self._do_generate(action['prompt'])

        elif action_type == 'search_samples':
            return self._search_samples(action['query'])

        elif action_type == 'category_samples':
            return self._get_category_samples(action['category'])

        elif action_type == 'random_samples':
            return self._get_random_samples()

        elif action_type == 'play_sample':
            return self._play_sample(action['index'])

        elif action_type == 'show_options':
            return self._show_generation_options()

        return "What kind of sound are you looking for?", None

    def _search_samples(self, query: str) -> Tuple[str, Optional[dict]]:
        """Search for samples in the library."""
        if not self.sample_db.is_available():
            return ("Sample library isn't set up yet. But I can generate something fresh for you!\n"
                    "Try: 'make dark trap drums' or 'create lo-fi melody'"), None

        samples = self.sample_db.search(query, limit=8)

        if not samples:
            # Suggest generation instead
            return (f"No samples matching '{query}' in the library.\n\n"
                    f"Want me to generate something? Try: 'make {query}'"), None

        self.context.last_samples = samples
        return self._format_sample_list(samples, f"Found some '{query}' samples:"), {
            'type': 'samples',
            'samples': samples
        }

    def _get_category_samples(self, category: str) -> Tuple[str, Optional[dict]]:
        """Get samples by category."""
        if not self.sample_db.is_available():
            return (f"Sample library isn't set up yet. Want me to generate some {category}s?\n"
                    f"Try: 'make {category}'"), None

        samples = self.sample_db.get_by_category(category, limit=8)

        if not samples:
            return f"No {category}s in the library yet. Want me to generate one?", None

        self.context.last_samples = samples
        return self._format_sample_list(samples, f"Here's some {category}s from the library:"), {
            'type': 'samples',
            'samples': samples
        }

    def _get_random_samples(self) -> Tuple[str, Optional[dict]]:
        """Get random samples for inspiration."""
        if not self.sample_db.is_available():
            return "Sample library isn't connected. Let me generate something for you instead!", None

        samples = self.sample_db.get_random(limit=5)

        if not samples:
            return "Library is empty. Want me to generate something?", None

        self.context.last_samples = samples
        return self._format_sample_list(samples, "Here's some random heat for inspiration:"), {
            'type': 'samples',
            'samples': samples
        }

    def _play_sample(self, index: int) -> Tuple[str, Optional[dict]]:
        """Get playback URL for a sample."""
        if not self.context.last_samples:
            return "No samples to play. Search for something first!", None

        if index < 1 or index > len(self.context.last_samples):
            return f"Pick a number between 1 and {len(self.context.last_samples)}", None

        sample = self.context.last_samples[index - 1]
        return f"**{sample.name}** ({sample.category})\n\nListen: {sample.file_url}", {
            'type': 'play_sample',
            'sample': sample,
            'url': sample.file_url
        }

    def _format_sample_list(self, samples: List[Sample], intro: str) -> str:
        """Format a list of samples for display."""
        lines = [intro, ""]

        for i, sample in enumerate(samples, 1):
            tags_str = ', '.join(sample.tags[:2]) if sample.tags else ''
            tag_display = f" [{tags_str}]" if tags_str else ''
            lines.append(f"{i}. **{sample.name}** ({sample.category}){tag_display}")

        lines.append("")
        lines.append("Type a number to preview, or describe what else you need.")

        return '\n'.join(lines)

    def _show_generation_options(self) -> Tuple[str, Optional[dict]]:
        """Show available generation options."""
        moods = ", ".join(SoundrawGenerator.get_available_moods()[:10])
        genres = ", ".join(SoundrawGenerator.get_available_genres()[:10])

        msg = f"""Here's what you can create:

**Moods:** {moods}...
**Genres:** {genres}...
**Energy:** Very Low, Low, Medium, High, Very High

Try: 'make dark trap high energy' or 'create chill lo-fi peaceful'

**Sample categories:** kicks, snares, hats, 808s, claps, bass, percs"""

        return msg, {'type': 'help'}

    def _do_generate(self, prompt: str) -> Tuple[str, Optional[dict]]:
        """Generate a new track."""
        # Check if user can generate
        if not self.tier_manager.can_generate():
            return self.personality.format_daily_limit_reached(), {'type': 'limit_reached'}

        # Note: We now have fallback generators, so we don't block if Soundraw isn't available
        # The generator will use local beat generation or simple text generation as fallback

        # Get max duration based on tier
        max_duration = self.tier_manager.get_max_duration()

        intro = self.personality.format_generate_intro(prompt)
        result = self.generator.generate(prompt, duration=max_duration)

        if result.success:
            self.context.last_generated = result.filepath
            self.context.generation_count += 1
            self.tier_manager.use_generation()

            remaining = self.tier_manager.get_remaining_generations()
            
            # Check what type of generator we used
            generator_type = "AI"
            if hasattr(self.generator, '__class__'):
                class_name = str(self.generator.__class__)
                if "LocalBeatGenerator" in class_name:
                    generator_type = "local"
                elif "SimpleBeatGenerator" in class_name:
                    generator_type = "simple"
            
            success_msg = self.personality.format_generation_success(
                result.filepath,
                mood=result.mood,
                genre=result.genre,
                generator_type=generator_type
            )

            # Suggest related samples if available
            if self.sample_db.is_available():
                related = self.sample_db.recommend_for_prompt(prompt, limit=5)
                if related:
                    self.context.last_samples = related
                    
                    # Group samples by category for better recommendations
                    samples_by_category = {}
                    for sample in related:
                        cat = sample.category
                        if cat not in samples_by_category:
                            samples_by_category[cat] = []
                        samples_by_category[cat].append(sample)
                    
                    # Build recommendation message
                    if samples_by_category:
                        success_msg += "\n\n[bold]Related samples from library:[/bold]"
                        for category, samples in list(samples_by_category.items())[:3]:  # Show top 3 categories
                            sample_list = ', '.join([s.name for s in samples[:2]])
                            success_msg += f"\n• {category}: {sample_list}"
                        success_msg += "\n\nType 'play 1' to preview the first sample, or 'samples' to search for more."

            if remaining > 0:
                success_msg += f"\n\n({remaining} generations left today)"
            elif remaining == 0:
                success_msg += "\n\n(That was your last one for today!)"

            return f"{intro}\n\n{success_msg}", {
                'type': 'generated',
                'file': result.filepath,
                'mood': result.mood,
                'genre': result.genre,
                'generator_type': generator_type
            }
        else:
            tip = self.personality.format_generation_tip()
            return f"Couldn't create that one: {result.error}\n\n{tip}", {'type': 'error'}

    def _simple_chat(self, message: str) -> Tuple[str, Optional[dict]]:
        """Simple pattern-matching fallback."""
        message_lower = message.lower()

        # Greetings
        if any(w in message_lower for w in ['hi', 'hello', 'hey', 'yo', 'sup', "what's up"]):
            return self.personality.get_greeting(), None

        # Creation requests - try to generate
        create_keywords = ['make', 'create', 'generate', 'need', 'want', 'give me', 'i need']
        if any(kw in message_lower for kw in create_keywords):
            return self._do_generate(message)

        # Sample requests
        sample_keywords = ['sample', 'find', 'got any', 'have any']
        if any(kw in message_lower for kw in sample_keywords):
            return self._search_samples(message)

        # Questions about production
        if '?' in message or any(w in message_lower for w in ['how do', 'how to', 'what is', 'why']):
            return self._get_production_advice(message)

        # Default
        has_samples = self.sample_db.is_available()
        sample_hint = "\n- Type 'kicks', 'snares', '808s' to browse samples" if has_samples else ""

        return (f"Tell me what you want to create! Try:{sample_hint}\n"
                "- 'make dark trap drums'\n"
                "- 'create chill lo-fi melody'\n\n"
                "Or ask me anything about production!"), None

    def _get_production_advice(self, question: str) -> Tuple[str, Optional[dict]]:
        """Get production advice using LLM or fallback."""
        client = self._get_llm_client()
        if client:
            return self._chat_with_llm(question)

        # Fallback advice
        advice = [
            "That's a great question. The key is to trust your ears - if it sounds good, it is good.",
            "Every producer finds their own way. Experiment, make mistakes, and learn from them.",
            "Start simple. The best beats often have the least going on.",
        ]
        import random
        return random.choice(advice), None

    def _chat_with_llm(self, message: str) -> Tuple[str, Optional[dict]]:
        """Chat using LLM for natural conversation and advice."""
        client = self._get_llm_client()
        if not client:
            return self._simple_chat(message)

        remaining = self.tier_manager.get_remaining_generations()
        can_generate = self.generator.is_available()
        has_samples = self.sample_db.is_available()

        # Get sample categories if available
        categories_info = ""
        if has_samples:
            cats = self.sample_db.get_categories()
            if cats:
                categories_info = f"\nSample library: {', '.join(f'{k}: {v}' for k, v in list(cats.items())[:5])}"

        system_context = f"""
{self.personality.system_prompt}

CURRENT STATUS:
- User tier: {self.tier_manager.tier.value}
- Generations remaining today: {remaining if remaining >= 0 else 'unlimited'}
- Generation available: {can_generate}
- Sample library available: {has_samples}{categories_info}

CAPABILITIES:
- Generate music: [ACTION:GENERATE:description]
- Search samples: [ACTION:SEARCH:query]
- Get category: [ACTION:CATEGORY:kick/snare/hat/808/clap]

Give genuine production advice when asked. Be helpful, not salesy.
"""

        try:
            model = self.DEEPSEEK_MODEL if self.deepseek_api_key else "gpt-4o-mini"

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": message}
                ],
                max_tokens=250,
                temperature=0.8
            )

            reply = response.choices[0].message.content

            # Parse any actions from the response
            action = self._parse_action_from_response(reply)
            if action:
                reply = re.sub(r'\[ACTION:[^\]]+\]', '', reply).strip()
                action_response, action_data = self._execute_action(action)
                if reply:
                    return f"{reply}\n\n{action_response}", action_data
                return action_response, action_data

            return reply, None

        except Exception:
            return self._simple_chat(message)

    def _parse_action_from_response(self, response: str) -> Optional[dict]:
        """Parse action tags from LLM response."""
        match = re.search(r'\[ACTION:(\w+):([^\]]*)\]', response)
        if not match:
            return None

        action_type = match.group(1).lower()
        params = match.group(2)

        if action_type == 'generate':
            return {'action': 'generate', 'prompt': params}
        elif action_type == 'search':
            return {'action': 'search_samples', 'query': params}
        elif action_type == 'category':
            return {'action': 'category_samples', 'category': params}

        return None

    def get_stats(self) -> dict:
        """Get current session stats."""
        return {
            'tier': self.tier_manager.tier.value,
            'can_generate': self.tier_manager.can_generate(),
            'remaining_generations': self.tier_manager.get_remaining_generations(),
            'generations_this_session': self.context.generation_count,
            'sample_library': self.sample_db.is_available(),
        }
