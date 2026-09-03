"""FR-009: rejection requires a non-empty reason."""

from datetime import date
from decimal import Decimal

import pytest

from src.models.expense_claim import ClaimStatus, ExpenseClaim
from src.models.review_decision import ReviewDecisionType
from src.services.policy_engine.errors import DomainValidationError
from src.services.policy_engine.review_workflow import ReviewDecisionInput, apply_review_decision


def _flagged_claim() -> ExpenseClaim:
    return ExpenseClaim(
        submitter_id="emp1",
        category="Meals",
        amount=Decimal("65.00"),
        expense_date=date(2026, 8, 19),
        status=ClaimStatus.PENDING_REVIEW,
    )


def test_reject_without_reason_raises():
    with pytest.raises(DomainValidationError):
        apply_review_decision(
            _flagged_claim(),
            ReviewDecisionInput(decision=ReviewDecisionType.REJECTED),
            reviewer_id="reviewer1",
        )


def test_reject_with_blank_reason_raises():
    with pytest.raises(DomainValidationError):
        apply_review_decision(
            _flagged_claim(),
            ReviewDecisionInput(decision=ReviewDecisionType.REJECTED, reason="   "),
            reviewer_id="reviewer1",
        )
