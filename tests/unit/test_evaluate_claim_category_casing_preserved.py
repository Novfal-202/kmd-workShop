"""FR-005: case-insensitive policy matching must not change the category casing
stored on/returned for a claim, or interpolated into violation detail messages —
only the internal comparison used during evaluation is case-insensitive."""

from decimal import Decimal

from src.models.expense_claim import ViolationCode
from src.services.policy_engine.evaluate_claim import evaluate_claim
from tests.unit.conftest import make_claim_input, now_utc


def test_claim_category_casing_is_unchanged_by_evaluation(rule_set):
    claim = make_claim_input(category="mEaLs", amount=Decimal("10.00"))
    evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert claim.category == "mEaLs"


def test_over_cap_violation_detail_echoes_original_submitted_casing(rule_set):
    claim = make_claim_input(category="MEALS", amount=Decimal("65.00"), receipt_attached=True)
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    violation = next(v for v in result.violations if v.code == ViolationCode.OVER_CATEGORY_CAP)
    assert "MEALS" in violation.detail
    assert "Meals" not in violation.detail
