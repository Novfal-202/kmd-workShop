"""FR-005/FR-006: auto-approval decision rule, including exceeds_auto_approval_threshold."""

from decimal import Decimal

from src.models.expense_claim import ClaimStatus, ViolationCode
from src.services.policy_engine.evaluate_claim import evaluate_claim
from tests.unit.conftest import make_claim_input, now_utc


def test_fully_compliant_low_value_claim_is_auto_approved(rule_set):
    claim = make_claim_input(category="Meals", amount=Decimal("35.00"))
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.AUTO_APPROVED
    assert result.violations == []


def test_amount_at_threshold_inclusive_is_auto_approved(rule_set):
    claim = make_claim_input(category="Equipment", amount=Decimal("200.00"), receipt_attached=True)
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.AUTO_APPROVED


def test_amount_above_threshold_is_pending_review_even_if_otherwise_compliant(rule_set):
    claim = make_claim_input(category="Travel", amount=Decimal("220.00"), receipt_attached=True)
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.EXCEEDS_AUTO_APPROVAL_THRESHOLD for v in result.violations)
