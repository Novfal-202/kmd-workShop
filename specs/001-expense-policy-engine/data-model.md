# Phase 1 Data Model: Corporate Expense Reimbursement & Policy Engine

All entities are Pydantic v2 models (constitution Article III.2). Fields marked **(config)** belong to the configurable `PolicyRuleSet`, not to individual claims.

## ExpenseClaim

Represents a single reimbursement request (spec Key Entities: Expense Claim).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | System-generated identifier |
| `submitter_id` | str | Employee identifier (FR-001) |
| `amount` | Decimal | MUST be > 0 (FR-014); rejected at submission otherwise |
| `category` | str | Required (FR-001, FR-015); MUST resolve to a configured `PolicyRuleSet` category or the claim is routed to manual review |
| `description` | str | Free-text; MUST be validated/sanitized as untrusted input (see Edge/Malformed test cases) |
| `expense_date` | date | Date the expense was incurred; MUST be a valid calendar date (rejected otherwise) |
| `submission_date` | datetime | System-set at submission (and re-set on edit, per FR-016) |
| `receipt_attached` | bool | Whether a receipt was provided (FR-003) |
| `status` | enum | `auto_approved`, `pending_review`, `approved`, `rejected`, `needs_information`, `withdrawn` |
| `violations` | list[ViolationReason] | Zero or more; populated by policy evaluation (FR-007) |
| `review_decisions` | list[ReviewDecision] | History of reviewer actions on this claim (FR-010) |

**Validation rules** (enforced at submission and on every edit, FR-016):
- `amount > 0` (FR-014) — else reject.
- `expense_date` and `submission_date` must be valid, parseable dates — else reject.
- `category` must be present (non-null) — else reject as a missing required field.
- `description` must not be used unsanitized in any storage/query operation (defends against injection payloads such as the SQL-injection-style fixture case).

**State transitions**:

```text
[new submission] --(passes all checks, amount <= auto-approval threshold)--> auto_approved
[new submission] --(fails >=1 check OR amount > auto-approval threshold)--> pending_review
pending_review --(reviewer approves)--> approved                       [FR-018: reviewer != submitter; FR-019: first decision wins]
pending_review --(reviewer rejects, reason required)--> rejected       [FR-018, FR-019]
pending_review --(reviewer requests info)--> needs_information         [FR-018, FR-019]
pending_review --(employee withdraws)--> withdrawn                     [FR-020; races with the three transitions above — first write wins]
needs_information --(employee resubmits / edits)--> pending_review   [re-evaluated per FR-016]
needs_information --(employee withdraws)--> withdrawn                  [FR-020]
[edit at any pre-terminal status] --> re-run full evaluation, status recomputed as above
```

`approved`, `rejected`, and `withdrawn` are terminal for a given claim version; `auto_approved` is also terminal (spec does not define a re-review path for auto-approved claims).

**Concurrency & authorization guards on the `pending_review`/`needs_information` → {`approved`,`rejected`,`needs_information`,`withdrawn`} transitions** (added by 2026-09-03 clarification):
- **FR-018 (segregation of duties)**: `ReviewDecision.reviewer_id` MUST NOT equal `ExpenseClaim.submitter_id`; a same-person attempt is rejected before any state change and the claim stays routed to a different reviewer.
- **FR-019 (first-decision-wins)**: the transition is only valid `WHERE status IN ('pending_review','needs_information')`; a second reviewer decision or a withdrawal attempt racing against it, once the status has already moved, is rejected with an "already decided" / "no longer available" error rather than applied.

## ViolationReason (value object)

One entry per rule failure, used to populate `ExpenseClaim.violations` and drive FR-007's "specific reasons" requirement.

| Field | Type | Notes |
|---|---|---|
| `code` | enum | `over_category_cap`, `missing_required_receipt`, `weekend_policy_violation`, `possible_duplicate`, `late_submission`, `uncapped_category`, `exceeds_auto_approval_threshold` |
| `detail` | str | Human-readable explanation (e.g., "Amount $65.00 exceeds Meals cap of $50.00") |

Multiple `ViolationReason` entries MUST be able to coexist on one claim (spec Edge Cases: compound-violation case).

## PolicyRuleSet (configuration entity)

Represents the configurable business rules (spec Key Entities: Policy Rule Set). Loaded by the policy engine at evaluation time; not part of any individual claim.

| Field | Type | Notes |
|---|---|---|
| `category_caps` | dict[str, Decimal] | **(config)** Per-category spending cap (FR-002). A category absent from this map is "uncapped" and MUST route to manual review (FR-015), not auto-approve. |
| `receipt_required_threshold` | Decimal | **(config)** Inclusive; claims at or above this amount without a receipt are flagged (FR-003) |
| `auto_approval_threshold` | Decimal | **(config)** Inclusive; the maximum amount eligible for auto-approval when otherwise compliant (FR-005) |
| `weekend_exempt_categories` | list[str] | **(config)** Categories not subject to the weekend policy (FR-004) |
| `late_submission_days` | int | **(config)** Default 90 (spec Edge Cases); claims submitted more than this many days after `expense_date` are flagged `late_submission` |

## ReviewDecision

Represents one reviewer action on a flagged claim (spec Key Entities: Review Decision).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `claim_id` | UUID | FK to `ExpenseClaim.id` |
| `reviewer_id` | str | FR-010 |
| `decision` | enum | `approved`, `rejected`, `needs_information` |
| `reason` | str \| None | Required (non-null) when `decision == rejected` (FR-009); optional otherwise |
| `decided_at` | datetime | FR-010 |

**Invariant** (FR-018): `reviewer_id != ExpenseClaim.submitter_id` for the claim referenced by `claim_id` — enforced before the `ReviewDecision` is created, not just recorded as data.

## AuditLogEntry

Represents one immutable record of a policy evaluation, satisfying FR-017 and constitution Article II.1's testability requirement.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `claim_id` | UUID | FK to `ExpenseClaim.id` |
| `evaluated_at` | datetime | |
| `rules_evaluated` | list[str] | Which rule codes were checked (e.g., `over_category_cap`, `missing_required_receipt`, ...) |
| `outcome` | enum | `auto_approved` or `pending_review`, mirroring the claim's resulting status at that evaluation |
| `violations` | list[ViolationReason] | Snapshot of violations found at this evaluation (empty if none) |

Audit entries are append-only: an edit that re-triggers evaluation (FR-016) creates a **new** `AuditLogEntry`, never mutates a prior one, preserving a full compliance history.

## Employee / Reviewer (identity references)

Per spec Assumptions, identity/authentication is provided by an existing corporate identity system. This feature only needs to reference identifiers:

| Field | Type | Notes |
|---|---|---|
| `id` | str | Opaque identifier from the existing identity system |
| `display_name` | str | For UI/notification purposes only |

No separate persistence or lifecycle management for these is in scope.

## Entity Relationships

```text
Employee 1 ──── * ExpenseClaim
ExpenseClaim 1 ──── * ReviewDecision  (reviewer = Reviewer.id)
ExpenseClaim 1 ──── * AuditLogEntry
ExpenseClaim * ──── 1 PolicyRuleSet   (resolved via category, evaluated at decision time — not a stored FK)
```
