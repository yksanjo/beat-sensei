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
    generations_per_day: int  # Daily limit for Soundraw
    can_use_premium_models: bool  # Eleven Labs, etc (future)
    can_analyze_audio: bool
    can_export: bool
    priority_support: bool
    extended_duration: bool  # Longer track generation


TIER_LIMITS = {
    Tier.FREE: TierLimits(
        can_generate=True,  # Free tier now gets Soundraw!
        generations_per_day=5,  # 5 per day on free
        can_use_premium_models=False,
        can_analyze_audio=True,
        can_export=True,
        priority_support=False,
        extended_duration=False,  # 30 sec max
    ),
    Tier.PRO: TierLimits(
        can_generate=True,
        generations_per_day=50,  # 50 per day
        can_use_premium_models=True,  # Eleven Labs access
        can_analyze_audio=True,
        can_export=True,
        priority_support=True,
        extended_duration=True,  # Up to 5 min
    ),
    Tier.ENTERPRISE: TierLimits(
        can_generate=True,
        generations_per_day=-1,  # Unlimited
        can_use_premium_models=True,
        can_analyze_audio=True,
        can_export=True,
        priority_support=True,
        extended_duration=True,
    ),
}


class TierManager:
    """Manage user tier and license validation."""

    def __init__(self, config_path: Optional[str] = None):
        self._tier = Tier.FREE
        self._license_key: Optional[str] = None
        self._generations_used_today = 0
        self._last_generation_date: Optional[str] = None

    @property
    def tier(self) -> Tier:
        """Get current tier."""
        return self._tier

    @property
    def limits(self) -> TierLimits:
        """Get limits for current tier."""
        return TIER_LIMITS[self._tier]

    def _reset_daily_count_if_needed(self):
        """Reset generation count if it's a new day."""
        from datetime import date
        today = date.today().isoformat()
        if self._last_generation_date != today:
            self._generations_used_today = 0
            self._last_generation_date = today

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
        self._reset_daily_count_if_needed()
        if not self.limits.can_generate:
            return False
        if self.limits.generations_per_day == -1:
            return True
        return self._generations_used_today < self.limits.generations_per_day

    def can_use_premium_models(self) -> bool:
        """Check if user can use premium AI models (Eleven Labs, etc)."""
        return self.limits.can_use_premium_models

    def get_max_duration(self) -> int:
        """Get maximum track duration in seconds based on tier."""
        if self.limits.extended_duration:
            return 300  # 5 minutes for pro/enterprise
        return 30  # 30 seconds for free

    def use_generation(self) -> bool:
        """Use one generation credit."""
        self._reset_daily_count_if_needed()
        if not self.can_generate():
            return False
        self._generations_used_today += 1
        return True

    def get_remaining_generations(self) -> int:
        """Get remaining generations today."""
        self._reset_daily_count_if_needed()
        if self.limits.generations_per_day == -1:
            return -1  # Unlimited
        return max(0, self.limits.generations_per_day - self._generations_used_today)

    def get_tier_display(self) -> str:
        """Get display string for current tier."""
        remaining = self.get_remaining_generations()
        if self._tier == Tier.FREE:
            return f"Free ({remaining} generations left today)"
        elif self._tier == Tier.PRO:
            if remaining == -1:
                return "Pro (Unlimited)"
            return f"Pro ({remaining} generations left today)"
        else:
            return "Enterprise (Unlimited)"

    def check_soundraw_token(self) -> bool:
        """Check if Soundraw API token is set."""
        return bool(os.getenv("SOUNDRAW_API_TOKEN"))
