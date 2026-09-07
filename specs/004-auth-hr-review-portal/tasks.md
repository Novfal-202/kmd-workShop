---

description: "Task list template for feature implementation"
---

# Tasks: Authentication and HR Review Portal

**Input**: Design documents from `/specs/004-auth-hr-review-portal/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md (all present)

**Tests**: Included. The plan's Constitution Check (Article II.1, adapted) commits to a corresponding test for every new access-control rule (wrong-role access blocked, rejection requires a reason, an already-decided claim offers no further action, a concurrent second decision is rejected), enforced in this phase.

**Organization**: Tasks are grouped by user story (spec.md priorities P1/P1/P1/P3) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Paths are relative to the repository root; this feature touches both the existing `001-expense-policy-engine` backend (`src/`, `tests/`) and the existing `002-expense-portal-ui` frontend (`frontend/`).

## Path Conventions

Web app per plan.md: extends both existing halves of the project, no new project/service.

```text
src/{models,services/auth,repositories,api}
tests/{unit,contract,integration}
frontend/src/{components,pages,lib}
frontend/tests/{component,integration}
```

---

## Phase 1: Setup

**Purpose**: New backend dependencies this feature needs

- [ ] T001 Add `bcrypt` and `pyjwt` to `[project.dependencies]` in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The identity/session infrastructure every user story depends on to know who is calling

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational ⚠️

- [ ] T002 [P] Unit tests for `hash_password`/`verify_password` — hash differs from plaintext, verification succeeds for the correct password and fails for an incorrect one — in `tests/unit/test_auth_passwords.py`
- [ ] T003 [P] Unit tests for `issue_session_token`/`decode_session_token` — round-trip decode returns the original `sub`/`role`, an expired token is rejected, a tampered token is rejected — in `tests/unit/test_auth_tokens.py`
- [ ] T004 [P] Contract tests for `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` — valid login sets the session cookie and returns `{role, display_name}`, invalid credentials return a single generic 401 message, `GET /auth/me` returns 401 with no/expired cookie, logout clears the session — in `tests/contract/test_auth_routes.py`

### Implementation for Foundational

- [ ] T005 Create the `UserAccount` Pydantic v2 model (`id`, `username`, `password_hash`, `role`, `display_name`) in `src/models/user_account.py` per data-model.md
- [ ] T006 [P] Implement `hash_password(password: str) -> str` / `verify_password(password: str, password_hash: str) -> bool` in `src/services/auth/passwords.py` (research.md §2, bcrypt) (depends on T002, T001)
- [ ] T007 [P] Implement `issue_session_token(user: UserAccount) -> str` / `decode_session_token(token: str) -> SessionClaims | None` in `src/services/auth/tokens.py` (research.md §1-2, pyjwt HS256, `exp` claim, secret from an environment variable) (depends on T003, T001, T005)
- [ ] T008 Implement `UserRepository` (SQLite-backed, following `ClaimRepository`'s `Table`/engine pattern, seeded with a handful of employee accounts plus one HR account per research.md §5) in `src/repositories/user_repository.py` (depends on T005, T006)
- [ ] T009 Implement FastAPI dependencies `get_current_user`, `require_employee`, `require_hr` (read the session cookie, decode via T007, load via T008, raise 401/403 as appropriate) in `src/api/dependencies.py` (depends on T007, T008)
- [ ] T010 Implement `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` in `src/api/auth_routes.py` per contracts/auth-employees-api.yaml (depends on T004, T006, T007, T008, T009)
- [ ] T011 Register the `auth_routes` router on the FastAPI app in `src/api/main.py` (depends on T010)
- [ ] T012 [P] Add `credentials: 'include'` to the `fetch` call in the typed API client so the session cookie is sent on every request, in `frontend/src/lib/apiClient.ts`
- [ ] T013 [P] Implement `login`, `logout`, and a `useSession()` TanStack Query hook wrapping `GET /auth/me` in `frontend/src/lib/authClient.ts` per contracts/ui-contract.md
- [ ] T014 Implement `<RequireRole role="employee" | "hr">` route guard (redirects to `/login` when unauthenticated, to the caller's own portal root on a role mismatch, renders children on match) in `frontend/src/components/RequireRole.tsx` per contracts/ui-contract.md (depends on T013)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Employee and HR Each Sign In to Their Own Portal (Priority: P1) 🎯 MVP

**Goal**: A sign-in screen gates every screen; a successful sign-in routes to the correct portal for the account's role; a session persists across reload and ends on sign-out or expiry.

**Independent Test**: Sign in as an employee and confirm the employee portal (not the HR portal) loads; sign out and sign in as HR and confirm the HR portal (not the employee portal) loads; confirm no screen renders before sign-in.

### Tests for User Story 1 ⚠️

- [ ] T015 [P] [US1] Component test: `<RequireRole>` redirects to `/login` when `useSession()` is `'unauthenticated'`, redirects to the session's own portal root on a role mismatch, and renders its children when the role matches, in `frontend/tests/component/RequireRole.test.tsx` (mocking `useSession`)
- [ ] T016 [P] [US1] Component test: `<LoginPage>` shows one generic error message on a failed sign-in without indicating which field was wrong, and disables its submit control while the request is in flight, in `frontend/tests/component/LoginPage.test.tsx`
- [ ] T017 [P] [US1] Integration test: a successful employee sign-in redirects to `/`, a successful HR sign-in redirects to `/hr`, in `frontend/tests/integration/loginRedirect.test.tsx`

### Implementation for User Story 1

- [ ] T018 [US1] Implement `<LoginPage>` (username/password form, calls `authClient.login`, redirects by the returned role, shows the generic error from T016) in `frontend/src/pages/LoginPage.tsx` (depends on T013, T014)
- [ ] T019 [US1] Add the `/login` route and gate the app shell on `useSession()` (redirect to `/login` when unauthenticated) in `frontend/src/App.tsx` (depends on T018)
- [ ] T020 [US1] Add a sign-out action (calls `authClient.logout`, redirects to `/login`) to the shared nav in `frontend/src/App.tsx` (depends on T019)

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP (sign-in/out and role routing work, verifiable via T015-T017 even before US2/US3's own protected pages exist).

---

## Phase 4: User Story 2 - Employee Submits Claims and Tracks Their Status (Priority: P1)

**Goal**: The existing new-claim and claim-history experience is unchanged, now reachable only after employee sign-in and using the authenticated session's identity instead of a hardcoded constant.

**Independent Test**: Sign in as an employee, submit a claim, confirm it appears in that employee's claim history with its current status exactly as before this feature, and confirm `/hr` is unreachable.

### Tests for User Story 2 ⚠️

- [ ] T021 [P] [US2] Extend contract tests for `POST /claims` and `GET /claims` asserting `submitter_id` comes from the authenticated session rather than a hardcoded constant, and that a request with no/expired session is rejected, in `tests/contract/test_claims_routes.py`
- [ ] T022 [P] [US2] Integration test: employee sign-in → submit a claim → the claim appears in that employee's own history; a claim submitted under a different signed-in employee does not appear, in `frontend/tests/integration/employeePortalGated.test.tsx`

### Implementation for User Story 2

- [ ] T023 [US2] Replace `CURRENT_EMPLOYEE_ID` with the `require_employee` dependency (T009), sourcing `submitter_id` from the authenticated user, in `src/api/claims_routes.py` (depends on T009)
- [ ] T024 [US2] Wrap the `/` and `/history` routes with `<RequireRole role="employee">` in `frontend/src/App.tsx` (depends on T014, T019)

**Checkpoint**: User Stories 1 AND 2 both work — the employee flow is fully gated and uses real identity.

---

## Phase 5: User Story 3 - HR Reviews an Employee's Claims (Priority: P1)

**Goal**: HR signs in, sees a list of employees who have submitted claims, selects one to see their claims, and can approve, reject (with a required reason), or request clarification on any claim still awaiting a decision.

**Independent Test**: Sign in as HR, select an employee from the employee list, confirm their claims render, and perform each of the three decisions on different claims, confirming each is recorded and reflected correctly.

### Tests for User Story 3 ⚠️

- [ ] T025 [P] [US3] Contract tests for `GET /employees` and `GET /employees/{employeeId}/claims` — HR-only (403 for a non-HR session), 404 for an unknown employee, list scoped to employees with at least one claim — in `tests/contract/test_employees_routes.py`
- [ ] T026 [P] [US3] Extend contract tests for `POST /claims/{claimId}/decisions` asserting `reviewer_id` comes from the authenticated HR session rather than a hardcoded constant, and that a non-HR session is rejected with 403, in `tests/contract/test_review_routes.py`
- [ ] T027 [P] [US3] Integration test: HR flow — employee list renders, selecting an employee shows their claims, rejecting without a reason is blocked, rejecting with a reason updates the claim's status and removes its decision controls, in `frontend/tests/integration/hrReviewFlow.test.tsx`
- [ ] T028 [P] [US3] Integration test: two concurrent decision attempts on the same claim — the second shows an "already decided" message and does not change the outcome of the first, in `frontend/tests/integration/hrConcurrentDecision.test.tsx`
- [ ] T029 [P] [US3] Component test: `<EmployeeListPage>` and `<EmployeeClaimsPage>` each render a clear empty state when there is no data, in `frontend/tests/component/EmployeeEmptyStates.test.tsx`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `GET /employees` (distinct submitters with at least one claim, joined to `UserAccount` for display name, research.md §4) gated by `require_hr`, in `src/api/employees_routes.py` (depends on T009)
- [ ] T031 [US3] Implement `GET /employees/{employeeId}/claims` gated by `require_hr`, in `src/api/employees_routes.py` (depends on T030)
- [ ] T032 [US3] Register the `employees_routes` router on the app in `src/api/main.py` (depends on T031)
- [ ] T033 [US3] Replace `CURRENT_REVIEWER_ID` with the `require_hr` dependency (T009), sourcing `reviewer_id` from the authenticated user, in `src/api/review_routes.py` (depends on T009)
- [ ] T034 [P] [US3] Implement `<ReviewDecisionControls>` (approve / reject-with-required-reason / request-clarification, 409 "already decided" handling) in `frontend/src/components/ReviewDecisionControls.tsx` per contracts/ui-contract.md
- [ ] T035 [US3] Implement `<EmployeeListPage>` (fetches `GET /employees`, empty state) in `frontend/src/pages/EmployeeListPage.tsx` (depends on T030)
- [ ] T036 [US3] Implement `<EmployeeClaimsPage>` (fetches `GET /employees/{id}/claims`, renders via the existing `<ClaimHistoryList>` from `002` unmodified, shows `<ReviewDecisionControls>` only for claims in a decidable status, empty state) in `frontend/src/pages/EmployeeClaimsPage.tsx` (depends on T031, T034)
- [ ] T037 [US3] Add `/hr` and `/hr/employees/:employeeId` routes wrapped with `<RequireRole role="hr">` in `frontend/src/App.tsx` (depends on T014, T035, T036)

**Checkpoint**: User Stories 1, 2, AND 3 all work — the full authentication and HR review loop is functional.

---

## Phase 6: User Story 4 - The Employee Portal Looks Polished, Not Cramped (Priority: P3)

**Goal**: Consistent margin/spacing around content on the employee-facing screens at both desktop and mobile widths.

**Independent Test**: Visually inspect the new-claim and claim-history screens at desktop and ~375px widths and confirm content is no longer flush against viewport/container edges.

### Implementation for User Story 4

- [X] T038 [P] [US4] Increase page/section margin and spacing on `frontend/src/pages/NewClaimPage.tsx`, `frontend/src/pages/ClaimHistoryPage.tsx`, and the shared nav container in `frontend/src/App.tsx` so content is never flush against viewport/container edges, at both desktop and ~375px widths (FR-015)

**Checkpoint**: All 4 user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Confirms the full feature end-to-end and closes out constitution/spec obligations that span all stories

- [ ] T039 [P] Document the seeded development credentials (employee and HR seed account usernames/passwords) in `frontend/README.md`'s "Running against the real backend" section and in the root `README.md`
- [ ] T040 Execute `specs/004-auth-hr-review-portal/quickstart.md` Scenarios 1-7 end-to-end against the running backend and frontend, and record results
- [ ] T041 Run the full backend suite (`pytest tests/`) and linters (`ruff check src tests`, `black --check src tests`), and the full frontend suite (`npm test` in `frontend/`) and linters (`npm run lint`, `npx tsc -b` in `frontend/`), confirming 100% pass per constitution Article II.2

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 has no dependency on US2/US3/US4
  - US2 depends on Foundational's `require_employee`-ready dependencies and `<RequireRole>`/`/login` routing from US1 (T019) to wrap its routes, but its own claim-submission logic is otherwise independently testable
  - US3 depends on Foundational and on US1's `<RequireRole>`/`/login` routing (T019) to wrap its routes, but is otherwise independent of US2
  - US4 has no dependency on US2/US3 — it only edits existing employee pages' styling
- **Polish (Phase 7)**: Depends on all four user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational; needs US1's `/login` route and app-shell gating (T019) to wrap its routes with `<RequireRole>`, but its backend identity change (T023) is independent of US1
- **User Story 3 (P1)**: Can start after Foundational; needs US1's `/login` route/gating (T019) for the same reason as US2, but is otherwise independent of US2
- **User Story 4 (P3)**: Can start after Foundational - purely a styling edit to existing pages, no dependency on US1/US2/US3

### Within Each User Story

- Tests written before implementation tasks (write, confirm they fail, then implement)
- Backend identity/route changes before frontend pages that call them
- Story complete and checkpointed before moving to the next priority

### Parallel Opportunities

- T002, T003, T004 (Foundational tests) can run in parallel
- T006, T007 can run in parallel once T001/T002/T003/T005 land; T012, T013 can run in parallel with the backend foundational tasks
- All US1 test tasks (T015-T017) can run in parallel
- T021, T022 (US2 tests) can run in parallel
- T025-T029 (all US3 tests) can run in parallel; T034 (ReviewDecisionControls) can run in parallel with US3's backend tasks (T030-T033)
- T038 (US4) can run in parallel with any other story once Foundational is done
- T039 can run in parallel with T040/T041 authoring, though it should land before T040's credential-dependent walkthrough

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Component test: RequireRole redirect/role-mismatch/match behavior in frontend/tests/component/RequireRole.test.tsx"
Task: "Component test: LoginPage generic error + in-flight disabling in frontend/tests/component/LoginPage.test.tsx"
Task: "Integration test: employee/HR sign-in redirects to the correct portal in frontend/tests/integration/loginRedirect.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run quickstart.md Scenario 1 and confirm sign-in/out and role-based redirect work
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → identity/session infrastructure ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP: sign-in works, routes to the right portal shell)
3. Add User Story 2 → Test independently (quickstart.md Scenario 2) → Deploy/Demo (employee flow gated and using real identity)
4. Add User Story 3 → Test independently (quickstart.md Scenarios 3-6) → Deploy/Demo (HR can finally act on claims)
5. Add User Story 4 → quickstart.md Scenario 7 → Deploy/Demo (visual polish)
6. Polish phase → full end-to-end pass

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (owns `LoginPage`/`/login` routing)
   - Developer B: User Story 2's backend identity change (T023, independent of US1's frontend work) plus its tests
   - Developer C: User Story 3's backend (`employees_routes.py`, T033) and `<ReviewDecisionControls>` (T034), which don't depend on US1's frontend routing
   - Developer D: User Story 4 (fully independent styling pass)
3. Once US1's `/login`/`<RequireRole>` routing (T019) lands, US2's and US3's route-wrapping tasks (T024, T037) integrate quickly

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2's T024 and US3's T037 both edit `frontend/src/App.tsx` after US1's T019/T020 create it — sequence these edits rather than running them as true parallel file edits, even though the three stories are independently testable in isolation
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
