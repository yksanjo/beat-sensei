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

        # DeepSeek API key
        self.deepseek_api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")

        # LLM client
        self._llm_client = None

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

    def chat(self, user_message: str) -> Tuple[str, Optional[dict]]:
        """Process a user message and return response with any actions."""
        # Check for direct commands
        action = self._parse_direct_command(user_message)
        if action:
            return self._execute_action(action)

        # Use LLM if available
        client = self._get_llm_client()
        if client:
            return self._chat_with_llm(user_message)

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
            return self.personality.format_no_results(query), {'type': 'no_results'}

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
            return "Generation is a Pro feature. Upgrade to unlock AI sample creation!", {'type': 'upgrade_required'}

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
                max_tokens=500,
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
