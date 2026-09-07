# Implementation Plan: Corporate Expense Portal Web UI

**Branch**: `002-expense-portal-ui` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-expense-portal-ui/spec.md`

## Summary

Build a React + Tailwind single-page web client for the existing Corporate Expense Reimbursement & Policy Engine backend (`001-expense-policy-engine`). Employees fill a dynamically-validated claim form, attach a receipt by upload or link, submit to the backend, and see one of four status badges (Auto-Approved, Requires Manager, Audit Flagged, Rejected — falling back to a generic Pending Review state for any unrecognized backend status) plus per-violation tags, computed by a single pure mapping function from the backend's actual `status`/`violations` payload. A claim history view lists all of an employee's own claims and reflects later reviewer decisions on reload. Receipt upload/link requires one small additive backend surface (`POST /receipts`) since the existing `001` contract only carries a boolean `receipt_attached` flag; this is documented as a new, spec-justified extension rather than a modification of the shipped `001` implementation.

## Technical Context

**Language/Version**: TypeScript 5.x, React 18

**Primary Dependencies**: Vite (build/dev server), Tailwind CSS 3, React Hook Form + Zod (dynamic field validation, research.md §3), TanStack Query (API/mutation state, research.md §4), MSW (mock network layer for the 8 status mocks, research.md §7)

**Storage**: N/A on the client beyond browser `sessionStorage` for in-progress draft preservation (FR-016, research.md §8); all durable claim/receipt data lives in the existing backend.

**Testing**: Vitest + React Testing Library (component/unit), MSW-backed integration tests driven by `contracts/mock-responses.json` for all 4 status states + fallback + error paths.

**Target Platform**: Modern evergreen browsers (Chrome/Edge/Firefox/Safari, last 2 versions), responsive from ~375px mobile width up through desktop (FR-015).

**Project Type**: Web application — new `frontend/` client added alongside the existing `src/` backend (Option 2 structure).

**Performance Goals**: Status decision or an explicit in-progress/error state visible within 5 seconds of submission under normal network conditions (SC-002); field-level validation feedback renders within a single interaction frame (no perceptible lag) to support SC-003's pre-submission catch rate.

**Constraints**: Status badges MUST be distinguishable by more than color alone (icon/text, not color-only) for accessibility, since FR-008/FR-009 are safety/compliance-relevant signals; `mapClaimToStatusBadge` (research.md §5) MUST be the single source of truth for status→badge mapping — no component may string-match a raw backend status itself, so a future backend status addition only requires one function change.

**Scale/Scope**: Single employee-facing app; 4 user stories, ~6 core components (`ClaimForm`, `ReceiptAttachment`, `StatusBadge`, `ViolationTag`, `ClaimHistoryList`, plus page-level containers); no reviewer/manager UI (out of scope per spec Assumptions).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution (`constitution.md`, "Project Constitution: Corporate Policy & Expense Services") was written for the `001` backend service. Its articles are evaluated below as they apply to a frontend feature; Article III's Pydantic/HTTP-transport wording is backend-specific and is interpreted by its underlying intent (keep validation/decision logic decoupled from and testable independent of its rendering/transport layer) rather than applied literally.

| Article | Requirement | Status | Notes |
|---|---|---|---|
| I.1 | No code without an approved specification | PASS | `spec.md` exists and passed its requirements-quality checklist (all items pass, no open `[NEEDS CLARIFICATION]`) before this plan was generated. |
| I.2 | Diffs that violate spec.md or add unrequested scope are rejected | PASS (design-time) | This plan implements FR-001..FR-017 as written. The one piece of new backend scope (`POST /receipts`, research.md §6) is justified as required by FR-004, not unrequested — documented explicitly in `contracts/receipts-api.yaml` rather than silently bundled into the existing `001` contract. |
| II.1 | Every business policy rule MUST have a corresponding synthetic test case | PASS (adapted) | This feature has no *policy* rules of its own (policy evaluation is `001`'s responsibility) — its analogous obligation is that every client-side validation rule (FR-002: amount>0, valid non-future date, required-receipt threshold) has a corresponding unit test against the Zod schema, and every status-mapping branch (research.md §5) has a corresponding test against `contracts/mock-responses.json`. Enforced in Phase 2 tasks. |
| II.2 | Generated code MUST pass 100% of deterministic unit tests and static linters | CARRIED FORWARD | Enforced at implementation/CI time, not a design-time gate. |
| III.1 | Pure business logic MUST remain decoupled from HTTP/API transport layers | PASS (adapted) | `mapClaimToStatusBadge` and the Zod validation schema are pure functions with no `fetch`/component dependency (`contracts/ui-contract.md`); API calls live only in TanStack Query hooks, never inside the mapping/validation logic or presentational components. |
| III.2 | Models MUST strictly use Pydantic v2 validation contracts | N/A (frontend has no Pydantic models) | This article governs backend Python models. The frontend's equivalent data-contract discipline is TypeScript types mirrored 1:1 from the backend OpenAPI schemas (`data-model.md`) plus Zod for its own form-input validation — the same spirit (a single strict, typed validation boundary) applied in the frontend's own language/runtime. |

No violations requiring justification beyond the one documented, spec-required backend extension above — Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/002-expense-portal-ui/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/             # Phase 1 output (/speckit-plan command)
│   ├── receipts-api.yaml       # New, additive backend contract this feature depends on
│   ├── ui-contract.md          # Internal component/function contracts
│   └── mock-responses.json     # Pre-existing: 8 status-state mocks for MSW
├── checklists/
│   └── requirements.md
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/                       # Existing 001-expense-policy-engine backend (unchanged by this feature,
│                          #   except the additive receipt_id field and new /receipts routes it depends on)
├── models/
├── services/
├── repositories/
└── api/

frontend/                  # New: this feature
├── src/
│   ├── components/
│   │   ├── ClaimForm.tsx           # FR-001..FR-003; owns ClaimFormDraft (React Hook Form + Zod)
│   │   ├── ReceiptAttachment.tsx   # FR-004..FR-006
│   │   ├── StatusBadge.tsx         # FR-008, FR-017
│   │   ├── ViolationTag.tsx        # FR-009
│   │   └── ClaimHistoryList.tsx    # FR-013, FR-014
│   ├── pages/
│   │   ├── NewClaimPage.tsx        # US1: composes ClaimForm + ReceiptAttachment + submission state
│   │   └── ClaimHistoryPage.tsx    # US4
│   ├── lib/
│   │   ├── statusMapping.ts        # mapClaimToStatusBadge (research.md §5) — pure, no API/component deps
│   │   ├── validationSchema.ts     # Zod schema for ClaimFormDraft (research.md §3)
│   │   ├── apiClient.ts            # Typed fetch wrapper against 001's api.yaml + this feature's receipts-api.yaml
│   │   └── draftPersistence.ts     # sessionStorage mirroring (FR-016, research.md §8)
│   ├── types/
│   │   └── api.ts                  # ExpenseClaimApiResponse, ViolationReasonApi, ReceiptReference (data-model.md)
│   └── mocks/
│       └── handlers.ts             # MSW handlers built from contracts/mock-responses.json
└── tests/
    ├── unit/                       # statusMapping.ts, validationSchema.ts
    ├── component/                  # ClaimForm, ReceiptAttachment, StatusBadge, ViolationTag, ClaimHistoryList
    └── integration/                # Full NewClaimPage / ClaimHistoryPage flows against MSW mocks
```

**Structure Decision**: Web application (Option 2) — the existing `src/` backend is untouched in its own layering (models/services/repositories/api), and this feature adds a sibling `frontend/` app. Within `frontend/`, `lib/statusMapping.ts` and `lib/validationSchema.ts` are kept as pure, transport/render-free modules (mirroring the constitution's Article III decoupling intent, adapted per the Constitution Check above), separate from `lib/apiClient.ts` (the only place `fetch` is called) and from `components/`/`pages/` (rendering only).

## Complexity Tracking

*No unjustified violations — table omitted. The one piece of new scope (the `/receipts` backend endpoint) is tracked and justified in the Constitution Check row for Article I.2 and in `research.md` §6, not as a complexity/violation trade-off.*

## Amendment (2026-09-07): Employee Name, Table History, and Layout Polish (FR-018..FR-021)

Two `/speckit-clarify` sessions after this feature's original delivery added FR-018 (interim
employee-name capture), amended FR-013 (table layout) and FR-001, and added FR-019..FR-021 (claim
history row density, submit-button integration, page whitespace balance). This amendment covers
that work without regenerating the artifacts above, since no new entity, contract, or dependency is
introduced.

**Status**: FR-018 (employee name field) and FR-013's table conversion are already implemented and
tested. FR-019, FR-020, and FR-021 (this plan's remaining scope) are not yet implemented.

**Technical Context delta**: No new dependencies, no new Technical Context values change — this is
a Tailwind class-level styling amendment plus one additive backend field (research.md §9), not a
new architectural surface.

**Constitution re-check**: No new gate implications. Article I.2 (no unrequested scope) is
satisfied by scoping FR-019..FR-021 exactly to the three complaints raised in clarify, per
research.md §10 — the card/table's internal padding from the prior polish round is explicitly
preserved, not reopened.

**Files affected** (extends the Project Structure above, no new files):

```text
frontend/src/components/ClaimHistoryList.tsx   # FR-019: row vertical spacing
frontend/src/components/ClaimForm.tsx          # FR-020: submit button becomes an attached footer bar
frontend/src/pages/NewClaimPage.tsx            # FR-020 (submit bar container), FR-021 (page padding)
frontend/src/pages/ClaimHistoryPage.tsx        # FR-021: page padding
```
