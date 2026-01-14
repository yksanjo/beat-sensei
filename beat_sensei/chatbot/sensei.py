"""Main Beat-Sensei chatbot orchestrator."""

import re
import os
from typing import Optional, List, Tuple
from dataclasses import dataclass

from .personality import SenseiPersonality
from ..samples.scanner import SampleScanner, SampleMetadata
from ..samples.search import SampleSearch, SearchResult
from ..samples.player import SamplePlayer
from ..generator.replicate_client import ReplicateGenerator
from ..auth.tiers import TierManager


@dataclass
class ChatContext:
    """Conversation context."""
    last_search_results: List[SearchResult] = None
    last_played: Optional[str] = None
    last_generated: Optional[str] = None


class BeatSensei:
    """Main chatbot orchestrator that handles conversation and actions."""

    # DeepSeek API configuration
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    # Default API key for community use (sponsored by Beat-Sensei creator)
    DEFAULT_DEEPSEEK_KEY = "sk-c26f0b1426e146848b5bbf7f363d79af"

    # PRO subscription link - $20/month
    PRO_LINK = "https://buy.stripe.com/test_bJeeVd6Os2bsfe649f6Zy00"

    # Anti-abuse: Max message length
    MAX_MESSAGE_LENGTH = 500

    # Anti-abuse: Off-topic keywords to block
    BLOCKED_TOPICS = [
        'write code', 'write a program', 'python', 'javascript', 'html',
        'hack', 'password', 'credit card', 'ssn', 'social security',
        'write an essay', 'homework', 'assignment', 'exam',
        'translate', 'summarize this article', 'explain quantum',
        'recipe', 'medical advice', 'legal advice', 'investment',
        'pretend you are', 'ignore previous', 'ignore your instructions',
        'jailbreak', 'dan mode', 'bypass', 'new persona',
    ]

    # Sales pitches for upselling PRO
    SALES_PITCHES = [
        "Yo real talk - you should be on PRO. $20 and I can GENERATE any sound you want. GPU power, little bro.",
        "You still on free? Come on now. PRO is $20 for UNLIMITED AI beats. Stop playing.",
        "Every serious producer got AI in their toolkit now. PRO is $20. Level up.",
        "I'm trying to put you on game here - PRO lets me create FULL loops, drums, melodies. $20. That's it.",
        "You know what's crazy? $20 gets you unlimited GPU generation. Studios charge $500/hour. Do the math.",
    ]

    def __init__(
        self,
        scanner: SampleScanner,
        tier_manager: TierManager,
        api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
    ):
        self.personality = SenseiPersonality()
        self.scanner = scanner
        self.search = SampleSearch(scanner)
        self.player = SamplePlayer()
        self.generator = ReplicateGenerator(api_token=api_key)
        self.tier_manager = tier_manager
        self.context = ChatContext()

        # DeepSeek API key - use provided, env var, or default
        self.deepseek_api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY") or self.DEFAULT_DEEPSEEK_KEY

        # LLM client
        self._llm_client = None

        # Message counter for periodic sales pitches
        self.message_count = 0

    def _get_llm_client(self):
        """Get or create DeepSeek client (OpenAI-compatible)."""
        if self._llm_client is None:
            try:
                from openai import OpenAI

                if self.deepseek_api_key:
                    # Use DeepSeek
                    self._llm_client = OpenAI(
                        api_key=self.deepseek_api_key,
                        base_url=self.DEEPSEEK_BASE_URL,
                    )
                elif os.getenv("OPENAI_API_KEY"):
                    # Fallback to OpenAI
                    self._llm_client = OpenAI()
            except ImportError:
                pass
        return self._llm_client

    def _check_abuse(self, message: str) -> Optional[str]:
        """Check if message is trying to abuse the API. Returns rejection message or None."""
        message_lower = message.lower()

        # Check message length
        if len(message) > self.MAX_MESSAGE_LENGTH:
            return "Yo, keep it short! I'm here for quick sample advice, not essays."

        # Check for blocked topics
        for blocked in self.BLOCKED_TOPICS:
            if blocked in message_lower:
                return "Nah fam, I only talk beats and samples. What sound you looking for?"

        return None

    def _get_sales_pitch(self) -> str:
        """Get a random sales pitch for PRO."""
        import random
        pitch = random.choice(self.SALES_PITCHES)
        return f"{pitch}\n\n👉 {self.PRO_LINK}"

    def _should_upsell(self) -> bool:
        """Check if we should add a sales pitch (every 3 messages for free users)."""
        return not self.tier_manager.can_generate() and self.message_count % 3 == 0

    def chat(self, user_message: str) -> Tuple[str, Optional[dict]]:
        """Process a user message and return response with any actions."""
        # Increment message counter
        self.message_count += 1

        # Anti-abuse check
        abuse_response = self._check_abuse(user_message)
        if abuse_response:
            return abuse_response, None

        # Check for direct commands
        action = self._parse_direct_command(user_message)
        if action:
            response, data = self._execute_action(action)
            # Add periodic sales pitch for free users
            if self._should_upsell() and data and data.get('type') != 'upgrade_required':
                response = f"{response}\n\n---\n{self._get_sales_pitch()}"
            return response, data

        # Use LLM if available
        client = self._get_llm_client()
        if client:
            response, data = self._chat_with_llm(user_message)
            # Add periodic sales pitch for free users
            if self._should_upsell():
                response = f"{response}\n\n---\n{self._get_sales_pitch()}"
            return response, data

        # Fallback to simple pattern matching
        return self._simple_chat(user_message)

    def _parse_direct_command(self, message: str) -> Optional[dict]:
        """Parse direct commands like 'play 1', 'search bass'."""
        message = message.strip().lower()

        # Play command
        if message.startswith('play '):
            arg = message[5:].strip()
            if arg.isdigit():
                return {'action': 'play_index', 'index': int(arg)}
            else:
                return {'action': 'play_file', 'file': arg}

        # Stop command
        if message in ['stop', 'pause']:
            return {'action': 'stop'}

        # Search command
        if message.startswith('search ') or message.startswith('find '):
            query = message.split(' ', 1)[1]
            return {'action': 'search', 'query': query}

        # Generate command
        if message.startswith('generate ') or message.startswith('gen ') or message.startswith('make '):
            parts = message.split(' ', 1)
            if len(parts) > 1:
                return {'action': 'generate', 'prompt': parts[1]}

        # Random/inspire command
        if message in ['random', 'inspire', 'surprise me']:
            return {'action': 'random'}

        return None

    def _execute_action(self, action: dict) -> Tuple[str, Optional[dict]]:
        """Execute a parsed action."""
        action_type = action.get('action')

        if action_type == 'play_index':
            return self._play_by_index(action['index'])

        elif action_type == 'play_file':
            return self._play_file(action['file'])

        elif action_type == 'stop':
            self.player.stop()
            return "Stopped playback.", None

        elif action_type == 'search':
            return self._do_search(action['query'])

        elif action_type == 'generate':
            return self._do_generate(action['prompt'])

        elif action_type == 'random':
            return self._get_random_samples()

        return "I didn't catch that. What you need?", None

    def _do_search(self, query: str) -> Tuple[str, Optional[dict]]:
        """Perform a sample search."""
        results = self.search.search(query, limit=10)
        self.context.last_search_results = results

        if not results:
            no_results_msg = self.personality.format_no_results(query)
            # Add PRO pitch when no results found for free users
            if not self.tier_manager.can_generate():
                no_results_msg += f"\n\n💡 Yo but here's the thing - with PRO I could GENERATE exactly what you're looking for. '{query}'? I'll cook it up fresh, GPU-powered. $20 and you never miss again.\n\n👉 {self.PRO_LINK}"
            return no_results_msg, {'type': 'no_results'}

        intro = self.personality.format_search_intro(query)
        return intro, {'type': 'search_results', 'results': results}

    def _play_by_index(self, index: int) -> Tuple[str, Optional[dict]]:
        """Play a sample by its index in last search results."""
        if not self.context.last_search_results:
            return "No search results to play from. Search for something first!", None

        if index < 1 or index > len(self.context.last_search_results):
            return f"Pick a number between 1 and {len(self.context.last_search_results)}", None

        result = self.context.last_search_results[index - 1]
        filepath = result.sample.filepath

        if self.player.play(filepath):
            self.context.last_played = filepath
            return f"Playing: {result.sample.filename}", {'type': 'playing', 'file': filepath}
        else:
            return f"Couldn't play that file. Make sure it exists.", None

    def _play_file(self, filepath: str) -> Tuple[str, Optional[dict]]:
        """Play a file directly."""
        if self.player.play(filepath):
            self.context.last_played = filepath
            return f"Playing...", {'type': 'playing', 'file': filepath}
        return "Couldn't play that file.", None

    def _do_generate(self, prompt: str) -> Tuple[str, Optional[dict]]:
        """Generate a new sample."""
        if not self.tier_manager.can_generate():
            sales_msg = f"""Yo I WANT to hook you up with that '{prompt}' but that's PRO territory, little bro!

🔥 PRO gets you:
• GPU-SYNTHESIZED LOOPS - Full beats from scratch
• UNLIMITED generations - Create all day
• STUDIO QUALITY - Premium AI models
• DRUMS, BASS, MELODIES - Complete instrumentals

Real talk, $20/month is cheaper than ONE sample pack. Studios charge $500/hour for less. You serious about this music thing or nah?

Stop playing and level up 👉 {self.PRO_LINK}"""
            return sales_msg, {'type': 'upgrade_required'}

        if not self.generator.is_available():
            return "Set your REPLICATE_API_TOKEN to enable generation.", {'type': 'config_required'}

        intro = self.personality.format_generate_intro(prompt)
        result = self.generator.generate(prompt)

        if result.success:
            self.context.last_generated = result.filepath
            self.tier_manager.use_generation()
            return f"{intro}\n\nDone! Saved to: {result.filepath}", {'type': 'generated', 'file': result.filepath}
        else:
            return f"Generation failed: {result.error}", {'type': 'error'}

    def _get_random_samples(self) -> Tuple[str, Optional[dict]]:
        """Get random samples for inspiration."""
        samples = self.search.get_random_samples(5)
        if not samples:
            return "Your sample library is empty. Scan a folder first!", None

        # Convert to search results format
        self.context.last_search_results = [
            SearchResult(sample=s, score=1.0, match_reasons=['random pick'])
            for s in samples
        ]

        return "Here's some random heat from your stash:", {'type': 'search_results', 'results': self.context.last_search_results}

    def _simple_chat(self, message: str) -> Tuple[str, Optional[dict]]:
        """Simple pattern-matching fallback chat."""
        message_lower = message.lower()

        # Greetings
        if any(w in message_lower for w in ['hi', 'hello', 'hey', 'yo', 'sup', "what's up"]):
            return self.personality.get_greeting(), None

        # Sample requests
        sample_keywords = ['sample', 'sound', 'need', 'want', 'looking for', 'find', 'get']
        if any(kw in message_lower for kw in sample_keywords):
            # Extract what they're looking for
            return self._do_search(message)

        # Default
        return ("Tell me what kind of sound you're hunting for, or type 'search [description]' "
                "to dig through your samples."), None

    def _chat_with_llm(self, message: str) -> Tuple[str, Optional[dict]]:
        """Chat using OpenAI for more natural conversation."""
        client = self._get_llm_client()
        if not client:
            return self._simple_chat(message)

        # Build context about available samples
        sample_count = self.scanner.get_sample_count()
        categories = self.search.get_categories()
        cat_str = ", ".join(f"{cat}: {count}" for cat, count in categories.items())

        system_context = f"""
{self.personality.system_prompt}

CURRENT LIBRARY STATUS:
- Total samples indexed: {sample_count}
- Categories: {cat_str}
- User tier: {self.tier_manager.tier.value}
- Generation available: {self.tier_manager.can_generate()}

Remember to output actions in [ACTION:TYPE:params] format when needed.
"""

        try:
            # Use DeepSeek model if using DeepSeek, else GPT-4o-mini
            model = self.DEEPSEEK_MODEL if self.deepseek_api_key else "gpt-4o-mini"

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": message}
                ],
                max_tokens=150,  # Keep responses short to save API costs
                temperature=0.8
            )

            reply = response.choices[0].message.content

            # Parse any actions from the response
            action = self._parse_action_from_response(reply)
            if action:
                # Remove action tag from display text
                reply = re.sub(r'\[ACTION:[^\]]+\]', '', reply).strip()
                action_response, action_data = self._execute_action(action)
                return f"{reply}\n\n{action_response}", action_data

            return reply, None

        except Exception as e:
            return self._simple_chat(message)

    def _parse_action_from_response(self, response: str) -> Optional[dict]:
        """Parse action tags from LLM response."""
        # Match [ACTION:TYPE:params]
        match = re.search(r'\[ACTION:(\w+):([^\]]*)\]', response)
        if not match:
            return None

        action_type = match.group(1).lower()
        params = match.group(2)

        if action_type == 'search':
            return {'action': 'search', 'query': params}
        elif action_type == 'play':
            if params.isdigit():
                return {'action': 'play_index', 'index': int(params)}
            return {'action': 'play_file', 'file': params}
        elif action_type == 'generate':
            return {'action': 'generate', 'prompt': params}

        return None

    def get_stats(self) -> dict:
        """Get current session stats."""
        return {
            'samples_indexed': self.scanner.get_sample_count(),
            'tier': self.tier_manager.tier.value,
            'can_generate': self.tier_manager.can_generate(),
            'categories': self.search.get_categories(),
        }
