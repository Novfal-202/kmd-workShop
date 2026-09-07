"""PolicyRuleSet Pydantic v2 model — configurable business rules (data-model.md)."""

from decimal import Decimal

from pydantic import BaseModel, Field

DEFAULT_LATE_SUBMISSION_DAYS = 90


def _normalize_category(value: str) -> str:
    """Single source of truth for the case-insensitive category-matching rule
    (research.md §1-2, specs/003-case-insensitive-categories). Every category-keyed
    lookup on PolicyRuleSet must compare through this helper, never a raw dict/list
    membership check, so the casing rule only needs to change in one place.
    """
    return value.casefold()


class PolicyRuleSet(BaseModel):
    """Configuration entity. Not part of any individual claim; resolved at evaluation time."""

    category_caps: dict[str, Decimal] = Field(default_factory=dict)
    receipt_required_threshold: Decimal
    auto_approval_threshold: Decimal
    weekend_exempt_categories: list[str] = Field(default_factory=list)
    late_submission_days: int = DEFAULT_LATE_SUBMISSION_DAYS

    def get_category_cap(self, category: str) -> Decimal | None:
        """Case-insensitive replacement for `category_caps.get(category)` (FR-001)."""
        normalized = _normalize_category(category)
        for configured_category, cap in self.category_caps.items():
            if _normalize_category(configured_category) == normalized:
                return cap
        return None

    def is_weekend_exempt(self, category: str) -> bool:
        """Case-insensitive replacement for `category in weekend_exempt_categories` (FR-002)."""
        normalized = _normalize_category(category)
        return any(
            _normalize_category(exempt_category) == normalized
            for exempt_category in self.weekend_exempt_categories
        )
