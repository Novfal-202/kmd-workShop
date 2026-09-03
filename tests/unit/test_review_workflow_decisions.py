"""FR-008, FR-010: apply_review_decision transitions."""

from datetime import date
from decimal import Decimal

from src.models.expense_claim import ClaimStatus, ExpenseClaim
from src.models.review_decision import ReviewDecisionType
from src.services.policy_engine.review_workflow import ReviewDecisionInput, apply_review_decision


def _flagged_claim() -> ExpenseClaim:
    return ExpenseClaim(
        submitter_id="emp1",
        category="Meals",
        amount=Decimal("65.00"),
        expense_date=date(2026, 8, 19),
        status=ClaimStatus.PENDING_REVIEW,
    )


def test_approve_sets_status_and_records_decision():
    claim = _flagged_claim()
    updated = apply_review_decision(
        claim, ReviewDecisionInput(decision=ReviewDecisionType.APPROVED), reviewer_id="reviewer1"
    )
    assert updated.status == ClaimStatus.APPROVED
    assert len(updated.review_decisions) == 1
    assert updated.review_decisions[0].reviewer_id == "reviewer1"


def test_reject_with_reason_sets_status():
    claim = _flagged_claim()
    updated = apply_review_decision(
        claim,
        ReviewDecisionInput(decision=ReviewDecisionType.REJECTED, reason="Missing justification"),
        reviewer_id="reviewer1",
    )
    assert updated.status == ClaimStatus.REJECTED
    assert updated.review_decisions[0].reason == "Missing justification"


def test_needs_information_sets_status():
    claim = _flagged_claim()
    updated = apply_review_decision(
        claim,
        ReviewDecisionInput(decision=ReviewDecisionType.NEEDS_INFORMATION),
        reviewer_id="reviewer1",
    )
    assert updated.status == ClaimStatus.NEEDS_INFORMATION
