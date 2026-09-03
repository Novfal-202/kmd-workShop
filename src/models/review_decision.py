"""ReviewDecision Pydantic v2 model (data-model.md).

Invariant (FR-018): reviewer_id != the claim's submitter_id for the claim referenced by
claim_id — enforced by review_workflow.apply_review_decision before this is constructed,
not by this model itself (a value object has no access to the claim it belongs to).
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ReviewDecisionType(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFORMATION = "needs_information"


class ReviewDecision(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    claim_id: uuid.UUID
    reviewer_id: str
    decision: ReviewDecisionType
    reason: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
