"""spec Edge Cases: late_submission, 90-day window."""

from datetime import UTC, datetime
from decimal import Decimal

from src.models.expense_claim import ClaimStatus, ViolationCode
from src.services.policy_engine.evaluate_claim import evaluate_claim
from tests.unit.conftest import WEEKDAY, make_claim_input


def test_submission_within_window_is_not_flagged(rule_set):
    claim = make_claim_input(category="Meals", amount=Decimal("35.00"), expense_date=WEEKDAY)
    submission_date = datetime(2026, 11, 16, tzinfo=UTC)  # 89 days later
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=submission_date)
    assert all(v.code != ViolationCode.LATE_SUBMISSION for v in result.violations)


def test_submission_past_window_is_flagged(rule_set):
    claim = make_claim_input(category="Meals", amount=Decimal("35.00"), expense_date=WEEKDAY)
    submission_date = datetime(2026, 11, 18, tzinfo=UTC)  # 91 days later
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=submission_date)
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.LATE_SUBMISSION for v in result.violations)
