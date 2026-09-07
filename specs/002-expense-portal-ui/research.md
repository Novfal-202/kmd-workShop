# Phase 0 Research: Corporate Expense Portal Web UI

## 1. Frontend framework & build tooling

- **Decision**: React 18 + TypeScript, built with Vite.
- **Rationale**: User explicitly requested React; Vite gives fast dev-server HMR and a simple build for a single-page employee portal with no SSR requirement (spec has no SEO/server-rendering need). TypeScript gives compile-time safety for the `ExpenseClaim`/status-mapping shapes shared with the backend contract.
- **Alternatives considered**: Next.js (rejected — no server-rendering/routing-on-the-server requirement, adds unneeded complexity for an authenticated internal tool); Create React App (rejected — unmaintained, slower dev loop than Vite).

## 2. Styling

- **Decision**: Tailwind CSS 3, utility-first, with a small shared `statusBadge` style map for the 5 badge states (4 known + fallback).
- **Rationale**: Explicitly requested by the user; utility classes keep the 4-state badge system (FR-008) and violation tags (FR-009) consistent without a separate CSS-in-JS dependency.
- **Alternatives considered**: CSS Modules (rejected — more boilerplate for the same outcome, not requested).

## 3. Form state & dynamic validation (FR-002, FR-003)

- **Decision**: React Hook Form + Zod schema validation, with per-field validation on change/blur.
- **Rationale**: React Hook Form re-renders only changed fields (fits "dynamic field validation" without perceptible lag); Zod gives a single declarative schema (amount > 0, valid non-future date, category required) that can be unit-tested independent of any component (mirrors the project constitution's preference for logic decoupled from its transport/rendering layer — see Constitution Check in plan.md).
- **Alternatives considered**: Formik (rejected — heavier re-render model, less idiomatic with TS inference than RHF+Zod); hand-rolled `useState` validation (rejected — does not scale cleanly to FR-002's multi-field dynamic rules and would duplicate logic per field).

## 4. API/data layer & in-flight state (FR-007, FR-010, FR-011, FR-012)

- **Decision**: TanStack Query (React Query) wrapping a thin typed `fetch`-based API client, with mutation state (`idle` / `pending` / `success` / `error`) driving the in-progress and duplicate-submission-prevention UI states.
- **Rationale**: TanStack Query's mutation status directly models FR-011 ("submitting" state) and FR-010 (a mutation already `pending` cannot be re-fired from the same submit control); its query cache/`refetch` model directly supports FR-014 (claim history reflecting a later reviewer decision on reload).
- **Alternatives considered**: Plain `useEffect` + manual loading flags (rejected — reinvents request de-duplication and retry semantics that FR-010/FR-012 depend on); Redux Toolkit Query (rejected — pulls in a global store the portal doesn't otherwise need).

## 5. Status badge mapping (backend status → 4 UI states)

- **Decision**: A single pure mapping function, `mapClaimToStatusBadge(claim: ExpenseClaim): StatusBadge`, is the one place that turns a backend `status` + `violations[]` into one of `auto_approved → "Auto-Approved"`, `pending_review → "Requires Manager" | "Audit Flagged"`, `rejected → "Rejected"`, anything else → `"Pending Review"` (fallback, FR-017).
- **Rationale**: The backend (`specs/001-expense-policy-engine/contracts/api.yaml`) only exposes one `pending_review` status — it does not distinguish "routine manager review" from "audit flagged." Per spec.md's Assumptions, that split is a presentation-layer decision. To make it deterministic and testable rather than ad hoc per component, the same heuristic already used to build `contracts/mock-responses.json` is adopted as the actual mapping rule: a `pending_review` claim is `"Audit Flagged"` if any of its violations is `possible_duplicate`, `late_submission`, or `uncapped_category` (integrity/compliance concerns); otherwise it is `"Requires Manager"` (routine cap/receipt/weekend/threshold checks). `needs_information` also maps to `"Requires Manager"` (it is a reviewer awaiting more employee input, not a new decision category). `withdrawn`/`approved` (post-review terminal states) render with their own history-only labels rather than the 4 submission-time badges, since they only ever appear in claim history (US4), never as a fresh submission result.
- **Alternatives considered**: Asking the backend team to add a `severity` field (rejected for this feature — would require modifying the already-shipped `001-expense-policy-engine` contract/implementation, which is out of scope here; revisit if the heuristic proves wrong in practice — flagged as a risk, not a blocker).

## 6. Receipt attachment transport (FR-004, FR-005, FR-006)

- **Decision**: A new small backend surface is required and is added as a documented contract extension (not a modification of the existing `001` implementation): `POST /receipts` (multipart file upload OR `{url: string}` JSON body) returning `{receipt_id, kind: "file"|"link", filename_or_url}`; the claim submission (`POST /claims`) is extended with an optional `receipt_id` field alongside the existing `receipt_attached` boolean.
- **Rationale**: The existing `001-expense-policy-engine` `ClaimSubmission` schema only carries a `receipt_attached: boolean` — there is no field to carry an actual file or link. Spec 002's FR-004 explicitly requires both upload and link attachment with a pre-submission confirmation, which is impossible against the current contract as written. Rather than silently assuming a shape, this is called out here as new, additive backend scope this feature depends on (see `contracts/receipts-api.yaml`), justified because it is required by an already-approved requirement (FR-004) in this feature's own spec, not unrequested scope.
- **Alternatives considered**: Encoding the file as a data-URL directly inside the claim JSON payload (rejected — no size-limit enforcement point, no server-side type validation per FR-005, poor for large receipts); requiring links only for v1 (rejected — spec explicitly requires upload as a first-class option, not just link).

## 7. Testing & mocking the 4 status states before backend integration

- **Decision**: Vitest + React Testing Library for component/unit tests; Mock Service Worker (MSW) to serve `specs/002-expense-portal-ui/contracts/mock-responses.json` as the network layer during development and tests, so all 4 badge states (and the fallback + error states) are exercisable without the live backend.
- **Rationale**: MSW intercepts at the network layer (not by mocking the API-client module), so the same component code path used against the real backend is exercised in tests — directly reusing the 8 mock payloads already produced for this feature.
- **Alternatives considered**: Jest + manual `fetch` mocks (rejected — MSW's network-level interception is less brittle and already fits the existing mock JSON fixture shape).

## 8. Draft preservation on session expiry (FR-016)

- **Decision**: Form values are mirrored to `sessionStorage` on every change (debounced) and rehydrated on mount; a 401 response from any API call triggers a re-authentication prompt without clearing the in-memory form state.
- **Rationale**: `sessionStorage` survives a re-auth redirect/reload within the same tab without needing new backend storage, satisfying FR-016 with no server-side change.
- **Alternatives considered**: In-memory only (rejected — lost on a full page reload, which a re-auth redirect may trigger); persisting to the backend as a draft entity (rejected — no such capability exists or is requested; out of scope per spec Assumptions).

## 9. Interim employee-name capture (FR-001, FR-018)

- **Decision**: `employee_name` is added as an optional, default-`""` field on `001`'s
  `ExpenseClaimInput`/`ExpenseClaim` models and `claims` table (with an idempotent `ALTER TABLE`
  migration guard for the pre-existing dev database), while the portal's own Zod schema makes it
  *required* client-side.
- **Rationale**: Making the field backend-optional avoids breaking the ~20 already-passing `001`
  backend tests and the protected `tests/fixtures/synthetic_expenses.json` fixture; "required"
  only needs to be true from the employee's perspective, which the client-side Zod schema already
  enforces (the same pattern FR-002/FR-003 use for every other required field).
- **Alternatives considered**: A hard-required backend field (rejected — large, unnecessary blast
  radius across an unrelated, already-shipped test suite for a field whose only real requirement
  is "the portal won't let you submit without it").

## 10. Claim history table density, submit button placement, and page whitespace (FR-019, FR-020, FR-021)

- **Decision**: Increase `<td>`/`<tr>` vertical padding in `ClaimHistoryList` (`py-3` → a larger
  value) so status badges and violation tags read as clearly separated between rows; restyle the
  claim form's submit control as a bottom action bar directly attached to the form (e.g. a
  top-bordered footer strip inside the same card) rather than a button floating below its own gap
  of whitespace; reduce the outer page wrapper's vertical padding (`py-8`/`sm:py-10`) on
  `NewClaimPage`/`ClaimHistoryPage` so a short page doesn't read as mostly empty space, while
  leaving the card's own internal padding (`p-6`/`sm:p-8`) — which fixed the earlier "no margin"
  complaint — untouched, per the clarify session's explicit confirmation.
- **Rationale**: These are the three concrete complaints raised in the `/speckit-clarify` session
  of this date; the clarify answer explicitly distinguishes "excess empty page area" (to reduce)
  from "internal card/table padding" (to keep), so the fix must touch page-level vertical rhythm
  and the submit button's own container, not undo the earlier margin work.
- **Alternatives considered**: Reducing the card's internal padding instead (rejected — directly
  contradicted by the clarify session's answer, and would reintroduce the original "cramped, no
  margin" complaint this iteration is not asking to bring back).

## Outstanding NEEDS CLARIFICATION

None — all Technical Context unknowns are resolved above (including this amendment's).
