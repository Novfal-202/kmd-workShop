---

description: "Task list template for feature implementation"
---

# Tasks: Corporate Expense Reimbursement & Policy Engine

**Input**: Design documents from `specs/001-expense-policy-engine/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. Constitution Article II.1 requires a synthetic test case for every business policy rule, and II.2 requires 100% pass of deterministic unit tests before code is accepted — tests are therefore mandatory for this feature, not optional.

**Organization**: Tasks are grouped by user story (spec.md priorities P1/P2/P3) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every description

## Path Conventions

Single-project backend per `plan.md`: `src/models/`, `src/services/policy_engine/`, `src/repositories/`, `src/api/` at repository root; `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/fixtures/` (fixture already generated).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create the project directory structure per `plan.md`: `src/models/`, `src/services/policy_engine/`, `src/repositories/`, `src/api/`, `tests/unit/`, `tests/contract/`, `tests/integration/` (leave `tests/fixtures/synthetic_expenses.json` as-is)
- [X] T002 Initialize the Python 3.11+ project with `pyproject.toml` declaring dependencies: `fastapi`, `pydantic>=2`, `uvicorn`, `sqlalchemy` (or equivalent SQLite access), `pytest`
- [X] T003 [P] Configure `ruff` and `black` (or equivalent) linting/formatting config in `pyproject.toml`, satisfying constitution Article II.2's "static linters" requirement
- [X] T004 [P] Implement the SQLite dev database connection/session helper in `src/repositories/db.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create the `ExpenseClaim`, `ExpenseClaimInput`, and `ViolationReason` Pydantic v2 models in `src/models/expense_claim.py`, including the `status` enum (`auto_approved`, `pending_review`, `approved`, `rejected`, `needs_information`, `withdrawn`) and the `ViolationReason.code` enum from `data-model.md`
- [X] T006 [P] Create the `PolicyRuleSet` Pydantic v2 model in `src/models/policy_rule_set.py` (`category_caps`, `receipt_required_threshold`, `auto_approval_threshold`, `weekend_exempt_categories`, `late_submission_days`)
- [X] T007 [P] Create the `ReviewDecision` Pydantic v2 model in `src/models/review_decision.py`
- [X] T008 [P] Create the `AuditLogEntry` Pydantic v2 model in `src/models/audit_log_entry.py`
- [X] T009 Implement `ClaimRepository` in `src/repositories/claim_repository.py`: `create`, `get`, `list_by_employee`, `list_review_queue`, and an atomic `try_transition(claim_id, allowed_from_statuses, to_status, mutation)` method that performs a single conditional `UPDATE ... WHERE status IN (allowed_from_statuses)` — the shared first-write-wins primitive both US2's decisions and US3's withdrawal rely on for FR-019 (depends on T005, T007)
- [X] T010 [P] Implement `AuditRepository` (append-only inserts, no updates/deletes) in `src/repositories/audit_repository.py` (depends on T008)
- [X] T011 Implement the audit-entry builder in `src/services/policy_engine/audit_trail.py`, turning an evaluation result into an `AuditLogEntry` per FR-017 (depends on T008)
- [X] T012 [P] Create the FastAPI app skeleton and a `ValidationError` exception handler (mapping domain validation errors to HTTP 422/403/409 per `contracts/api.yaml`) in `src/api/main.py`
- [X] T013 [P] Seed the default `PolicyRuleSet` (example values from `research.md` §5: Meals cap $50.00, receipt-required threshold $100.00, auto-approval threshold $200.00, Travel/Lodging weekend-exempt) via `src/repositories/policy_rule_set_repository.py` (depends on T006)

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Employee Submits an Expense Claim and Gets an Instant Decision (Priority: P1) 🎯 MVP

**Goal**: An employee submits a claim and immediately receives either an auto-approval or a "pending review" status with specific violation reason(s).

**Independent Test**: Submit a claim under the auto-approval threshold with a valid receipt on a weekday and confirm instant auto-approval; submit a claim that violates a rule and confirm it is flagged with the correct reason(s).

### Tests for User Story 1 ⚠️

> Write these tests FIRST; ensure they FAIL before implementation (T025 onward)

- [X] T014 [P] [US1] Unit test `over_category_cap` rule (FR-002) in `tests/unit/test_evaluate_claim_cap.py`
- [X] T015 [P] [US1] Unit test `missing_required_receipt` rule (FR-003) in `tests/unit/test_evaluate_claim_receipt.py`
- [X] T016 [P] [US1] Unit test `weekend_policy_violation` rule, including exempt categories (FR-004) in `tests/unit/test_evaluate_claim_weekend.py`
- [X] T017 [P] [US1] Unit test the auto-approval decision rule, including `exceeds_auto_approval_threshold` (FR-005, FR-006) in `tests/unit/test_evaluate_claim_auto_approval.py`
- [X] T018 [P] [US1] Unit test `possible_duplicate` rule (FR-013) in `tests/unit/test_evaluate_claim_duplicate.py`
- [X] T019 [P] [US1] Unit test `late_submission` rule, 90-day window (spec Edge Cases) in `tests/unit/test_evaluate_claim_late_submission.py`
- [X] T020 [P] [US1] Unit test `uncapped_category` routing to manual review (FR-015) in `tests/unit/test_evaluate_claim_uncapped.py`
- [X] T021 [P] [US1] Unit test compound-violation reporting — multiple simultaneous violations all recorded together (spec Edge Cases) in `tests/unit/test_evaluate_claim_compound.py`
- [X] T022 [P] [US1] Unit test the `ExpenseClaimInput` validation boundary — zero/negative amount, malformed date, missing category, SQL-injection-style description treated as opaque text (FR-014) in `tests/unit/test_expense_claim_input_validation.py`
- [X] T023 [P] [US1] Contract test `POST /claims`, `GET /claims/{claimId}`, `PUT /claims/{claimId}` against `contracts/api.yaml` in `tests/contract/test_claims_routes.py`
- [X] T024 [US1] Integration test replaying all 20 claims in `tests/fixtures/synthetic_expenses.json`, asserting actual `status`/`violations` match each claim's `expected_status`/`expected_violations` (depends on T014-T023)

### Implementation for User Story 1

- [X] T025 [US1] Implement `evaluate_claim` pure function (checks 1–7 from `contracts/policy-engine-contract.md`) in `src/services/policy_engine/evaluate_claim.py` (depends on T005, T006, T011)
- [X] T026 [US1] Implement `POST /claims` (submit claim, run `evaluate_claim`, persist via `ClaimRepository`, write `AuditLogEntry` via `AuditRepository`) in `src/api/claims_routes.py` (depends on T009, T010, T025)
- [X] T027 [US1] Implement `GET /claims/{claimId}` in `src/api/claims_routes.py` (depends on T009)
- [X] T028 [US1] Implement `PUT /claims/{claimId}` (edit claim, re-run `evaluate_claim` per FR-016) in `src/api/claims_routes.py` (depends on T025, T026)
- [X] T029 [US1] Implement `GET /claims/{claimId}/audit-trail` (FR-017) in `src/api/claims_routes.py` (depends on T010)
- [X] T030 [US1] Register the claims router on the FastAPI app in `src/api/main.py` (depends on T012, T026-T029)

**Checkpoint**: User Story 1 is fully functional and independently testable — claims can be submitted and get instant, correct decisions.

---

## Phase 4: User Story 2 - Finance/Auditor Reviews Flagged Claims (Priority: P2)

**Goal**: A reviewer sees flagged claims with their violation reasons and can approve, reject, or request more information, with segregation-of-duties and concurrency-safety guarantees.

**Independent Test**: Open the review queue, inspect a flagged claim's reasons, approve it, and confirm the status/reviewer/timestamp are recorded; confirm self-review is blocked and a concurrent second decision is rejected.

### Tests for User Story 2 ⚠️

- [X] T031 [P] [US2] Unit test `apply_review_decision` approve/reject/needs_information transitions (FR-008, FR-010) in `tests/unit/test_review_workflow_decisions.py`
- [X] T032 [P] [US2] Unit test FR-009 — rejection requires a non-empty reason in `tests/unit/test_review_workflow_reject_reason.py`
- [X] T033 [P] [US2] Unit test FR-018 — reviewer cannot decide on their own submitted claim in `tests/unit/test_review_workflow_self_review.py`
- [X] T034 [P] [US2] Unit test FR-019 — `ClaimRepository.try_transition` first-write-wins: a second conditional update on an already-transitioned claim affects zero rows in `tests/unit/test_claim_repository_concurrency.py`
- [X] T035 [P] [US2] Contract test `GET /review-queue`, `POST /claims/{claimId}/decisions` (including 403 and 409 responses) against `contracts/api.yaml` in `tests/contract/test_review_routes.py`
- [X] T036 [US2] Integration test for the full reviewer flow — queue listing (US2 Acceptance Scenario 1), approve, reject without reason (422), self-review attempt (403), concurrent decisions (one 200 + one 409) in `tests/integration/test_review_workflow.py` (depends on T031-T035)

### Implementation for User Story 2

- [X] T037 [US2] Implement `apply_review_decision` pure function (FR-008, FR-009, FR-010, FR-018) in `src/services/policy_engine/review_workflow.py` (depends on T005, T007)
- [X] T038 [US2] Implement `GET /review-queue` in `src/api/review_routes.py` (depends on T009)
- [X] T039 [US2] Implement `POST /claims/{claimId}/decisions`, wiring `apply_review_decision` + `ClaimRepository.try_transition` (FR-019) + employee notification (FR-011) in `src/api/review_routes.py` (depends on T009, T037)
- [X] T040 [US2] Implement the employee notification dispatch stub for claim status-change events (FR-011), riding the existing notification channel per spec Assumptions, in `src/services/notifications.py`
- [X] T041 [US2] Register the review router on the FastAPI app in `src/api/main.py` (depends on T012, T038, T039)

**Checkpoint**: User Stories 1 AND 2 both work independently — the full submit → flag → review loop is functional.

---

## Phase 5: User Story 3 - Employee Tracks Claim Status and History (Priority: P3)

**Goal**: An employee views their claim history with current status/reasons, and can withdraw a claim still awaiting review.

**Independent Test**: Submit several claims with different outcomes, confirm the employee's history view reflects each claim's status/reasons, then withdraw a pending claim and confirm it leaves the review queue and shows as "withdrawn" in history.

### Tests for User Story 3 ⚠️

- [X] T042 [P] [US3] Unit test `withdraw_claim` transition and its FR-019 race guard against a concurrent reviewer decision in `tests/unit/test_withdrawal.py`
- [X] T043 [P] [US3] Contract test `GET /claims` (list) and `POST /claims/{claimId}/withdraw` (including 409 response) against `contracts/api.yaml` in `tests/contract/test_claim_history_routes.py`
- [X] T044 [US3] Integration test for employee claim history — reflects reviewer decisions without further employee action (US3 Acceptance Scenario 2) and reflects a withdrawal (US3 Acceptance Scenario 3) in `tests/integration/test_claim_history.py` (depends on T042, T043)

### Implementation for User Story 3

- [X] T045 [US3] Implement `withdraw_claim` pure function (FR-020) in `src/services/policy_engine/withdrawal.py` (depends on T005)
- [X] T046 [US3] Implement `GET /claims` (employee's own claim history, FR-012) in `src/api/claims_routes.py` (depends on T009)
- [X] T047 [US3] Implement `POST /claims/{claimId}/withdraw`, wiring `withdraw_claim` + `ClaimRepository.try_transition` (FR-019/FR-020) in `src/api/claims_routes.py` (depends on T009, T045)

**Checkpoint**: All user stories are now independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T048 [P] Walk through every step of `quickstart.md` against the running service and record the results
- [X] T049 [P] Add structured logging for claim evaluations and review decisions across `src/api/` and `src/services/policy_engine/`
- [X] T050 Run the full suite (`pytest tests/unit tests/contract tests/integration`) and the configured linter, and confirm 100% pass per constitution Article II.2
- [X] T051 [P] Write `README.md` with setup/run instructions that reference `quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational completion; can then proceed in parallel or in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on other stories. Produces flagged claims that US2 and US3 consume, but is independently testable via direct submission (T024's fixture replay needs no reviewer or history feature).
- **User Story 2 (P2)**: Independently testable given any flagged claim (can be seeded directly in tests without going through the US1 HTTP endpoint). Shares `ClaimRepository.try_transition` (T009, Foundational) with US3 but has no code dependency on US3.
- **User Story 3 (P3)**: Independently testable given any claim in any status (can be seeded directly). Shares `ClaimRepository.try_transition` (T009) with US2 but has no code dependency on US2.

### Within Each User Story

- Tests (T014-T024, T031-T036, T042-T044) MUST be written and FAIL before their corresponding implementation tasks
- Pure business-logic functions (`evaluate_claim`, `apply_review_decision`, `withdraw_claim`) before the API routes that call them
- Routes before router registration in `src/api/main.py`

### Parallel Opportunities

- All Setup tasks marked [P] (T003, T004) can run in parallel after T001-T002
- All Foundational model tasks marked [P] (T005-T008) can run in parallel; T009-T013 depend on one or more of them
- Once Foundational (Phase 2) completes, US1, US2, and US3 test-writing can start in parallel across developers (implementation tasks within a story still follow the pure-function-before-route order above)
- All [P] tasks within a story's Tests subsection can run in parallel with each other

---

## Parallel Example: User Story 1

```bash
# Launch all rule unit tests for User Story 1 together:
Task: "Unit test over_category_cap rule (FR-002) in tests/unit/test_evaluate_claim_cap.py"
Task: "Unit test missing_required_receipt rule (FR-003) in tests/unit/test_evaluate_claim_receipt.py"
Task: "Unit test weekend_policy_violation rule (FR-004) in tests/unit/test_evaluate_claim_weekend.py"
Task: "Unit test auto-approval decision rule (FR-005, FR-006) in tests/unit/test_evaluate_claim_auto_approval.py"
Task: "Unit test possible_duplicate rule (FR-013) in tests/unit/test_evaluate_claim_duplicate.py"
Task: "Unit test late_submission rule in tests/unit/test_evaluate_claim_late_submission.py"
Task: "Unit test uncapped_category routing (FR-015) in tests/unit/test_evaluate_claim_uncapped.py"
Task: "Unit test compound-violation reporting in tests/unit/test_evaluate_claim_compound.py"
Task: "Unit test ExpenseClaimInput validation boundary (FR-014) in tests/unit/test_expense_claim_input_validation.py"
Task: "Contract test claims routes against contracts/api.yaml in tests/contract/test_claims_routes.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run T014-T024, confirm the fixture replay (T024) passes for all 20 synthetic claims
5. Deploy/demo if ready — a working submit-and-decide loop, even with no reviewer UI, already demonstrates SC-001 through SC-004

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 → validate independently → demo (MVP)
3. Add User Story 2 → validate independently → demo (flagged claims now get resolved)
4. Add User Story 3 → validate independently → demo (employees get visibility and control)
5. Polish (Phase 6) → run `quickstart.md` end-to-end, confirm constitution Article II.2 compliance

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (Foundational tasks T005-T008 can be split across developers)
2. Once Foundational is done:
   - Developer A: User Story 1 (T014-T030)
   - Developer B: User Story 2 (T031-T041) — can seed flagged claims directly in tests without waiting on US1's HTTP endpoint
   - Developer C: User Story 3 (T042-T047) — can seed claims directly in tests without waiting on US1/US2
3. Stories integrate through the shared `ClaimRepository`/models built in Foundational

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Tests must be written and confirmed failing before their implementation tasks
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
- `tests/fixtures/synthetic_expenses.json` (20 claims, 5/5/5/5 partitions) already exists and is consumed by T024; no fixture-generation task is needed
