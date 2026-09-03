"""withdraw_claim — pure transition function (FR-020, contracts/policy-engine-contract.md).

The actual FR-019 race guard (against a concurrent reviewer decision) lives in
ClaimRepository.try_transition's conditional UPDATE; this function only computes the new
claim state once the caller has confirmed the claim is still in an allowed status.
"""

from src.models.expense_claim import ClaimStatus, ExpenseClaim
from src.services.policy_engine.errors import DomainValidationError


def withdraw_claim(claim: ExpenseClaim, requester_id: str) -> ExpenseClaim:
    if requester_id != claim.submitter_id:
        raise DomainValidationError("Only the submitting employee may withdraw their own claim")

    return claim.model_copy(update={"status": ClaimStatus.WITHDRAWN})
