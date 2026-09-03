"""FR-003: missing_required_receipt."""

from decimal import Decimal

from src.models.expense_claim import ClaimStatus, ViolationCode
from src.services.policy_engine.evaluate_claim import evaluate_claim
from tests.unit.conftest import make_claim_input, now_utc


def test_below_threshold_no_receipt_required(rule_set):
    claim = make_claim_input(category="Equipment", amount=Decimal("99.99"), receipt_attached=False)
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert all(v.code != ViolationCode.MISSING_REQUIRED_RECEIPT for v in result.violations)


def test_at_threshold_without_receipt_is_flagged(rule_set):
    claim = make_claim_input(category="Equipment", amount=Decimal("100.00"), receipt_attached=False)
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.MISSING_REQUIRED_RECEIPT for v in result.violations)


def test_at_threshold_with_receipt_is_not_flagged(rule_set):
    claim = make_claim_input(category="Equipment", amount=Decimal("100.00"), receipt_attached=True)
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert all(v.code != ViolationCode.MISSING_REQUIRED_RECEIPT for v in result.violations)
