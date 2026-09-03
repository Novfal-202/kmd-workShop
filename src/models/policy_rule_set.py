"""PolicyRuleSet Pydantic v2 model — configurable business rules (data-model.md)."""

from decimal import Decimal

from pydantic import BaseModel, Field

DEFAULT_LATE_SUBMISSION_DAYS = 90


class PolicyRuleSet(BaseModel):
    """Configuration entity. Not part of any individual claim; resolved at evaluation time."""

    category_caps: dict[str, Decimal] = Field(default_factory=dict)
    receipt_required_threshold: Decimal
    auto_approval_threshold: Decimal
    weekend_exempt_categories: list[str] = Field(default_factory=list)
    late_submission_days: int = DEFAULT_LATE_SUBMISSION_DAYS
