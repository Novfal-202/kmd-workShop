# Phase 1 Data Model: Corporate Expense Portal Web UI

These are the frontend's own TypeScript data shapes. `ExpenseClaimApiResponse` mirrors the backend's `ExpenseClaim` schema (`specs/001-expense-policy-engine/contracts/api.yaml`) as received over the wire; the rest are UI-layer types derived from it. No backend model in `001` is redefined here.

## ExpenseClaimApiResponse (wire shape, from backend)

Mirrors `components.schemas.ExpenseClaim` in `specs/001-expense-policy-engine/contracts/api.yaml`, plus the additive fields introduced by this feature (`research.md` §6).

| Field | Type | Notes |
|---|---|---|
| `id` | `string` (uuid) | |
| `submitter_id` | `string` | |
| `category` | `string` | |
| `amount` | `number` | |
| `description` | `string?` | |
| `expense_date` | `string` (date) | |
| `submission_date` | `string` (date-time) | |
| `receipt_attached` | `boolean` | |
| `receipt_id` | `string?` (uuid) | New (FR-004) — set when a receipt was uploaded/linked via `POST /receipts` |
| `employee_name` | `string?` | New (FR-001/FR-018, research.md §9) — interim, portal-captured identity; optional on the wire (backend default `""`), required client-side |
| `status` | `"auto_approved" \| "pending_review" \| "approved" \| "rejected" \| "needs_information" \| "withdrawn"` | |
| `violations` | `ViolationReasonApi[]` | |

## ViolationReasonApi (wire shape)

| Field | Type | Notes |
|---|---|---|
| `code` | `"over_category_cap" \| "missing_required_receipt" \| "weekend_policy_violation" \| "possible_duplicate" \| "late_submission" \| "uncapped_category" \| "exceeds_auto_approval_threshold"` | |
| `detail` | `string` | Human-readable reason shown in the violation tag (FR-009) |

## StatusBadge (UI-derived, FR-008/FR-017)

The output of `mapClaimToStatusBadge` (research.md §5) — never constructed by hand from raw backend status strings anywhere else in the UI.

| Field | Type | Notes |
|---|---|---|
| `label` | `"Auto-Approved" \| "Requires Manager" \| "Audit Flagged" \| "Rejected" \| "Pending Review"` | `"Pending Review"` is the FR-017 fallback for any unrecognized backend status |
| `tone` | `"success" \| "warning" \| "danger" \| "neutral"` | Drives the Tailwind color classes; `Auto-Approved → success`, `Requires Manager → warning`, `Audit Flagged → danger`, `Rejected → danger`, `Pending Review (fallback) → neutral` |
| `rawStatus` | `string` | The original backend status string, always retained for the fallback case and for debugging |

## ClaimFormDraft (UI-only, form state)

The React Hook Form values, persisted to `sessionStorage` per FR-016.

| Field | Type | Validation rule (FR-002, FR-003) |
|---|---|---|
| `employeeName` | `string` | Non-empty (FR-018) |
| `amount` | `string` (raw input) → parsed `number` | Must parse to a number `> 0` |
| `category` | `string` | Non-empty, one of the known categories supplied by the portal's category list |
| `expenseDate` | `string` (ISO date) | Must be a valid date, not in the future |
| `description` | `string?` | Optional, no format constraint |
| `receipt` | `ReceiptAttachmentDraft \| null` | See below; required only if `amount` is at/above the receipt threshold surfaced by the backend/policy config (US2 Acceptance Scenario 3) |

## ReceiptAttachmentDraft (UI-only, pre-submission)

| Field | Type | Notes |
|---|---|---|
| `kind` | `"file" \| "link"` | |
| `file` | `File?` | Present when `kind === "file"`; validated client-side against allowed MIME types and max size (FR-005) before upload |
| `url` | `string?` | Present when `kind === "link"`; validated as well-formed URL (US3 Acceptance Scenario 2) |
| `uploadStatus` | `"idle" \| "uploading" \| "uploaded" \| "error"` | Drives the upload-progress edge case (spec Edge Cases: large/slow uploads) |
| `receiptId` | `string?` (uuid) | Set once `POST /receipts` resolves; sent as `receipt_id` on claim submission |
| `previewLabel` | `string` | Filename (file) or the validated URL (link), shown as the pre-submission confirmation (FR-004) |

## ClaimSubmissionState (UI-only, submission lifecycle)

Drives FR-010 (duplicate-submit prevention), FR-011 (in-progress state), FR-012 (error + retry).

| Field | Type | Notes |
|---|---|---|
| `phase` | `"idle" \| "submitting" \| "succeeded" \| "failed"` | `"submitting"` disables the submit control (FR-010) and renders the in-progress state (FR-011) |
| `result` | `ExpenseClaimApiResponse?` | Set on `"succeeded"`; feeds `mapClaimToStatusBadge` |
| `error` | `{ message: string; retryable: boolean }?` | Set on `"failed"` (FR-012); the original `ClaimFormDraft` remains intact for retry |

## Relationships

- One `ClaimFormDraft` (+ optional `ReceiptAttachmentDraft`) is submitted and becomes one `ExpenseClaimApiResponse`.
- One `ExpenseClaimApiResponse` maps to exactly one `StatusBadge` (via `mapClaimToStatusBadge`) and zero-or-more `ViolationReasonApi` rendered as violation tags.
- The claim history view (US4) is a list of `ExpenseClaimApiResponse`, each independently mapped to its own `StatusBadge`.

## State transitions (UI submission lifecycle only — backend claim-status transitions are owned by `001-expense-policy-engine`)

```text
idle --submit--> submitting --success--> succeeded
submitting --network/server error--> failed --retry--> submitting
failed --edit any field--> idle (form remains populated)
```
