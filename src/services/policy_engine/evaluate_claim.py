"""evaluate_claim — pure policy evaluation (contracts/policy-engine-contract.md).

No I/O: `prior_claims` (the submitter's own prior claims) and `submission_date` are passed
in by the caller. Constitution Article III.1: no HTTP/transport or storage imports here.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from src.models.expense_claim import (
    ClaimStatus,
    ExpenseClaim,
    ExpenseClaimInput,
    ViolationCode,
    ViolationReason,
)
from src.models.policy_rule_set import PolicyRuleSet

WEEKEND_ISO_WEEKDAYS = (6, 7)  # Saturday, Sunday (date.isoweekday())


class EvaluationResult(BaseModel):
    status: ClaimStatus
    violations: list[ViolationReason] = Field(default_factory=list)
    rules_evaluated: list[str] = Field(default_factory=list)


def _is_duplicate(claim: ExpenseClaimInput, prior_claims: list[ExpenseClaim]) -> bool:
    return any(
        p.amount == claim.amount
        and p.category == claim.category
        and p.expense_date == claim.expense_date
        for p in prior_claims
    )


def evaluate_claim(
    claim: ExpenseClaimInput,
    rule_set: PolicyRuleSet,
    prior_claims: list[ExpenseClaim],
    submission_date: datetime,
) -> EvaluationResult:
    violations: list[ViolationReason] = []
    rules_evaluated: list[str] = []

    # 1 & 2. over_category_cap / uncapped_category (FR-002, FR-015)
    rules_evaluated.append(ViolationCode.OVER_CATEGORY_CAP.value)
    rules_evaluated.append(ViolationCode.UNCAPPED_CATEGORY.value)
    cap = rule_set.category_caps.get(claim.category)
    if cap is None:
        violations.append(
            ViolationReason(
                code=ViolationCode.UNCAPPED_CATEGORY,
                detail=f"Category '{claim.category}' has no configured spending cap",
            )
        )
    elif claim.amount > cap:
        violations.append(
            ViolationReason(
                code=ViolationCode.OVER_CATEGORY_CAP,
                detail=f"Amount ${claim.amount} exceeds {claim.category} cap of ${cap}",
            )
        )

    # 3. missing_required_receipt (FR-003)
    rules_evaluated.append(ViolationCode.MISSING_REQUIRED_RECEIPT.value)
    if claim.amount >= rule_set.receipt_required_threshold and not claim.receipt_attached:
        violations.append(
            ViolationReason(
                code=ViolationCode.MISSING_REQUIRED_RECEIPT,
                detail=(
                    f"Amount ${claim.amount} is at/above the "
                    f"${rule_set.receipt_required_threshold} receipt-required threshold, "
                    "but no receipt was attached"
                ),
            )
        )

    # 4. weekend_policy_violation (FR-004)
    rules_evaluated.append(ViolationCode.WEEKEND_POLICY_VIOLATION.value)
    if (
        claim.expense_date.isoweekday() in WEEKEND_ISO_WEEKDAYS
        and claim.category not in rule_set.weekend_exempt_categories
    ):
        violations.append(
            ViolationReason(
                code=ViolationCode.WEEKEND_POLICY_VIOLATION,
                detail=(
                    f"Expense dated {claim.expense_date} falls on a weekend "
                    "for a non-exempt category"
                ),
            )
        )

    # 5. possible_duplicate (FR-013)
    rules_evaluated.append(ViolationCode.POSSIBLE_DUPLICATE.value)
    if _is_duplicate(claim, prior_claims):
        violations.append(
            ViolationReason(
                code=ViolationCode.POSSIBLE_DUPLICATE,
                detail=(
                    "A prior claim with the same amount, category, "
                    "and expense date already exists"
                ),
            )
        )

    # 6. late_submission (spec Edge Cases)
    rules_evaluated.append(ViolationCode.LATE_SUBMISSION.value)
    days_since_expense = (submission_date.date() - claim.expense_date).days
    if days_since_expense > rule_set.late_submission_days:
        violations.append(
            ViolationReason(
                code=ViolationCode.LATE_SUBMISSION,
                detail=(
                    f"Submitted {days_since_expense} days after the expense date, "
                    f"exceeding the {rule_set.late_submission_days}-day window"
                ),
            )
        )

    # 7. exceeds_auto_approval_threshold (FR-005, FR-006)
    rules_evaluated.append(ViolationCode.EXCEEDS_AUTO_APPROVAL_THRESHOLD.value)
    if claim.amount > rule_set.auto_approval_threshold:
        violations.append(
            ViolationReason(
                code=ViolationCode.EXCEEDS_AUTO_APPROVAL_THRESHOLD,
                detail=(
                    f"Amount ${claim.amount} exceeds the ${rule_set.auto_approval_threshold} "
                    "auto-approval threshold"
                ),
            )
        )

    status = ClaimStatus.AUTO_APPROVED if not violations else ClaimStatus.PENDING_REVIEW
    return EvaluationResult(status=status, violations=violations, rules_evaluated=rules_evaluated)
