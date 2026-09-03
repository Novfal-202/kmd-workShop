"""ExpenseClaim, ExpenseClaimInput, and ViolationReason Pydantic v2 models (data-model.md)."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ClaimStatus(StrEnum):
    AUTO_APPROVED = "auto_approved"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFORMATION = "needs_information"
    WITHDRAWN = "withdrawn"


# Statuses from which a reviewer decision or a withdrawal may transition the claim (FR-019).
DECIDABLE_STATUSES = (ClaimStatus.PENDING_REVIEW, ClaimStatus.NEEDS_INFORMATION)


class ViolationCode(StrEnum):
    OVER_CATEGORY_CAP = "over_category_cap"
    MISSING_REQUIRED_RECEIPT = "missing_required_receipt"
    WEEKEND_POLICY_VIOLATION = "weekend_policy_violation"
    POSSIBLE_DUPLICATE = "possible_duplicate"
    LATE_SUBMISSION = "late_submission"
    UNCAPPED_CATEGORY = "uncapped_category"
    EXCEEDS_AUTO_APPROVAL_THRESHOLD = "exceeds_auto_approval_threshold"


class ViolationReason(BaseModel):
    """Value object: one rule failure (contracts/policy-engine-contract.md)."""

    model_config = ConfigDict(frozen=True)

    code: ViolationCode
    detail: str


class ExpenseClaimInput(BaseModel):
    """Submission/edit payload. Validation boundary enforced before evaluate_claim runs (FR-014)."""

    category: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    description: str = ""
    expense_date: date
    receipt_attached: bool = False


class ExpenseClaim(BaseModel):
    """Persisted expense claim (data-model.md: ExpenseClaim)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    submitter_id: str
    category: str
    amount: Decimal
    description: str = ""
    expense_date: date
    submission_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    receipt_attached: bool = False
    status: ClaimStatus
    violations: list[ViolationReason] = Field(default_factory=list)
    review_decisions: list["ReviewDecision"] = Field(default_factory=list)


from src.models.review_decision import ReviewDecision  # noqa: E402

ExpenseClaim.model_rebuild()
