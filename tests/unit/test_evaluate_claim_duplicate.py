"""FR-013: possible_duplicate."""

from datetime import date
from decimal import Decimal

from src.models.expense_claim import ClaimStatus, ExpenseClaim, ViolationCode
from src.services.policy_engine.evaluate_claim import evaluate_claim
from tests.unit.conftest import WEEKDAY, make_claim_input, now_utc


def _prior_claim(**overrides) -> ExpenseClaim:
    defaults = dict(
        submitter_id="emp1",
        category="Meals",
        amount=Decimal("35.00"),
        expense_date=WEEKDAY,
        status=ClaimStatus.AUTO_APPROVED,
    )
    defaults.update(overrides)
    return ExpenseClaim(**defaults)


def test_no_prior_claims_is_not_a_duplicate(rule_set):
    claim = make_claim_input(category="Meals", amount=Decimal("35.00"))
    result = evaluate_claim(claim, rule_set, prior_claims=[], submission_date=now_utc())
    assert all(v.code != ViolationCode.POSSIBLE_DUPLICATE for v in result.violations)


def test_matching_prior_claim_is_flagged_as_duplicate(rule_set):
    claim = make_claim_input(category="Meals", amount=Decimal("35.00"))
    result = evaluate_claim(
        claim, rule_set, prior_claims=[_prior_claim()], submission_date=now_utc()
    )
    assert result.status == ClaimStatus.PENDING_REVIEW
    assert any(v.code == ViolationCode.POSSIBLE_DUPLICATE for v in result.violations)


def test_different_expense_date_is_not_a_duplicate(rule_set):
    claim = make_claim_input(
        category="Meals", amount=Decimal("35.00"), expense_date=date(2026, 8, 20)
    )
    result = evaluate_claim(
        claim, rule_set, prior_claims=[_prior_claim()], submission_date=now_utc()
    )
    assert all(v.code != ViolationCode.POSSIBLE_DUPLICATE for v in result.violations)
