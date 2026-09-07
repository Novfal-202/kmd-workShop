# Phase 1 Data Model: Authentication and HR Review Portal

## UserAccount (new entity, `src/models/user_account.py`)

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | The identity value stored as `submitter_id` on a claim (employee accounts) or `reviewer_id` on a review decision (HR accounts) — the same string `001`'s existing models already carry, now sourced from a real account instead of a hardcoded constant. |
| `username` | `string` | Unique sign-in identifier. |
| `password_hash` | `string` | bcrypt hash (research.md §2) — a plaintext password is never stored or logged. |
| `role` | `"employee" \| "hr"` | Determines which portal a successful sign-in routes to (FR-002) and which routes a session may call (FR-003). |
| `display_name` | `string` | Shown in the UI (nav bar, HR's employee list) instead of the raw `id`/`username`. |

**Validation rules**: `username` unique across all accounts (enforced at the repository/storage
layer, mirroring how `ClaimRepository` enforces `id` uniqueness via primary key); `role` restricted
to the two-value enum above — no third role exists in this feature.

## SessionToken (new value object, not persisted — `src/services/auth/tokens.py`)

| Field | Type | Notes |
|---|---|---|
| `sub` | `string` | The `UserAccount.id` this token authenticates. |
| `role` | `"employee" \| "hr"` | Copied from `UserAccount.role` at issuance, so route dependencies can check role without a database round trip per request. |
| `exp` | `datetime` | Standard JWT expiry claim (FR-006) — a reasonable session-length window (research.md §1); expiry alone is sufficient for FR-006, no server-side revocation list is introduced. |

**Lifecycle**: issued by `POST /auth/login` on successful credential verification; carried in an
httpOnly cookie on every subsequent request; a `POST /auth/logout` clears the cookie (there is
nothing server-side to invalidate for a plain JWT — the cookie's removal is the entire effect,
consistent with research.md §1's decision not to introduce a session store).

## Employee List Entry (HR view, derived — not a stored entity)

| Field | Type | Notes |
|---|---|---|
| `employee_id` | `string` | The `submitter_id` value from an existing claim row. |
| `display_name` | `string` | From the matching `UserAccount`, if one exists; falls back to `employee_id` itself if no account record matches (keeps the list usable even for data that predates this feature's seeded accounts). |
| `claim_count` | `integer` | How many claims this employee has submitted — shown so HR isn't clicking into empty-looking entries; not a new stored field, computed from the existing `claims` table (research.md §4). |

## ExpenseClaim / ReviewDecision (existing entities, `001`) — unchanged shape, new identity source

| Field | Change |
|---|---|
| `ExpenseClaim.submitter_id` | **No shape change.** Now populated from the authenticated employee's `UserAccount.id` (via a `require_employee` dependency) instead of the hardcoded `CURRENT_EMPLOYEE_ID` constant. |
| `ReviewDecision.reviewer_id` | **No shape change.** Now populated from the authenticated HR user's `UserAccount.id` (via a `require_hr` dependency) instead of the hardcoded `CURRENT_REVIEWER_ID` constant. |

No other field on either entity changes. `ClaimStatus`, `ViolationReason`, `DECIDABLE_STATUSES`,
and the first-write-wins `try_transition` race guard are all reused exactly as `001` built them.

## Relationships

- One `UserAccount` (role `employee`) submits zero-or-more `ExpenseClaim`s, identified by
  `submitter_id == UserAccount.id` — unchanged from `001`, just now backed by a real account rather
  than a constant.
- One `UserAccount` (role `hr`) records zero-or-more `ReviewDecision`s, identified by
  `reviewer_id == UserAccount.id` — same relationship, same source change.
- The HR "employee list" is a read-only projection over existing `ExpenseClaim` rows grouped by
  `submitter_id`, joined to `UserAccount` for display — it is not a new stored relationship.

## State transitions

No new entity lifecycle is introduced. `ExpenseClaim.status` transitions are exactly `001`'s
existing set (`auto_approved`/`pending_review` → `approved`/`rejected`/`needs_information` →
optionally re-evaluated on edit, or `withdrawn`); this feature only changes *who* is authorized to
trigger the `approved`/`rejected`/`needs_information` transition, not the transition rules
themselves. A `SessionToken`'s only "lifecycle" is issued → expires or is explicitly cleared by
logout — it has no intermediate states.
