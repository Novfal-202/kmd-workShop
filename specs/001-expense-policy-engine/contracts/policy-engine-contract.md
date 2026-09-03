# Policy Engine Contract (internal library contract)

This is the contract for `src/services/policy_engine/`, the pure business-logic layer required by constitution Article III.1 to remain decoupled from HTTP/API transport. It is called directly by `src/api/` routes, and identically by tests and any future non-HTTP caller (e.g., a batch job or CLI), with no transport-specific types anywhere in its signature.

## `evaluate_claim`

```text
evaluate_claim(claim: ExpenseClaimInput, rule_set: PolicyRuleSet, prior_claims: list[ExpenseClaim]) -> EvaluationResult
```

- **Input**: a not-yet-persisted claim (or an edited claim being re-evaluated per FR-016), the currently configured `PolicyRuleSet`, and the submitter's prior claims (for duplicate/late-submission checks).
- **Output** (`EvaluationResult`): `status` (`auto_approved` | `pending_review`), `violations: list[ViolationReason]`, `audit_entry: AuditLogEntry`.
- **Pure function**: no I/O, no network/HTTP calls, no database writes — `prior_claims` is passed in by the caller (repository lookup happens outside this function), and the caller is responsible for persisting the result and the audit entry.
- **Rule checks performed, each independently, with all failing checks reported together** (spec Edge Cases — compound violations):
  1. `over_category_cap` — FR-002: `claim.amount > rule_set.category_caps[claim.category]`
  2. `uncapped_category` — FR-015: `claim.category not in rule_set.category_caps`
  3. `missing_required_receipt` — FR-003: `claim.amount >= rule_set.receipt_required_threshold and not claim.receipt_attached`
  4. `weekend_policy_violation` — FR-004: `claim.expense_date.weekday() in {5,6} and claim.category not in rule_set.weekend_exempt_categories`
  5. `possible_duplicate` — FR-013: an entry in `prior_claims` with matching `(submitter_id, amount, category, expense_date)`
  6. `late_submission` — spec Edge Cases: `(claim.submission_date - claim.expense_date).days > rule_set.late_submission_days`
  7. `exceeds_auto_approval_threshold` — FR-005/FR-006: `claim.amount > rule_set.auto_approval_threshold` (only relevant when no other violation fired; still prevents auto-approval)
- **Decision rule** (FR-005/FR-006): `status = auto_approved` if and only if zero violations were found from checks 1–7; otherwise `pending_review` with the full violation list attached.

## `apply_review_decision`

```text
apply_review_decision(claim: ExpenseClaim, decision: ReviewDecisionInput, reviewer_id: str) -> ExpenseClaim
```

- **Preconditions**:
  - `claim.status in {pending_review, needs_information}` (FR-008) — the pure function checks this against the claim snapshot it was given; the repository's conditional `UPDATE ... WHERE status IN (...)` (see `research.md` §6) is the actual concurrency guard against a second decision or a withdrawal winning the race, and reports "already decided" if the write affects zero rows (FR-019). This function itself is called only after that guard has succeeded, so it does not perform I/O-based locking.
  - `reviewer_id != claim.submitter_id` (FR-018) — else this function raises a self-review validation error for the caller to translate into an HTTP 403; the claim's status and violations are left untouched, and it remains available in the review queue for a different reviewer.
  - If `decision.decision == "rejected"`, `decision.reason` MUST be non-empty (FR-009), else this function raises a validation error for the caller (API layer) to translate into an HTTP 422.
- **Effect**: appends a `ReviewDecision` (with `reviewer_id`, `decision`, `reason`, `decided_at`) to `claim.review_decisions`, and sets `claim.status` to `approved`, `rejected`, or `needs_information` accordingly (FR-010). Returns the updated claim for the caller to persist and to trigger the FR-011 employee notification (notification dispatch itself lives outside this pure function, per the spec Assumption that it rides on an existing notification channel).

## `withdraw_claim`

```text
withdraw_claim(claim: ExpenseClaim, requester_id: str) -> ExpenseClaim
```

- **Preconditions**:
  - `requester_id == claim.submitter_id` — only the submitting employee may withdraw their own claim.
  - `claim.status in {pending_review, needs_information}` (FR-020) — as with `apply_review_decision`, the repository's conditional `UPDATE ... WHERE status IN (...)` is the actual race guard against a reviewer decision landing first; if the write affects zero rows the caller returns a "no longer withdrawable" error (FR-019/FR-020 share the same first-write-wins mechanism, see `research.md` §7).
- **Effect**: sets `claim.status = withdrawn`, removing it from the review queue while leaving it visible in the employee's claim history (US3 Acceptance Scenario 3). No `ReviewDecision` is created — withdrawal is an employee action, not a reviewer decision. Returns the updated claim for the caller to persist.

## Input validation boundary (`ExpenseClaimInput` construction)

Performed by the `ExpenseClaimInput` Pydantic v2 model itself (constitution Article III.2), before `evaluate_claim` is ever called — i.e., these are type/field validators, not business rules:

- `amount` MUST be `> 0` (FR-014) — zero/negative rejected at construction.
- `expense_date` MUST parse as a valid calendar date — malformed dates (e.g., month 13) rejected at construction.
- `category` MUST be a non-empty string — missing/null category rejected at construction.
- `description`, if present, is treated as opaque untrusted text: never interpolated into any storage query string (the repository layer uses parameterized queries/ORM binding only), so injection-style payloads are stored harmlessly as plain text rather than executed.

Any of these failures short-circuits before `evaluate_claim` runs, and the API layer returns a `422` with a `ValidationError` body (see `contracts/api.yaml`) — these are the cases the `edge_malformed` partition of `tests/fixtures/synthetic_expenses.json` exercises.

## Traceability

| Fixture partition | Exercises |
|---|---|
| `happy_path` | `evaluate_claim` decision rule, zero-violation path, `auto_approved` and compliant-but-above-threshold `pending_review` |
| `policy_violation` | Checks 1, 3, 4, and the compound-violation case (checks 1+3+4 together) |
| `boundary_limit` | Inclusive/exclusive edges of checks 1, 3, and 7 |
| `edge_malformed` | The `ExpenseClaimInput` validation boundary (rejected before `evaluate_claim` is called) |
