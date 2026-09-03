"""Review routes — thin transport layer (constitution Article III.1)."""

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from src.api.claims_routes import claim_repository
from src.logging_config import log_event
from src.models.expense_claim import DECIDABLE_STATUSES, ExpenseClaim
from src.models.review_decision import ReviewDecisionType
from src.services.notifications import default_dispatcher
from src.services.policy_engine.errors import AlreadyDecidedError, NotFoundError
from src.services.policy_engine.review_workflow import ReviewDecisionInput, apply_review_decision

router = APIRouter()


class ReviewDecisionRequest(BaseModel):
    decision: ReviewDecisionType
    reason: str | None = None


# Placeholder for the identity system this feature assumes exists (spec Assumptions).
CURRENT_REVIEWER_ID = "current-reviewer"


@router.get("/review-queue")
def list_review_queue() -> list[ExpenseClaim]:
    return claim_repository.list_review_queue()


@router.post("/claims/{claim_id}/decisions")
def record_decision(claim_id: uuid.UUID, payload: ReviewDecisionRequest) -> ExpenseClaim:
    claim = claim_repository.get(claim_id)
    if claim is None:
        raise NotFoundError(f"Claim {claim_id} not found")

    decision_input = ReviewDecisionInput(decision=payload.decision, reason=payload.reason)

    result = claim_repository.try_transition(
        claim_id,
        allowed_from_statuses=DECIDABLE_STATUSES,
        mutation=lambda c: apply_review_decision(c, decision_input, CURRENT_REVIEWER_ID),
    )
    if result is None:
        raise AlreadyDecidedError(f"Claim {claim_id} has already been decided")

    default_dispatcher.notify_status_change(claim_id, result.submitter_id, result.status.value)
    log_event(
        "review_decision_recorded",
        claim_id=str(claim_id),
        reviewer_id=CURRENT_REVIEWER_ID,
        decision=payload.decision.value,
        resulting_status=result.status.value,
    )
    return result
