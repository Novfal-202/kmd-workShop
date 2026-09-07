"""Claims routes — thin transport layer (constitution Article III.1): (de)serialization and
delegation to the policy engine + repositories only. No business rules live here.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter

from src.logging_config import log_event
from src.models.expense_claim import (
    DECIDABLE_STATUSES,
    ExpenseClaim,
    ExpenseClaimInput,
)
from src.repositories.audit_repository import AuditRepository
from src.repositories.claim_repository import ClaimRepository
from src.repositories.policy_rule_set_repository import PolicyRuleSetRepository
from src.services.policy_engine.audit_trail import build_audit_entry
from src.services.policy_engine.errors import AlreadyDecidedError, NotFoundError
from src.services.policy_engine.evaluate_claim import evaluate_claim
from src.services.policy_engine.withdrawal import withdraw_claim

router = APIRouter()

claim_repository = ClaimRepository()
audit_repository = AuditRepository()
policy_rule_set_repository = PolicyRuleSetRepository()

# Placeholder for the identity system this feature assumes exists (spec Assumptions).
CURRENT_EMPLOYEE_ID = "current-employee"


def _evaluate_and_persist(claim_input: ExpenseClaimInput, submitter_id: str) -> ExpenseClaim:
    now = datetime.now(UTC)
    prior_claims = claim_repository.list_by_employee(submitter_id)
    rule_set = policy_rule_set_repository.get_active_rule_set()
    result = evaluate_claim(claim_input, rule_set, prior_claims, submission_date=now)

    claim = ExpenseClaim(
        submitter_id=submitter_id,
        category=claim_input.category,
        amount=claim_input.amount,
        description=claim_input.description,
        expense_date=claim_input.expense_date,
        submission_date=now,
        receipt_attached=claim_input.receipt_attached,
        employee_name=claim_input.employee_name,
        status=result.status,
        violations=result.violations,
    )
    claim_repository.create(claim)
    audit_entry = build_audit_entry(
        claim.id, result.rules_evaluated, result.status, result.violations
    )
    audit_repository.append(audit_entry)
    log_event(
        "claim_evaluated",
        claim_id=str(claim.id),
        submitter_id=submitter_id,
        status=result.status.value,
        violation_codes=[v.code.value for v in result.violations],
    )
    return claim


@router.post("/claims", status_code=201)
def submit_claim(payload: ExpenseClaimInput) -> ExpenseClaim:
    return _evaluate_and_persist(payload, CURRENT_EMPLOYEE_ID)


@router.get("/claims")
def list_my_claims() -> list[ExpenseClaim]:
    return claim_repository.list_by_employee(CURRENT_EMPLOYEE_ID)


@router.get("/claims/{claim_id}")
def get_claim(claim_id: uuid.UUID) -> ExpenseClaim:
    claim = claim_repository.get(claim_id)
    if claim is None:
        raise NotFoundError(f"Claim {claim_id} not found")
    return claim


@router.put("/claims/{claim_id}")
def edit_claim(claim_id: uuid.UUID, payload: ExpenseClaimInput) -> ExpenseClaim:
    """FR-016: editing re-triggers the full policy evaluation as if newly submitted."""
    existing = claim_repository.get(claim_id)
    if existing is None:
        raise NotFoundError(f"Claim {claim_id} not found")

    now = datetime.now(UTC)
    prior_claims = [
        c for c in claim_repository.list_by_employee(existing.submitter_id) if c.id != claim_id
    ]
    rule_set = policy_rule_set_repository.get_active_rule_set()
    result = evaluate_claim(payload, rule_set, prior_claims, submission_date=now)

    updated = ExpenseClaim(
        id=existing.id,
        submitter_id=existing.submitter_id,
        category=payload.category,
        amount=payload.amount,
        description=payload.description,
        expense_date=payload.expense_date,
        submission_date=now,
        receipt_attached=payload.receipt_attached,
        employee_name=payload.employee_name or existing.employee_name,
        status=result.status,
        violations=result.violations,
        review_decisions=existing.review_decisions,
    )
    claim_repository.replace(updated)
    audit_entry = build_audit_entry(
        updated.id, result.rules_evaluated, result.status, result.violations
    )
    audit_repository.append(audit_entry)
    log_event(
        "claim_edited_and_reevaluated",
        claim_id=str(updated.id),
        status=result.status.value,
        violation_codes=[v.code.value for v in result.violations],
    )
    return updated


@router.get("/claims/{claim_id}/audit-trail")
def get_audit_trail(claim_id: uuid.UUID):
    if claim_repository.get(claim_id) is None:
        raise NotFoundError(f"Claim {claim_id} not found")
    return audit_repository.list_for_claim(claim_id)


@router.post("/claims/{claim_id}/withdraw")
def withdraw_claim_route(claim_id: uuid.UUID) -> ExpenseClaim:
    claim = claim_repository.get(claim_id)
    if claim is None:
        raise NotFoundError(f"Claim {claim_id} not found")

    result = claim_repository.try_transition(
        claim_id,
        allowed_from_statuses=DECIDABLE_STATUSES,
        mutation=lambda c: withdraw_claim(c, requester_id=CURRENT_EMPLOYEE_ID),
    )
    if result is None:
        raise AlreadyDecidedError(
            "Claim is no longer withdrawable — it already left pending_review/needs_information"
        )
    log_event("claim_withdrawn", claim_id=str(claim_id), submitter_id=CURRENT_EMPLOYEE_ID)
    return result
