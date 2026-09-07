# Quickstart: Validating the Expense Portal Web UI

## Prerequisites

- Node.js 20+ and a package manager (npm/pnpm).
- The `frontend/` app scaffolded per `plan.md` Project Structure (Vite + React + TypeScript + Tailwind).
- No live backend required for the scenarios below — MSW serves `contracts/mock-responses.json` (research.md §7).

## Setup

```bash
cd frontend
npm install
npm run dev
```

## Scenario 1 — All 4 status badges + fallback render correctly (US1, FR-008, FR-017)

1. With the dev server running and MSW mocking enabled, submit a claim using the "Auto-Approved" mock scenario's input values (`contracts/mock-responses.json` → `auto-approved-1`).
2. **Expected**: an "Auto-Approved" badge (success tone) appears with no violation tags.
3. Repeat for `requires-manager-1`, `audit-flagged-1`, and `rejected-1`.
4. **Expected**: "Requires Manager" (warning), "Audit Flagged" (danger), and "Rejected" (danger) badges appear respectively, each with the correct violation tag(s) from that mock's `violations`.
5. Serve a mock claim with an unrecognized `status` value (e.g., patch one mock to `"status": "escalated"`).
6. **Expected**: portal renders a "Pending Review" fallback badge including the raw status text, per FR-017 — it must not crash or silently show nothing.

## Scenario 2 — Dynamic field validation before submission (US2, FR-002, FR-003)

1. On the "New Claim" form, enter `-5` in the amount field and tab away.
2. **Expected**: inline error on the amount field; submit control disabled; no network request is made.
3. Set the expense date to a future date.
4. **Expected**: inline error on the date field.
5. Enter a valid amount above the receipt-required threshold with no receipt attached, then attempt submit.
6. **Expected**: inline warning near the receipt field; submit blocked until a receipt is attached or the amount is corrected.
7. Correct all fields.
8. **Expected**: all inline errors clear and the submit control becomes enabled.

## Scenario 3 — Receipt upload and link attachment (US3, FR-004, FR-005, FR-006)

1. Upload a small PDF or image file as a receipt.
2. **Expected**: filename/thumbnail confirmation appears before submission.
3. Remove it, then instead paste a receipt URL.
4. **Expected**: the link is validated as well-formed and shown as the attachment confirmation.
5. Attempt to attach an oversized file or an unsupported file type.
6. **Expected**: a clear rejection message; the attachment is not included with the claim.

## Scenario 4 — In-progress state, duplicate-submit prevention, and network-error handling (US1, FR-010, FR-011, FR-012)

1. Submit a valid claim against a mock endpoint with artificial delay.
2. **Expected**: a distinct "submitting" state is visible before the decision renders; clicking submit again during this window has no additional effect (no second request fires).
3. Configure MSW to simulate a network failure for one submission.
4. **Expected**: a clear, actionable error message distinct from any status badge; the form's entered values remain intact; retrying re-attempts submission without re-entering fields.

## Scenario 5 — Claim history reflects reviewer decisions (US4, FR-013, FR-014)

1. Load the claim history view against a mock list containing claims in various statuses (reuse `contracts/mock-responses.json` bodies as the list response).
2. **Expected**: each row shows amount, category, date, status badge, and violation reason(s) where present.
3. Update one mock claim's status to `"approved"` (simulating a reviewer decision) and reload the history view.
4. **Expected**: that claim's displayed status reflects the change without any other UI change required.

## Scenario 6 — Mobile-width usability (FR-015, SC-005)

1. Resize the viewport to a common mobile width (e.g., 375px) or use browser device emulation.
2. **Expected**: the claim form, receipt attachment, status badges, and claim history remain fully usable with no horizontal scrolling and no obscured controls.

## Traceability

| Scenario | Requirements exercised |
|---|---|
| 1 | FR-008, FR-009, FR-017, SC-004 |
| 2 | FR-002, FR-003, SC-003 |
| 3 | FR-004, FR-005, FR-006 |
| 4 | FR-010, FR-011, FR-012, SC-002, SC-006 |
| 5 | FR-013, FR-014 |
| 6 | FR-015, SC-005 |
