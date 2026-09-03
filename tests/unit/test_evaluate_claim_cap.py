"""FR-002: over_category_cap."""

from decimal import Decimal

from src.models.expense_claim import ClaimStatus, ViolationCode
from src.services.policy_engine.evaluate_claim import evaluate_claim
from tests.unit.conftest import make_claim_input, now_utc


def test_amount_within_cap_has_no_cap_violation(rule_set):
    claim = make_claim_input(category="Meals", amount=Decimal("50.00"))
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert all(v.code != ViolationCode.OVER_CATEGORY_CAP for v in result.violations)


def test_amount_over_cap_flags_violation_and_pending_review(rule_set):
    claim = make_claim_input(category="Meals", amount=Decimal("65.00"), receipt_attached=True)
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.OVER_CATEGORY_CAP for v in result.violations)
