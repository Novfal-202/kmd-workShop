---

description: "Task list template for feature implementation"
---

# Tasks: Case-Insensitive Expense Category Matching

**Input**: Design documents from `/specs/003-case-insensitive-categories/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md (all present)

**Tests**: Included. The plan's Constitution Check (Article II.1, adapted) commits to a casing-mismatch test case for each affected rule plus a dedicated unit test suite for the new `PolicyRuleSet` matching methods, enforced in this phase.

**Organization**: Tasks are grouped by user story (spec.md priorities P1/P2) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Paths are relative to the repository root; this feature only touches the existing `001-expense-policy-engine` backend (`src/`, `tests/`) — `frontend/` (002) is unaffected.

## Path Conventions

Single project (existing `001-expense-policy-engine` backend, unchanged layering):

```text
src/models/policy_rule_set.py
src/services/policy_engine/evaluate_claim.py
tests/unit/
```

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: The shared case-insensitive normalization rule both user stories build on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 Add a private `_normalize_category(value: str) -> str` helper (returns `value.casefold()`, research.md §2) to `PolicyRuleSet` in `src/models/policy_rule_set.py` — the single place both `get_category_cap` and `is_weekend_exempt` will call, so the casing rule itself is defined exactly once (FR-003)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 2: User Story 1 - Claim Category Is Matched Regardless of Casing (Priority: P1) 🎯 MVP

**Goal**: A claim's category matches its configured spending cap regardless of the casing used at submission time, while categories with no configured cap under any casing still correctly route to manual review.

**Independent Test**: Configure a cap for a category using one casing (e.g. "Meals"), submit claims for that category using different casings (e.g. "meals", "MEALS"), and confirm each is evaluated against the configured cap rather than flagged as uncapped; confirm a category with no configured cap under any casing is still flagged as uncapped.

### Tests for User Story 1 ⚠️

- [X] T002 [P] [US1] Unit tests for `PolicyRuleSet.get_category_cap` — exact-case match, differing-case match (e.g. "meals" vs "Meals", "MEALS" vs "Meals"), and no match under any casing returns `None` — in `tests/unit/test_policy_rule_set_matching.py` (depends on T001)
- [X] T003 [P] [US1] Extend `tests/unit/test_evaluate_claim_cap.py` with a casing-mismatch case: a claim submitted with a differently-cased category than the configured cap is still evaluated against that cap (over-cap and within-cap sub-cases)
- [X] T004 [P] [US1] Extend `tests/unit/test_evaluate_claim_uncapped.py` with a case confirming a category with no configured cap under any casing (e.g. "Supplies"/"supplies") still produces the `uncapped_category` violation (FR-004)

### Implementation for User Story 1

- [X] T005 [US1] Implement `PolicyRuleSet.get_category_cap(category: str) -> Decimal | None` in `src/models/policy_rule_set.py`, matching `category` against `self.category_caps` via `_normalize_category` on both sides (depends on T001)
- [X] T006 [US1] Update `evaluate_claim`'s `over_category_cap`/`uncapped_category` check (checks 1 & 2) in `src/services/policy_engine/evaluate_claim.py` to call `rule_set.get_category_cap(claim.category)` in place of `rule_set.category_caps.get(claim.category)` (depends on T005)

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP.

---

## Phase 3: User Story 2 - Consistent Category Matching Across All Policy Lookups (Priority: P2)

**Goal**: The weekend-exemption lookup (and, by the same pattern, any future category-keyed policy lookup) applies the identical case-insensitive rule as spending caps, so no lookup is left case-sensitive while another is fixed.

**Independent Test**: Configure a category as weekend-exempt using one casing, submit a weekend-dated claim for that category using a different casing, and confirm it is correctly treated as exempt.

### Tests for User Story 2 ⚠️

- [X] T007 [P] [US2] Unit tests for `PolicyRuleSet.is_weekend_exempt` — exact-case match, differing-case match, and a non-exempt category returns `False` — in `tests/unit/test_policy_rule_set_matching.py` (depends on T001; sequenced after T002 since both add to the same new file, per Notes)
- [X] T008 [P] [US2] Extend `tests/unit/test_evaluate_claim_weekend.py` with a casing-mismatch case: a weekend-dated claim submitted with a differently-cased exempt category produces no `weekend_policy_violation`

### Implementation for User Story 2

- [X] T009 [US2] Implement `PolicyRuleSet.is_weekend_exempt(category: str) -> bool` in `src/models/policy_rule_set.py`, matching `category` against `self.weekend_exempt_categories` via `_normalize_category` on both sides (depends on T001; sequenced after T005 since both add methods to the same file, per Notes)
- [X] T010 [US2] Update `evaluate_claim`'s `weekend_policy_violation` check (check 4) in `src/services/policy_engine/evaluate_claim.py` to call `rule_set.is_weekend_exempt(claim.category)` in place of `claim.category not in rule_set.weekend_exempt_categories` (depends on T009; sequenced after T006 since both edit the same file, per Notes)

**Checkpoint**: Both user stories are independently functional — every category-keyed policy lookup now shares the same case-insensitive rule.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Confirms the fix end-to-end and closes out constitution/spec obligations that span both stories

- [X] T011 [P] Add a regression test asserting `evaluate_claim`'s violation `detail` strings and the claim's `category` field retain the exact casing the claim was submitted with, even when a differently-cased match was found internally (FR-005), in `tests/unit/test_evaluate_claim_cap.py` or a new `tests/unit/test_evaluate_claim_category_casing_preserved.py`
- [X] T012 Execute `specs/003-case-insensitive-categories/quickstart.md` Scenarios 1-4 against a running instance of the backend and record results
- [X] T013 Run the full suite (`pytest tests/unit`) and the configured linters (`ruff check src tests`, `black --check src tests`) and confirm 100% pass per constitution Article II.2

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies - BLOCKS all user stories
- **User Stories (Phase 2-3)**: Both depend on Foundational phase completion
  - US1 has no dependency on US2
  - US2 does not depend on US1's cap-matching behavior, but both stories add methods to the same `src/models/policy_rule_set.py` file and both edit `src/services/policy_engine/evaluate_claim.py` — sequence US2's file edits after US1's (see Notes)
- **Polish (Phase 4)**: Depends on both user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on User Story 2
- **User Story 2 (P2)**: Can start after Foundational (Phase 1); independently testable via `is_weekend_exempt` in isolation, but its edits to `policy_rule_set.py`/`evaluate_claim.py` are sequenced after US1's (same files)

### Within Each User Story

- Tests written before implementation tasks (write, confirm they fail, then implement)
- `PolicyRuleSet` method before its `evaluate_claim` call-site update
- Story complete and checkpointed before moving to the next priority

### Parallel Opportunities

- T002, T003, T004 (all US1 test tasks) can run in parallel
- T007, T008 (all US2 test tasks) can run in parallel with each other, and with T002-T004 for authoring purposes, though T007 lands in the same new file as T002 (sequence the actual file edit, per Notes)
- T011 (Polish regression test) can run in parallel with T012/T013 authoring, though it should land before T013's full-suite run

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit tests for PolicyRuleSet.get_category_cap in tests/unit/test_policy_rule_set_matching.py"
Task: "Extend test_evaluate_claim_cap.py with a casing-mismatch case"
Task: "Extend test_evaluate_claim_uncapped.py with a still-uncapped-under-any-casing case"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational
2. Complete Phase 2: User Story 1
3. **STOP and VALIDATE**: Run quickstart.md Scenarios 1 and 3 against User Story 1 independently
4. Deploy/demo if ready — this alone fixes the reported bug for spending caps

### Incremental Delivery

1. Complete Foundational → shared normalization rule ready
2. Add User Story 1 → Test independently → Deploy/Demo (fixes the reported `uncapped_category` bug)
3. Add User Story 2 → Test independently (quickstart.md Scenario 2) → Deploy/Demo (closes the weekend-exemption gap too)
4. Polish phase → quickstart.md Scenario 4 and full end-to-end pass

### Parallel Team Strategy

With multiple developers:

1. Team completes Foundational together (it's one small task, T001)
2. Once Foundational is done:
   - Developer A: User Story 1 (`get_category_cap` + its `evaluate_claim` call site)
   - Developer B: prepares User Story 2's test suite against the not-yet-added `is_weekend_exempt`, then integrates once T001 lands and coordinates the shared-file edits with Developer A
3. Stories complete and integrate independently, with US2's shared-file edits sequenced after US1's

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US2 both add methods to `src/models/policy_rule_set.py` and both edit
  `src/services/policy_engine/evaluate_claim.py` after Foundational creates/updates those files —
  sequence these two stories' edits (T005/T006 before T009/T010) rather than running them as true
  parallel file edits, even though they are independently testable in isolation. The same applies
  to `tests/unit/test_policy_rule_set_matching.py` (T002 before T007) since both stories add test
  functions to the same new file.
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
