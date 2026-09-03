"""FR-020: withdraw_claim transition and its FR-019 race guard."""

from datetime import date
from decimal import Decimal

import pytest

from src.models.expense_claim import DECIDABLE_STATUSES, ClaimStatus, ExpenseClaim
from src.models.review_decision import ReviewDecisionType
from src.repositories.claim_repository import ClaimRepository
from src.repositories.db import build_engine
from src.services.policy_engine.errors import DomainValidationError
from src.services.policy_engine.review_workflow import ReviewDecisionInput, apply_review_decision
from src.services.policy_engine.withdrawal import withdraw_claim


def _flagged_claim() -> ExpenseClaim:
    return ExpenseClaim(
        submitter_id="emp1",
        category="Meals",
        amount=Decimal("65.00"),
        expense_date=date(2026, 8, 19),
        status=ClaimStatus.PENDING_REVIEW,
    )


def test_withdraw_sets_status_withdrawn():
    claim = _flagged_claim()
    updated = withdraw_claim(claim, requester_id="emp1")
    assert updated.status == ClaimStatus.WITHDRAWN


def test_withdraw_by_non_submitter_raises():
    claim = _flagged_claim()
    with pytest.raises(DomainValidationError):
        withdraw_claim(claim, requester_id="someone-else")


def test_withdraw_race_against_reviewer_decision_via_repository():
    repo = ClaimRepository(build_engine("sqlite:///:memory:"))
    claim = _flagged_claim()
    repo.create(claim)

    decided = repo.try_transition(
        claim.id,
        DECIDABLE_STATUSES,
        mutation=lambda c: apply_review_decision(
            c, ReviewDecisionInput(decision=ReviewDecisionType.APPROVED), reviewer_id="reviewer1"
        ),
    )
    assert decided is not None
    assert decided.status == ClaimStatus.APPROVED

    withdraw_attempt = repo.try_transition(
        claim.id, DECIDABLE_STATUSES, mutation=lambda c: withdraw_claim(c, requester_id="emp1")
    )
    assert withdraw_attempt is None
