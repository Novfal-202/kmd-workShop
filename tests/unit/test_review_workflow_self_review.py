"""FR-018: a reviewer cannot decide on their own submitted claim."""

from datetime import date
from decimal import Decimal

import pytest

from src.models.expense_claim import ClaimStatus, ExpenseClaim
from src.models.review_decision import ReviewDecisionType
from src.services.policy_engine.errors import SelfReviewError
from src.services.policy_engine.review_workflow import ReviewDecisionInput, apply_review_decision


def test_self_review_is_blocked():
    claim = ExpenseClaim(
        submitter_id="emp1",
        category="Meals",
        amount=Decimal("65.00"),
        expense_date=date(2026, 8, 19),
        status=ClaimStatus.PENDING_REVIEW,
    )
    with pytest.raises(SelfReviewError):
        apply_review_decision(
            claim, ReviewDecisionInput(decision=ReviewDecisionType.APPROVED), reviewer_id="emp1"
        )
    # Claim is left untouched.
    assert claim.status == ClaimStatus.PENDING_REVIEW
    assert claim.review_decisions == []
