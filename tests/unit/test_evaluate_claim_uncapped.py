"""FR-015: uncapped_category routes to manual review instead of defaulting to auto-approve."""

from decimal import Decimal

from src.models.expense_claim import ClaimStatus, ViolationCode
from src.services.policy_engine.evaluate_claim import evaluate_claim
from tests.unit.conftest import make_claim_input, now_utc


def test_category_without_configured_cap_is_flagged_uncapped(rule_set):
    claim = make_claim_input(category="Miscellaneous", amount=Decimal("10.00"))
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.UNCAPPED_CATEGORY for v in result.violations)


def test_unconfigured_category_is_still_flagged_uncapped_regardless_of_casing(rule_set):
    """FR-004: this fix corrects casing mismatches only — it must not fabricate a cap
    for a category that was never configured under any casing."""
    claim = make_claim_input(category="supplies", amount=Decimal("10.00"))
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.UNCAPPED_CATEGORY for v in result.violations)
