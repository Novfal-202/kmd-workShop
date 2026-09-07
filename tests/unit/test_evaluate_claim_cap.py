"""FR-002: over_category_cap."""

from decimal import Decimal

import pytest

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


def test_differently_cased_category_within_cap_has_no_cap_violation(rule_set):
    claim = make_claim_input(category="meals", amount=Decimal("50.00"))
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert all(v.code != ViolationCode.OVER_CATEGORY_CAP for v in result.violations)
    assert all(v.code != ViolationCode.UNCAPPED_CATEGORY for v in result.violations)


def test_differently_cased_category_over_cap_flags_violation(rule_set):
    claim = make_claim_input(category="MEALS", amount=Decimal("65.00"), receipt_attached=True)
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.OVER_CATEGORY_CAP for v in result.violations)
    assert all(v.code != ViolationCode.UNCAPPED_CATEGORY for v in result.violations)


@pytest.mark.parametrize(
    ("category", "cap"),
    [
        ("Lodging", Decimal("300.00")),
        ("Supplies", Decimal("100.00")),
        ("Entertainment", Decimal("150.00")),
    ],
)
def test_newly_covered_category_within_cap_has_no_cap_or_uncapped_violation(
    rule_set, category, cap
):
    """005-category-cap-coverage FR-001/FR-002: a portal-offered category that previously had
    no configured cap now evaluates against a real cap instead of always being flagged uncapped."""
    claim = make_claim_input(category=category, amount=cap, receipt_attached=True)
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert all(v.code != ViolationCode.OVER_CATEGORY_CAP for v in result.violations)
    assert all(v.code != ViolationCode.UNCAPPED_CATEGORY for v in result.violations)


@pytest.mark.parametrize(
    ("category", "over_cap_amount", "cap"),
    [
        ("Lodging", Decimal("350.00"), Decimal("300.00")),
        ("Supplies", Decimal("150.00"), Decimal("100.00")),
        ("Entertainment", Decimal("200.00"), Decimal("150.00")),
    ],
)
def test_newly_covered_category_over_cap_flags_over_cap_not_uncapped(
    rule_set, category, over_cap_amount, cap
):
    """005-category-cap-coverage FR-003: over-cap claims in a newly-covered category get the
    specific over-cap reason, not a generic 'no cap configured' message."""
    claim = make_claim_input(category=category, amount=over_cap_amount, receipt_attached=True)
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.OVER_CATEGORY_CAP for v in result.violations)
    assert all(v.code != ViolationCode.UNCAPPED_CATEGORY for v in result.violations)
