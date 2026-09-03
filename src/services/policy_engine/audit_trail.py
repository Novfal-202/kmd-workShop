"""Audit-entry builder (FR-017). Pure — no I/O; the caller persists the returned entry
via AuditRepository (constitution Article III.1: no storage import here).
"""

import uuid

from src.models.audit_log_entry import AuditLogEntry, EvaluationOutcome
from src.models.expense_claim import ClaimStatus, ViolationReason


def build_audit_entry(
    claim_id: uuid.UUID,
    rules_evaluated: list[str],
    resulting_status: ClaimStatus,
    violations: list[ViolationReason],
) -> AuditLogEntry:
    outcome = (
        EvaluationOutcome.AUTO_APPROVED
        if resulting_status == ClaimStatus.AUTO_APPROVED
        else EvaluationOutcome.PENDING_REVIEW
    )
    return AuditLogEntry(
        claim_id=claim_id,
        rules_evaluated=rules_evaluated,
        outcome=outcome,
        violations=violations,
    )
