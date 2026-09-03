"""FR-019: ClaimRepository.try_transition first-write-wins — a second conditional update on
an already-transitioned claim affects zero rows and returns None.
"""

from datetime import date
from decimal import Decimal

from src.models.expense_claim import DECIDABLE_STATUSES, ClaimStatus, ExpenseClaim
from src.repositories.claim_repository import ClaimRepository
from src.repositories.db import build_engine


def _repo() -> ClaimRepository:
    return ClaimRepository(build_engine("sqlite:///:memory:"))


def _flagged_claim() -> ExpenseClaim:
    return ExpenseClaim(
        submitter_id="emp1",
        category="Meals",
        amount=Decimal("65.00"),
        expense_date=date(2026, 8, 19),
        status=ClaimStatus.PENDING_REVIEW,
    )


def test_first_transition_succeeds_second_fails():
    repo = _repo()
    claim = _flagged_claim()
    repo.create(claim)

    first = repo.try_transition(
        claim.id,
        DECIDABLE_STATUSES,
        mutation=lambda c: c.model_copy(update={"status": ClaimStatus.APPROVED}),
    )
    assert first is not None
    assert first.status == ClaimStatus.APPROVED

    second = repo.try_transition(
        claim.id,
        DECIDABLE_STATUSES,
        mutation=lambda c: c.model_copy(update={"status": ClaimStatus.REJECTED}),
    )
    assert second is None

    persisted = repo.get(claim.id)
    assert persisted.status == ClaimStatus.APPROVED


def test_transition_on_nonexistent_claim_returns_none():
    repo = _repo()
    import uuid

    result = repo.try_transition(
        uuid.uuid4(),
        DECIDABLE_STATUSES,
        mutation=lambda c: c.model_copy(update={"status": ClaimStatus.APPROVED}),
    )
    assert result is None
