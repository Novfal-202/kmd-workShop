"""apply_review_decision — pure transition function (FR-008, FR-009, FR-010, FR-018,
contracts/policy-engine-contract.md).

The FR-019 race guard (first-decision-wins) lives in ClaimRepository.try_transition's
conditional UPDATE; this function only computes the new claim state once the caller has
confirmed the claim is still in an allowed status.
"""

from datetime import UTC, datetime

from src.models.expense_claim import ExpenseClaim
from src.models.review_decision import ReviewDecision, ReviewDecisionType
from src.services.policy_engine.errors import DomainValidationError, SelfReviewError

_DECISION_TO_STATUS = {
    ReviewDecisionType.APPROVED: "approved",
    ReviewDecisionType.REJECTED: "rejected",
    ReviewDecisionType.NEEDS_INFORMATION: "needs_information",
}


class ReviewDecisionInput:
    def __init__(self, decision: ReviewDecisionType, reason: str | None = None):
        self.decision = decision
        self.reason = reason


def apply_review_decision(
    claim: ExpenseClaim, decision: ReviewDecisionInput, reviewer_id: str
) -> ExpenseClaim:
    # FR-018: segregation of duties — a reviewer cannot decide on their own claim.
    if reviewer_id == claim.submitter_id:
        raise SelfReviewError(
            "A reviewer cannot approve, reject, or request info on their own claim"
        )

    # FR-009: rejection requires a non-empty reason.
    if decision.decision == ReviewDecisionType.REJECTED and not (decision.reason or "").strip():
        raise DomainValidationError("A reason is required to reject a claim")

    from src.models.expense_claim import ClaimStatus

    review_decision = ReviewDecision(
        claim_id=claim.id,
        reviewer_id=reviewer_id,
        decision=decision.decision,
        reason=decision.reason,
        decided_at=datetime.now(UTC),
    )

    new_status = ClaimStatus(_DECISION_TO_STATUS[decision.decision])
    return claim.model_copy(
        update={
            "status": new_status,
            "review_decisions": [*claim.review_decisions, review_decision],
        }
    )
