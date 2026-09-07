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
    """FR-004 (003-case-insensitive-categories): this fix corrects casing mismatches only —
    it must not fabricate a cap for a category that was never configured under any casing."""
    claim = make_claim_input(category="miscellaneous", amount=Decimal("10.00"))
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.UNCAPPED_CATEGORY for v in result.violations)


def test_category_outside_portal_offered_list_is_still_flagged_uncapped(rule_set):
    """FR-005 (005-category-cap-coverage): this feature only guarantees cap coverage for
    the portal's own offered category list (Meals/Travel/Lodging/Supplies/Entertainment) —
    a category outside that list (e.g. one only reachable via direct API use) remains
    correctly uncapped."""
    claim = make_claim_input(category="Consulting", amount=Decimal("10.00"))
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.UNCAPPED_CATEGORY for v in result.violations)
