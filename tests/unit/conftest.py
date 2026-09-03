from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.models.expense_claim import ExpenseClaimInput
from src.models.policy_rule_set import PolicyRuleSet

WEEKDAY = date(2026, 8, 19)  # Wednesday
SATURDAY = date(2026, 8, 22)
SUNDAY = date(2026, 8, 23)


@pytest.fixture
def rule_set() -> PolicyRuleSet:
    return PolicyRuleSet(
        category_caps={
            "Meals": Decimal("50.00"),
            "Travel": Decimal("1000.00"),
            "Equipment": Decimal("500.00"),
        },
        receipt_required_threshold=Decimal("100.00"),
        auto_approval_threshold=Decimal("200.00"),
        weekend_exempt_categories=["Travel", "Lodging"],
        late_submission_days=90,
    )


def make_claim_input(**overrides) -> ExpenseClaimInput:
    defaults = dict(
        category="Meals",
        amount=Decimal("35.00"),
        description="",
        expense_date=WEEKDAY,
        receipt_attached=False,
    )
    defaults.update(overrides)
    return ExpenseClaimInput(**defaults)


def now_utc() -> datetime:
    return datetime(2026, 8, 20, tzinfo=UTC)
