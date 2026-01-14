"""Search engine for audio samples."""

from typing import List, Optional
from dataclasses import dataclass
from .scanner import SampleMetadata, SampleScanner


@dataclass
class SearchResult:
    """A search result with relevance score."""
    sample: SampleMetadata
    score: float
    match_reasons: List[str]


class SampleSearch:
    """Search engine for finding samples by description."""

    def __init__(self, scanner: SampleScanner):
        self.scanner = scanner

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        bpm_range: Optional[tuple] = None,
        key: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search for samples matching the query."""
        results = []
        query_terms = query.lower().split()

        for sample in self.scanner.get_all_samples():
            score, reasons = self._score_sample(sample, query_terms, category, bpm_range, key)
            if score > 0:
                results.append(SearchResult(sample=sample, score=score, match_reasons=reasons))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def _score_sample(
        self,
        sample: SampleMetadata,
        query_terms: List[str],
        category: Optional[str],
        bpm_range: Optional[tuple],
        key: Optional[str]
    ) -> tuple:
        """Score how well a sample matches the search criteria."""
        score = 0.0
        reasons = []

        # Text matching
        searchable = f"{sample.filename} {' '.join(sample.tags or [])} {sample.category or ''}".lower()

        for term in query_terms:
            if term in searchable:
                score += 1.0
                reasons.append(f"matches '{term}'")
            # Partial matching
            elif any(term in word for word in searchable.split()):
                score += 0.5
                reasons.append(f"partial match '{term}'")

        # Category filter
        if category:
            if sample.category == category:
                score += 2.0
                reasons.append(f"category: {category}")
            else:
                score = 0  # Filter out non-matching categories
                return score, reasons

        # BPM filter
        if bpm_range and sample.bpm:
            min_bpm, max_bpm = bpm_range
            if min_bpm <= sample.bpm <= max_bpm:
                score += 1.5
                reasons.append(f"BPM {sample.bpm} in range")
            else:
                score *= 0.5  # Reduce but don't eliminate

        # Key filter
        if key and sample.key:
            if key.lower() in sample.key.lower():
                score += 1.5
                reasons.append(f"key: {sample.key}")

        return score, reasons

    def search_by_category(self, category: str, limit: int = 20) -> List[SampleMetadata]:
        """Get all samples in a category."""
        results = []
        for sample in self.scanner.get_all_samples():
            if sample.category == category:
                results.append(sample)
        return results[:limit]

    def search_by_bpm(self, target_bpm: float, tolerance: float = 5.0, limit: int = 10) -> List[SampleMetadata]:
        """Find samples near a target BPM."""
        results = []
        for sample in self.scanner.get_all_samples():
            if sample.bpm and abs(sample.bpm - target_bpm) <= tolerance:
                results.append(sample)
        return sorted(results, key=lambda s: abs(s.bpm - target_bpm))[:limit]

    def get_categories(self) -> dict:
        """Get count of samples per category."""
        categories = {}
        for sample in self.scanner.get_all_samples():
            cat = sample.category or 'unknown'
            categories[cat] = categories.get(cat, 0) + 1
        return categories

    def get_random_samples(self, count: int = 5) -> List[SampleMetadata]:
        """Get random samples for inspiration."""
        import random
        samples = self.scanner.get_all_samples()
        return random.sample(samples, min(count, len(samples)))
