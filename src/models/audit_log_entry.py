"""AuditLogEntry Pydantic v2 model — append-only compliance record (data-model.md, FR-017)."""

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.models.expense_claim import ViolationReason


class EvaluationOutcome(StrEnum):
    AUTO_APPROVED = "auto_approved"
    PENDING_REVIEW = "pending_review"


class AuditLogEntry(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    claim_id: uuid.UUID
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    rules_evaluated: list[str] = Field(default_factory=list)
    outcome: EvaluationOutcome
    violations: list[ViolationReason] = Field(default_factory=list)
