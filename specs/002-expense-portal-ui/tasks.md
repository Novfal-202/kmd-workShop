---

description: "Task list template for feature implementation"
---

# Tasks: Corporate Expense Portal Web UI

**Input**: Design documents from `/specs/002-expense-portal-ui/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md (all present)

**Tests**: Included. The plan's Constitution Check (Article II.1, adapted) commits to a corresponding test for every client-side validation rule and every status-mapping branch, enforced in this phase.

**Organization**: Tasks are grouped by user story (spec.md priorities P1/P2/P2/P3) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Paths are relative to the repository root; the existing `src/` backend (001) is untouched except where explicitly noted.

## Path Conventions

Web app per plan.md: new `frontend/` app alongside the existing `src/` backend.

```text
frontend/src/{components,pages,lib,types,mocks}
frontend/tests/{unit,component,integration}
```

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Scaffold `frontend/` as a Vite + React 18 + TypeScript project (`frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/index.html`, `frontend/src/main.tsx`) per plan.md Project Structure
- [X] T002 Install core dependencies in `frontend/package.json`: `react`, `react-dom`, `react-router-dom`, `react-hook-form`, `zod`, `@hookform/resolvers`, `@tanstack/react-query`, `tailwindcss`, `postcss`, `autoprefixer`, and dev dependencies `msw`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`
- [X] T003 [P] Configure Tailwind CSS in `frontend/tailwind.config.js`, `frontend/postcss.config.js`, and `frontend/src/index.css` (research.md §2)
- [X] T004 [P] Configure ESLint + Prettier for `frontend/` (`frontend/.eslintrc.cjs`, `frontend/.prettierrc`)
- [X] T005 [P] Configure Vitest + React Testing Library test environment in `frontend/vitest.config.ts` and `frontend/tests/setup.ts`
- [X] T006 [P] Copy `specs/002-expense-portal-ui/contracts/mock-responses.json` into `frontend/src/mocks/fixtures/mock-responses.json` and scaffold MSW browser/server entry points in `frontend/src/mocks/browser.ts` and `frontend/src/mocks/server.ts` (research.md §7)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Define shared TypeScript types (`ExpenseClaimApiResponse`, `ViolationReasonApi`) in `frontend/src/types/api.ts` per data-model.md
- [X] T008 [P] Implement the typed fetch wrapper base (base URL config, JSON parsing, error normalization into `{message, retryable}`) in `frontend/src/lib/apiClient.ts` per contracts/receipts-api.yaml and `specs/001-expense-policy-engine/contracts/api.yaml`
- [X] T009 [P] Implement the pure `mapClaimToStatusBadge` function in `frontend/src/lib/statusMapping.ts` per research.md §5 and data-model.md `StatusBadge`
- [X] T010 [P] Build MSW request handlers from `frontend/src/mocks/fixtures/mock-responses.json` covering `POST /claims`, `GET /claims`, `POST /receipts` in `frontend/src/mocks/handlers.ts`
- [X] T011 Set up app shell, routing (`/` → NewClaimPage, `/history` → ClaimHistoryPage), and the TanStack Query `QueryClientProvider` in `frontend/src/App.tsx` and `frontend/src/main.tsx`
- [X] T012 [P] Implement the `sessionStorage` draft-persistence helper (save/rehydrate/clear) in `frontend/src/lib/draftPersistence.ts` per research.md §8 and FR-016

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Employee Submits an Expense Claim Through the Portal (Priority: P1) 🎯 MVP

**Goal**: An employee fills the claim form, submits it to the backend, and sees the returned policy-evaluation outcome as one of the 4 status badges (or the fallback), with violation reasons, an in-progress state, and graceful error handling.

**Independent Test**: Fill out the claim form with valid data, submit, and confirm the portal displays the correct evaluation outcome and reason within seconds; verify network failure and unrecognized-status paths independently via mocked responses.

### Tests for User Story 1 ⚠️

- [X] T013 [P] [US1] Unit test `mapClaimToStatusBadge` against every entry in `frontend/src/mocks/fixtures/mock-responses.json`, asserting the returned `label` matches each entry's `ui_status`, in `frontend/tests/unit/statusMapping.test.ts`
- [X] T014 [P] [US1] Integration test: submitting a claim renders the correct badge for each of Auto-Approved, Requires Manager, Audit Flagged, and Rejected mocks in `frontend/tests/integration/newClaimSubmission.test.tsx`
- [X] T015 [P] [US1] Integration test: a simulated network/server failure shows a distinct error message, preserves entered field values, and a retry re-attempts submission in `frontend/tests/integration/newClaimError.test.tsx`
- [X] T016 [P] [US1] Integration test: an unrecognized backend `status` value renders the "Pending Review" fallback badge including the raw status text (FR-017) in `frontend/tests/integration/newClaimFallback.test.tsx`

### Implementation for User Story 1

- [X] T017 [P] [US1] Implement `<StatusBadge>` presentational component (renders `badge.label` styled purely by `badge.tone`) in `frontend/src/components/StatusBadge.tsx`
- [X] T018 [P] [US1] Implement `<ViolationTag>` presentational component (renders `violation.detail`, icon/tone from `violation.code`) in `frontend/src/components/ViolationTag.tsx`
- [X] T019 [US1] Implement base `<ClaimForm>` component with amount, category, and expense-date fields wired through React Hook Form, exposing `onSubmit(draft): Promise<void>` (no validation rules yet — added in US2) in `frontend/src/components/ClaimForm.tsx`
- [X] T020 [US1] Implement `useSubmitClaim` TanStack Query mutation hook wrapping `POST /claims` in `frontend/src/lib/apiClient.ts` (depends on T007, T008)
- [X] T021 [US1] Implement `NewClaimPage` composing `ClaimForm` + the submission lifecycle (`idle`/`submitting`/`succeeded`/`failed`) and rendering `StatusBadge` + `ViolationTag` list on success, in `frontend/src/pages/NewClaimPage.tsx` (depends on T017, T018, T019, T020, T009)
- [X] T022 [US1] Disable the submit control while `useSubmitClaim`'s mutation is `pending`, preventing duplicate submissions (FR-010) in `frontend/src/pages/NewClaimPage.tsx`
- [X] T023 [US1] Implement the submission error banner with a retry action that reuses the still-populated `ClaimForm` values (FR-012) in `frontend/src/pages/NewClaimPage.tsx`

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP.

---

## Phase 4: User Story 2 - Employee Gets Immediate Field-Level Guidance While Filling the Form (Priority: P2)

**Goal**: Dynamic, per-field validation (amount, date, receipt-required warning) before submission, without a backend round-trip.

**Independent Test**: Enter invalid values into each field individually (negative amount, missing category, future/invalid date, no receipt above threshold) and confirm each triggers a specific inline message without submitting.

### Tests for User Story 2 ⚠️

- [X] T024 [P] [US2] Unit tests for the Zod validation schema (amount must be `>0`, expense date must be valid and not in the future, category required) in `frontend/tests/unit/validationSchema.test.ts`
- [X] T025 [P] [US2] Component test: entering invalid values into each `ClaimForm` field shows its inline error and disables submit; correcting all fields clears every error in `frontend/tests/component/ClaimForm.test.tsx`

### Implementation for User Story 2

- [X] T026 [P] [US2] Implement the Zod schema for `ClaimFormDraft` (amount, category, expenseDate, description, receipt-required conditional) in `frontend/src/lib/validationSchema.ts` per research.md §3
- [X] T027 [US2] Wire the Zod schema into `ClaimForm` via the React Hook Form resolver with on-change/on-blur validation mode in `frontend/src/components/ClaimForm.tsx` (depends on T019, T026)
- [X] T028 [US2] Add inline, field-adjacent error messages for amount, category, and expense date in `frontend/src/components/ClaimForm.tsx`
- [X] T029 [US2] Add the receipt-required-threshold inline warning (shown when amount is at/above the threshold and no receipt is attached) in `frontend/src/components/ClaimForm.tsx`
- [X] T030 [US2] Disable the `NewClaimPage` submit control whenever `ClaimForm` reports any active validation error, in addition to the in-flight check from T022, in `frontend/src/pages/NewClaimPage.tsx` (depends on T021, T027)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Employee Attaches Receipts by Upload or by Link (Priority: P2)

**Goal**: Attach a receipt either as an uploaded file or a pasted link, with pre-submission confirmation, client-side type/size/URL checks, and removal.

**Independent Test**: Upload a file in one claim and paste a link in another; confirm both are accepted, previewed, and correctly included with the submitted claim; confirm an unsupported/oversized file is rejected with a clear message.

### Tests for User Story 3 ⚠️

- [X] T031 [P] [US3] Component test: uploading a supported file shows a filename/thumbnail confirmation in `frontend/tests/component/ReceiptAttachment.test.tsx`
- [X] T032 [P] [US3] Component test: pasting a well-formed URL validates and shows a link confirmation; a malformed URL is rejected in `frontend/tests/component/ReceiptAttachment.test.tsx`
- [X] T033 [P] [US3] Component test: an oversized file or unsupported file type is rejected with a clear message and is not attached, in `frontend/tests/component/ReceiptAttachment.test.tsx`

### Implementation for User Story 3

- [X] T034 [P] [US3] Add the `ReceiptReference` type and `ReceiptAttachmentDraft` type in `frontend/src/types/api.ts` per data-model.md (depends on T007)
- [X] T035 [US3] Implement `uploadReceipt` and `deleteReceipt` API calls against `POST /receipts` / `DELETE /receipts/{id}` in `frontend/src/lib/apiClient.ts` per `specs/002-expense-portal-ui/contracts/receipts-api.yaml` (depends on T008, T010)
- [X] T036 [US3] Implement `<ReceiptAttachment>` component (file-upload and link-entry modes, client-side type/size/URL validation before calling `uploadReceipt`, upload-progress state, preview, and removal) in `frontend/src/components/ReceiptAttachment.tsx` (depends on T034, T035)
- [X] T037 [US3] Integrate `<ReceiptAttachment>` into `ClaimForm`, wiring the resulting `receiptId` into the submitted claim payload (`receipt_id` field) in `frontend/src/components/ClaimForm.tsx` (depends on T019, T036)
- [X] T038 [US3] Prevent claim submission while a receipt upload is still in progress, extending the guard from T022, in `frontend/src/pages/NewClaimPage.tsx`

**Checkpoint**: User Stories 1, 2, AND 3 all work independently.

---

## Phase 6: User Story 4 - Employee Reviews Their Claim History and Status Changes (Priority: P3)

**Goal**: A list of the employee's own claims with status/violations, reflecting later reviewer decisions on reload.

**Independent Test**: Submit several claims with different outcomes, confirm the history view shows correct status/reasons for each, and confirm an updated status appears after a simulated backend-side reviewer decision and a reload.

### Tests for User Story 4 ⚠️

- [X] T039 [P] [US4] Component test: `ClaimHistoryList` renders amount, category, date, status badge, and violation tags for each mocked claim in `frontend/tests/component/ClaimHistoryList.test.tsx`
- [X] T040 [P] [US4] Integration test: reloading the claim history after a mock claim's status changes (e.g., to `approved`) reflects the new status without further action in `frontend/tests/integration/claimHistoryRefresh.test.tsx`

### Implementation for User Story 4

- [X] T041 [P] [US4] Implement `<ClaimHistoryList>` presentational component, computing each row's badge via `mapClaimToStatusBadge` and reusing `StatusBadge`/`ViolationTag`, in `frontend/src/components/ClaimHistoryList.tsx` (depends on T009, T017, T018)
- [X] T042 [US4] Implement `useClaimHistory` TanStack Query hook wrapping `GET /claims` with refetch-on-mount/window-focus in `frontend/src/lib/apiClient.ts` (depends on T007, T008)
- [X] T043 [US4] Implement `ClaimHistoryPage` composing `useClaimHistory` + `ClaimHistoryList` (loading/empty/error states) in `frontend/src/pages/ClaimHistoryPage.tsx` (depends on T041, T042)
- [X] T044 [US4] Add navigation between `NewClaimPage` and `ClaimHistoryPage` in `frontend/src/App.tsx`

**Checkpoint**: All 4 user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T045 [P] Wire `draftPersistence` (T012) into `ClaimForm`/`NewClaimPage`: mirror field changes to `sessionStorage`, rehydrate on mount, and prompt re-authentication on a `401` without discarding the draft (FR-016) in `frontend/src/pages/NewClaimPage.tsx`
- [X] T046 [P] Responsive/mobile-width pass (no horizontal scrolling, all controls usable at ~375px) across `ClaimForm`, `ReceiptAttachment`, `StatusBadge`, and `ClaimHistoryList` (FR-015, SC-005)
- [X] T047 [P] Accessibility pass: ensure status badges are distinguishable by icon/text and not color alone, and add ARIA attributes for inline field errors, across `frontend/src/components/`
- [X] T048 Execute `specs/002-expense-portal-ui/quickstart.md` Scenarios 1-6 end-to-end against the MSW mocks and record results
- [X] T049 [P] Add developer instructions (install, dev server, running tests, MSW mocking) in `frontend/README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 has no dependency on US2/US3/US4
  - US2 extends `ClaimForm` (T019 from US1) but is independently testable via its own Zod schema/tests
  - US3 extends `ClaimForm` (T019 from US1) but is independently testable via `ReceiptAttachment` in isolation
  - US4 reuses `StatusBadge`/`ViolationTag`/`mapClaimToStatusBadge` (US1/Foundational) but adds no new dependency back onto US1's page-level logic
- **Polish (Phase 7)**: Depends on all four user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational; builds on `ClaimForm` from US1 (same file, sequential edits) but is independently testable
- **User Story 3 (P2)**: Can start after Foundational; builds on `ClaimForm` from US1 (same file, sequential edits) but is independently testable via `ReceiptAttachment` alone
- **User Story 4 (P3)**: Can start after Foundational - reuses shared presentational components but does not depend on US2/US3 being complete

### Within Each User Story

- Tests written before implementation tasks (write, confirm they fail, then implement)
- Types/pure functions before components; components before page-level composition
- Story complete and checkpointed before moving to the next priority

### Parallel Opportunities

- All Setup tasks marked [P] (T003-T006) can run in parallel after T001-T002
- All Foundational tasks marked [P] (T008, T009, T010, T012) can run in parallel after T007
- All US1 test tasks (T013-T016) can run in parallel; `StatusBadge`/`ViolationTag` (T017-T018) can run in parallel
- All US2 test tasks (T024-T025) can run in parallel; T026 can run in parallel with US1/US3/US4 test-writing
- All US3 test tasks (T031-T033) can run in parallel; T034 can run in parallel with other stories' work
- All US4 test tasks (T039-T040) can run in parallel; T041 can run in parallel with US2/US3 work
- Polish tasks T045-T047, T049 can run in parallel; T048 runs last

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test mapClaimToStatusBadge against mock-responses.json in frontend/tests/unit/statusMapping.test.ts"
Task: "Integration test: submitting a claim renders each of the 4 status badges in frontend/tests/integration/newClaimSubmission.test.tsx"
Task: "Integration test: network/server failure shows error, preserves fields, retry works in frontend/tests/integration/newClaimError.test.tsx"
Task: "Integration test: unrecognized status renders Pending Review fallback in frontend/tests/integration/newClaimFallback.test.tsx"

# Launch independent components for User Story 1 together:
Task: "Implement StatusBadge component in frontend/src/components/StatusBadge.tsx"
Task: "Implement ViolationTag component in frontend/src/components/ViolationTag.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run quickstart.md Scenario 1 and 4 against User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (quickstart.md Scenario 2) → Deploy/Demo
4. Add User Story 3 → Test independently (quickstart.md Scenario 3) → Deploy/Demo
5. Add User Story 4 → Test independently (quickstart.md Scenario 5) → Deploy/Demo
6. Polish phase → quickstart.md Scenario 6 (mobile) and full end-to-end pass

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (owns `ClaimForm` base + `NewClaimPage`)
   - Developer B: User Story 4 (fully independent of `ClaimForm`)
   - Developer C: prepares User Story 2/3 test suites against the not-yet-extended `ClaimForm`, then integrates once T019 lands
3. Stories complete and integrate independently, with US2/US3 sequenced after US1's `ClaimForm` exists (same file)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 and US3 both edit `frontend/src/components/ClaimForm.tsx` after US1 creates it — sequence these two stories' `ClaimForm` edits (T027 before T037, or vice versa) rather than running them as true parallel file edits, even though they are independently testable in isolation
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
