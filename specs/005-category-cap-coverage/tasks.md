---

description: "Task list template for feature implementation"
---

# Tasks: Category Cap Coverage

**Input**: Design documents from `/specs/005-category-cap-coverage/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md (all present; no contracts/ — this feature changes no API surface)

**Tests**: Included. The plan's Constitution Check (Article II.1, adapted) commits to a test case per newly-capped category, enforced in this phase.

**Organization**: Single user story (spec.md priority P1) — no Setup or Foundational phase is needed since this feature adds no dependency, model, or infrastructure, only three configuration values.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 (this feature's only user story)
- Paths are relative to the repository root; this feature only touches the existing `001-expense-policy-engine` backend (`src/`, `tests/`) — `frontend/` (002) is unaffected.

## Path Conventions

```text
src/repositories/policy_rule_set_repository.py
tests/unit/
```

---

## Phase 1: User Story 1 - Every Portal Category Has a Decided Spending Cap (Priority: P1) 🎯 MVP

**Goal**: Every category the portal's claim form offers (Meals, Travel, Lodging, Supplies, Entertainment) has a configured, non-zero spending cap, so none of them can only ever produce an `uncapped_category` violation.

**Independent Test**: Submit a modest, policy-compliant claim in each of the portal's 5 offered categories and confirm each is evaluated against a real cap (auto-approved or over-cap-flagged with the specific cap amount), never merely "uncapped."

### Tests for User Story 1 ⚠️

- [X] T001 [P] [US1] Extend `tests/unit/test_evaluate_claim_cap.py` with within-cap and over-cap cases for `Lodging` (cap $300.00), `Supplies` (cap $100.00), and `Entertainment` (cap $150.00) — asserting `over_category_cap` fires when over, and neither `over_category_cap` nor `uncapped_category` fires when within cap
- [X] T002 [P] [US1] Extend `tests/unit/test_evaluate_claim_uncapped.py` with a regression case confirming a category outside the portal's offered list (e.g. `"Miscellaneous"`) still produces `uncapped_category`, unchanged by this feature (spec Acceptance Scenario 3, FR-005)

### Implementation for User Story 1

- [X] T003 [US1] Add `"Lodging": Decimal("300.00")`, `"Supplies": Decimal("100.00")`, and `"Entertainment": Decimal("150.00")` to `DEFAULT_POLICY_RULE_SET.category_caps` in `src/repositories/policy_rule_set_repository.py`, leaving the existing `Meals`, `Travel`, and `Equipment` entries unchanged (research.md §1, depends on T001/T002 existing first)

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the entire feature (single P1 story).

---

## Phase 2: Polish & Cross-Cutting Concerns

**Purpose**: Confirms the fix end-to-end and closes out constitution obligations

- [X] T004 Execute `specs/005-category-cap-coverage/quickstart.md` Scenarios 1-3 against a running instance of the backend and record results
- [X] T005 Run the full suite (`pytest tests/`) and the configured linters (`ruff check src tests`, `black --check src tests`), confirming 100% pass per constitution Article II.2

---

## Dependencies & Execution Order

### Phase Dependencies

- **User Story 1 (Phase 1)**: No dependencies — this is the entire feature; no Setup/Foundational phase applies
- **Polish (Phase 2)**: Depends on User Story 1 being complete

### Within User Story 1

- Tests (T001, T002) written before the implementation task (T003) — write, confirm they fail (categories still show `uncapped_category`), then implement
- T003 is a single-file, single-dict-literal edit — no sub-dependencies within it

### Parallel Opportunities

- T001 and T002 touch different files and can run in parallel
- T004 and T005 are independent verification passes and can run in either order, though both require T003 complete

---

## Parallel Example: User Story 1

```bash
# Launch both test-extension tasks together:
Task: "Extend test_evaluate_claim_cap.py with Lodging/Supplies/Entertainment cases"
Task: "Extend test_evaluate_claim_uncapped.py with an out-of-scope-category regression case"
```

---

## Implementation Strategy

### MVP First (and only)

1. Complete Phase 1: User Story 1 (T001-T003)
2. **STOP and VALIDATE**: Run quickstart.md Scenario 1 for each of the 3 newly-capped categories
3. Complete Phase 2: Polish (quickstart Scenarios 2-3, full suite + linters)
4. Deploy/demo — this is the entire feature

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Verify tests fail before implementing (both extended test files should show the 3 new categories still hitting `uncapped_category` before T003 lands)
- Commit after each task or logical group
