"""Main Beat-Sensei chatbot - Your Sample Library Curator."""

import os
from typing import Optional, Tuple, List
from dataclasses import dataclass

from .personality import SenseiPersonality
from ..database.supabase_client import SampleDatabase, Sample


@dataclass
class ChatContext:
    """Conversation context."""
    last_samples: Optional[List[Sample]] = None


class BeatSensei:
    """Main chatbot for sample library recommendations."""

    # DeepSeek API configuration
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    DEFAULT_DEEPSEEK_KEY = "sk-c26f0b1426e146848b5bbf7f363d79af"

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
        supabase_url: Optional[str] = None,
        supabase_anon_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
    ):
        self.personality = SenseiPersonality()
        self.sample_db = SampleDatabase(url=supabase_url, key=supabase_anon_key)
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
                return "I'm all about music samples - what do you want to find?"

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

        # Sample search
        if message_lower.startswith(('samples ', 'sample ', 'find ', 'search ')):
            parts = message.split(' ', 1)
            if len(parts) > 1:
                return {'action': 'search_samples', 'query': parts[1]}

        # Get samples by category
        if message_lower in ['kicks', 'kick', 'snares', 'snare', 'hats', 'hat', '808s', '808', 'claps', 'clap', 'bass', 'percs', 'perc', 'loops', 'loop']:
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

        # Help
        if message_lower in ['help', '?', '/help']:
            return {'action': 'show_help'}

        return None

    def _execute_action(self, action: dict) -> Tuple[str, Optional[dict]]:
        """Execute a parsed action."""
        action_type = action.get('action')

        if action_type == 'search_samples':
            return self._search_samples(action['query'])

        elif action_type == 'category_samples':
            return self._get_category_samples(action['category'])

        elif action_type == 'random_samples':
            return self._get_random_samples()

        elif action_type == 'play_sample':
            return self._play_sample(action['index'])

        elif action_type == 'show_help':
            return self._show_help()

        return "What kind of sound are you looking for?", None

    def _search_samples(self, query: str) -> Tuple[str, Optional[dict]]:
        """Search for samples in the library."""
        if not self.sample_db.is_available():
            return ("Sample library isn't set up yet.\n\n"
                    "To set up your sample library:\n"
                    "1. Create a Supabase project at supabase.com\n"
                    "2. Get your URL and anon key from Project Settings > API\n"
                    "3. Run: export SUPABASE_URL=your_url\n"
                    "4. Run: export SUPABASE_ANON_KEY=your_key"), None

        samples = self.sample_db.search(query, limit=8)

        if not samples:
            return (f"No samples matching '{query}' in the library.\n\n"
                    f"Try browsing categories: kicks, snares, hats, 808s, loops"), None

        self.context.last_samples = samples
        return self._format_sample_list(samples, f"Found samples for '{query}':"), {
            'type': 'samples',
            'samples': samples
        }

    def _get_category_samples(self, category: str) -> Tuple[str, Optional[dict]]:
        """Get samples by category."""
        if not self.sample_db.is_available():
            return ("Sample library isn't set up yet.\n\n"
                    "To set up your sample library:\n"
                    "1. Create a Supabase project at supabase.com\n"
                    "2. Get your URL and anon key from Project Settings > API\n"
                    "3. Run: export SUPABASE_URL=your_url\n"
                    "4. Run: export SUPABASE_ANON_KEY=your_key"), None

        # Map common requests to database categories
        category_map = {
            'loop': 'loop',
            'loops': 'loop',
            '808': '808',
            'bass': 'bass',
            'kick': 'kick',
            'snare': 'snare',
            'hat': 'hat',
            'clap': 'clap',
            'perc': 'perc'
        }
        
        db_category = category_map.get(category, category)
        samples = self.sample_db.get_by_category(db_category, limit=8)

        if not samples:
            return (f"No {category}s found in the library.\n\n"
                    f"Try: kicks, snares, hats, 808s, loops"), None

        self.context.last_samples = samples
        return self._format_sample_list(samples, f"{category.capitalize()}s in library:"), {
            'type': 'samples',
            'samples': samples
        }

    def _get_random_samples(self) -> Tuple[str, Optional[dict]]:
        """Get random samples for inspiration."""
        if not self.sample_db.is_available():
            return ("Sample library isn't set up yet.\n\n"
                    "To set up your sample library:\n"
                    "1. Create a Supabase project at supabase.com\n"
                    "2. Get your URL and anon key from Project Settings > API\n"
                    "3. Run: export SUPABASE_URL=your_url\n"
                    "4. Run: export SUPABASE_ANON_KEY=your_key"), None

        samples = self.sample_db.get_random(limit=6)

        if not samples:
            return ("Library is empty.\n\n"
                    "Upload samples using: python scripts/upload_samples.py /path/to/samples"), None

        self.context.last_samples = samples
        return self._format_sample_list(samples, "Random samples for inspiration:"), {
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
            lines.append(f"{i}. **{sample.name}** ({sample.category})")
            if tags_str:
                lines.append(f"   Tags: {tags_str}")
            if sample.pack_name:
                lines.append(f"   Pack: {sample.pack_name}")
            lines.append("")

        lines.append(f"Type 'play 1' to preview the first sample, or give me another search.")
        return "\n".join(lines)

    def _show_help(self) -> Tuple[str, Optional[dict]]:
        """Show help information."""
        help_text = """**Beat-Sensei Commands:**

**Browse samples:**
- `kicks` / `snares` / `hats` / `808s` / `loops` - Browse by category
- `search <query>` - Search sample library
- `random` - Get random samples for inspiration
- `play <number>` - Preview a sample

**Tips:**
- Be specific: "dark trap kicks", "jazzy loops", "aggressive 808s"
- Use tags: Samples are tagged by mood, genre, and style
- All samples are production-ready WAV files

**Setup:**
1. Create Supabase project at supabase.com
2. Set environment variables:
   export SUPABASE_URL=your_url
   export SUPABASE_ANON_KEY=your_key
3. Upload samples: python scripts/upload_samples.py /path/to/samples

**Ready to find your sound?**"""
        
        return help_text, {'type': 'help'}

    def _chat_with_llm(self, message: str) -> Tuple[str, Optional[dict]]:
        """Use LLM for natural language conversation."""
        try:
            client = self._get_llm_client()
            if not client:
                return self._simple_chat(message)

            response = client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": self.personality.system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=150
            )

            llm_response = response.choices[0].message.content.strip()
            
            # Check if the LLM response suggests searching for samples
            if any(keyword in llm_response.lower() for keyword in ['search', 'find', 'look for', 'try', 'check out']):
                # Extract potential search terms from the response
                # Simple heuristic: look for music-related terms
                music_terms = ['kick', 'snare', 'hat', '808', 'loop', 'bass', 'perc', 
                              'dark', 'trap', 'drill', 'r&b', 'lo-fi', 'aggressive', 'chill']
                
                for term in music_terms:
                    if term in message.lower():
                        return self._search_samples(term)
            
            return llm_response, None

        except Exception:
            return self._simple_chat(message)

    def _simple_chat(self, message: str) -> Tuple[str, Optional[dict]]:
        """Simple pattern-matching fallback."""
        message_lower = message.lower()

        # Greetings
        if any(w in message_lower for w in ['hi', 'hello', 'hey', 'yo', 'sup', "what's up"]):
            return self.personality.get_greeting(), None

        # Looking for sounds
        sound_keywords = ['sound', 'sample', 'kick', 'snare', 'hat', '808', 'loop', 'bass', 'drum', 'beat']
        if any(kw in message_lower for kw in sound_keywords):
            # Try to extract what they're looking for
            for term in sound_keywords:
                if term in message_lower:
                    return self._search_samples(term)
            
            return "What kind of sound are you looking for? Try 'kicks', 'loops', or 'search dark trap'", None

        # Default response
        return "Tell me what kind of sound you need, and I'll find it in the library. Try 'kicks' or 'search [your style]'", None

    def get_stats(self) -> dict:
        """Get statistics about the sample library."""
        stats = {
            'sample_db_available': self.sample_db.is_available(),
            'llm_available': self._get_llm_client() is not None,
        }
        
        if self.sample_db.is_available():
            categories = self.sample_db.get_categories()
            stats['categories'] = categories
            stats['total_samples'] = sum(categories.values())
        
        return stats