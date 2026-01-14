"""Tier management for Beat-Sensei free/pro features."""

from enum import Enum
from typing import Optional
from dataclasses import dataclass
import os


class Tier(Enum):
    """User subscription tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class TierLimits:
    """Limits for each tier."""
    can_generate: bool
    generations_per_month: int
    can_analyze_audio: bool
    can_export: bool
    priority_support: bool


TIER_LIMITS = {
    Tier.FREE: TierLimits(
        can_generate=False,
        generations_per_month=0,
        can_analyze_audio=True,
        can_export=True,
        priority_support=False,
    ),
    Tier.PRO: TierLimits(
        can_generate=True,
        generations_per_month=100,
        can_analyze_audio=True,
        can_export=True,
        priority_support=True,
    ),
    Tier.ENTERPRISE: TierLimits(
        can_generate=True,
        generations_per_month=-1,  # Unlimited
        can_analyze_audio=True,
        can_export=True,
        priority_support=True,
    ),
}


class TierManager:
    """Manage user tier and license validation."""

    def __init__(self, config_path: Optional[str] = None):
        self._tier = Tier.FREE
        self._license_key: Optional[str] = None
        self._generations_used = 0

    @property
    def tier(self) -> Tier:
        """Get current tier."""
        return self._tier

    @property
    def limits(self) -> TierLimits:
        """Get limits for current tier."""
        return TIER_LIMITS[self._tier]

    def activate_license(self, license_key: str) -> bool:
        """Activate a license key."""
        # Simple validation - in production this would call an API
        if license_key.startswith("BEAT-PRO-"):
            self._tier = Tier.PRO
            self._license_key = license_key
            return True
        elif license_key.startswith("BEAT-ENT-"):
            self._tier = Tier.ENTERPRISE
            self._license_key = license_key
            return True
        return False

    def can_generate(self) -> bool:
        """Check if user can generate samples."""
        if not self.limits.can_generate:
            return False
        if self.limits.generations_per_month == -1:
            return True
        return self._generations_used < self.limits.generations_per_month

    def use_generation(self) -> bool:
        """Use one generation credit."""
        if not self.can_generate():
            return False
        self._generations_used += 1
        return True

    def get_remaining_generations(self) -> int:
        """Get remaining generations this month."""
        if self.limits.generations_per_month == -1:
            return -1  # Unlimited
        return max(0, self.limits.generations_per_month - self._generations_used)

    def get_tier_display(self) -> str:
        """Get display string for current tier."""
        if self._tier == Tier.FREE:
            return "Free (Search & Preview)"
        elif self._tier == Tier.PRO:
            remaining = self.get_remaining_generations()
            return f"Pro ({remaining} generations left)"
        else:
            return "Enterprise (Unlimited)"

    def check_replicate_token(self) -> bool:
        """Check if Replicate API token is set."""
        return bool(os.getenv("REPLICATE_API_TOKEN"))
