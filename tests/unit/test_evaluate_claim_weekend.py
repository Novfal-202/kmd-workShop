"""FR-004: weekend_policy_violation, including exempt categories."""

from decimal import Decimal

from src.models.expense_claim import ClaimStatus, ViolationCode
from src.services.policy_engine.evaluate_claim import evaluate_claim
from tests.unit.conftest import SATURDAY, SUNDAY, make_claim_input, now_utc


def test_weekday_expense_not_flagged(rule_set):
    claim = make_claim_input(category="Equipment", amount=Decimal("80.00"))
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert all(v.code != ViolationCode.WEEKEND_POLICY_VIOLATION for v in result.violations)


def test_saturday_expense_in_non_exempt_category_is_flagged(rule_set):
    claim = make_claim_input(
        category="Equipment", amount=Decimal("80.00"), expense_date=SATURDAY, receipt_attached=True
    )
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.WEEKEND_POLICY_VIOLATION for v in result.violations)


def test_sunday_expense_in_exempt_category_is_not_flagged(rule_set):
    claim = make_claim_input(
        category="Travel", amount=Decimal("80.00"), expense_date=SUNDAY, receipt_attached=True
    )
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert all(v.code != ViolationCode.WEEKEND_POLICY_VIOLATION for v in result.violations)
