"""Supabase client for Beat-Sensei sample library."""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class Sample:
    """A sample from the database."""
    id: str
    name: str
    category: str  # kick, snare, hat, 808, clap, bass, melody, fx, loop
    pack_name: str
    file_url: str
    tags: List[str]
    bpm: Optional[int] = None
    key: Optional[str] = None
    mood: Optional[str] = None
    duration_ms: Optional[int] = None


class SampleDatabase:
    """Interface to Supabase sample library."""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_ANON_KEY")
        self._client = None

    def _get_client(self):
        """Get or create Supabase client."""
        if self._client is None:
            try:
                from supabase import create_client
                if self.url and self.key:
                    self._client = create_client(self.url, self.key)
            except ImportError:
                pass
        return self._client

    def is_available(self) -> bool:
        """Check if database is configured and available."""
        return self._get_client() is not None

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Sample]:
        """Search samples by query text."""
        client = self._get_client()
        if not client:
            return []

        try:
            # Build query
            q = client.table("samples").select("*")

            # Text search on name and tags
            q = q.or_(f"name.ilike.%{query}%,tags.cs.{{{query}}}")

            # Filter by category if specified
            if category:
                q = q.eq("category", category.lower())

            # Execute
            result = q.limit(limit).execute()

            return [self._row_to_sample(row) for row in result.data]

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def get_by_category(self, category: str, limit: int = 10) -> List[Sample]:
        """Get samples by category."""
        client = self._get_client()
        if not client:
            return []

        try:
            result = (
                client.table("samples")
                .select("*")
                .eq("category", category.lower())
                .limit(limit)
                .execute()
            )
            return [self._row_to_sample(row) for row in result.data]
        except Exception:
            return []

    def get_random(self, limit: int = 5, category: Optional[str] = None) -> List[Sample]:
        """Get random samples for inspiration."""
        client = self._get_client()
        if not client:
            return []

        try:
            q = client.table("samples").select("*")

            if category:
                q = q.eq("category", category.lower())

            # Use random ordering (Supabase/PostgreSQL)
            result = q.order("created_at", desc=True).limit(limit * 3).execute()

            # Shuffle in Python for true randomness
            import random
            samples = [self._row_to_sample(row) for row in result.data]
            random.shuffle(samples)
            return samples[:limit]

        except Exception:
            return []

    def get_by_mood(self, mood: str, limit: int = 10) -> List[Sample]:
        """Get samples by mood tag."""
        client = self._get_client()
        if not client:
            return []

        try:
            result = (
                client.table("samples")
                .select("*")
                .contains("tags", [mood.lower()])
                .limit(limit)
                .execute()
            )
            return [self._row_to_sample(row) for row in result.data]
        except Exception:
            return []

    def recommend_for_prompt(self, prompt: str, limit: int = 5) -> List[Sample]:
        """Recommend samples based on a generation prompt."""
        # Parse the prompt for relevant terms
        prompt_lower = prompt.lower()
        
        # Common drum patterns and their typical components
        drum_patterns = {
            'trap': ['kick', 'snare', 'hat', '808'],
            'drill': ['kick', 'snare', 'hat', '808'],
            'house': ['kick', 'clap', 'hat'],
            'techno': ['kick', 'hat', 'perc'],
            'dubstep': ['kick', 'snare', 'hat', 'bass'],
            'lo-fi': ['kick', 'snare', 'hat', 'perc'],
            'hip hop': ['kick', 'snare', 'hat', '808'],
            'boom bap': ['kick', 'snare', 'hat'],
        }

        # Detect genre from prompt
        detected_genre = None
        for genre, components in drum_patterns.items():
            if genre in prompt_lower:
                detected_genre = genre
                break

        # Category detection with priority
        categories_to_search = []
        
        # Check for specific instrument requests
        if any(w in prompt_lower for w in ['kick', 'kicks']):
            categories_to_search.append('kick')
        if any(w in prompt_lower for w in ['snare', 'snares', 'rim']):
            categories_to_search.append('snare')
        if any(w in prompt_lower for w in ['hat', 'hats', 'hihat', 'hi-hat']):
            categories_to_search.append('hat')
        if any(w in prompt_lower for w in ['808', '808s', 'sub', 'bass']):
            categories_to_search.append('808')
        if any(w in prompt_lower for w in ['clap', 'claps']):
            categories_to_search.append('clap')
        if any(w in prompt_lower for w in ['perc', 'percussion', 'shaker', 'tambourine']):
            categories_to_search.append('perc')
        if any(w in prompt_lower for w in ['melody', 'synth', 'keys', 'piano', 'guitar']):
            categories_to_search.append('melody')
        if any(w in prompt_lower for w in ['fx', 'effect', 'riser', 'impact']):
            categories_to_search.append('fx')

        # If no specific categories detected but we have a genre, use genre components
        if not categories_to_search and detected_genre:
            categories_to_search = drum_patterns[detected_genre]

        # Mood/style keywords
        mood_keywords = []
        mood_mapping = {
            'dark': ['dark', 'evil', 'sinister', 'grim', 'horror'],
            'hard': ['hard', 'aggressive', 'heavy', 'loud', 'distorted'],
            'soft': ['soft', 'gentle', 'mellow', 'smooth', 'warm', 'chill'],
            'trap': ['trap', 'drill', 'plugg'],
            'classic': ['classic', 'vintage', 'old', 'retro', 'boom', 'bap'],
            'crispy': ['crispy', 'crisp', 'clean', 'sharp'],
            'punchy': ['punchy', 'punch', 'knock', 'hit'],
            'acoustic': ['acoustic', 'organic', 'natural', 'live'],
            'electronic': ['electronic', 'synth', 'digital'],
        }
        
        for mood, keywords in mood_mapping.items():
            if any(w in prompt_lower for w in keywords):
                mood_keywords.append(mood)

        # Collect samples from all detected categories
        all_samples = []
        
        if categories_to_search:
            # Get samples from each category
            for category in categories_to_search[:3]:  # Limit to 3 categories
                cat_samples = self.get_by_category(category, limit=limit//2)
                all_samples.extend(cat_samples)
        
        # If we have mood keywords, try to filter or get mood-based samples
        if mood_keywords and len(all_samples) < limit:
            for mood in mood_keywords[:2]:  # Try up to 2 moods
                mood_samples = self.get_by_mood(mood, limit=limit//2)
                all_samples.extend(mood_samples)
        
        # If still not enough samples, do a generic search
        if len(all_samples) < limit:
            generic_samples = self.search(prompt, limit=limit)
            all_samples.extend(generic_samples)
        
        # Remove duplicates by ID
        unique_samples = []
        seen_ids = set()
        for sample in all_samples:
            if sample.id not in seen_ids:
                seen_ids.add(sample.id)
                unique_samples.append(sample)
        
        # Limit results
        return unique_samples[:limit]

    def get_categories(self) -> Dict[str, int]:
        """Get count of samples per category."""
        client = self._get_client()
        if not client:
            return {}

        try:
            result = client.table("samples").select("category").execute()
            counts = {}
            for row in result.data:
                cat = row.get("category", "other")
                counts[cat] = counts.get(cat, 0) + 1
            return counts
        except Exception:
            return {}

    def _row_to_sample(self, row: Dict[str, Any]) -> Sample:
        """Convert database row to Sample object."""
        return Sample(
            id=row.get("id", ""),
            name=row.get("name", ""),
            category=row.get("category", ""),
            pack_name=row.get("pack_name", ""),
            file_url=row.get("file_url", ""),
            tags=row.get("tags", []),
            bpm=row.get("bpm"),
            key=row.get("key"),
            mood=row.get("mood"),
            duration_ms=row.get("duration_ms"),
        )


# SQL Schema for Supabase (run this in Supabase SQL editor)
SCHEMA_SQL = """
-- Samples table
CREATE TABLE IF NOT EXISTS samples (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    pack_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_path TEXT,
    tags TEXT[] DEFAULT '{}',
    bpm INTEGER,
    key TEXT,
    mood TEXT,
    duration_ms INTEGER,
    file_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast search
CREATE INDEX IF NOT EXISTS idx_samples_category ON samples(category);
CREATE INDEX IF NOT EXISTS idx_samples_tags ON samples USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_samples_name ON samples(name);
CREATE INDEX IF NOT EXISTS idx_samples_pack ON samples(pack_name);

-- Enable Row Level Security
ALTER TABLE samples ENABLE ROW LEVEL SECURITY;

-- Allow public read access (samples are public)
CREATE POLICY "Samples are publicly readable"
ON samples FOR SELECT
TO public
USING (true);

-- Storage bucket for audio files
-- Run in Supabase Dashboard > Storage > Create bucket: "samples"
-- Set to public
"""
