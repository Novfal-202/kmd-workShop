# Implementation Plan: Case-Insensitive Expense Category Matching

**Branch**: `003-case-insensitive-categories` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-case-insensitive-categories/spec.md`

## Summary

Fix a defect in the `001-expense-policy-engine` backend: `evaluate_claim` matches a claim's
`category` against `PolicyRuleSet.category_caps` and `weekend_exempt_categories` using exact,
case-sensitive comparisons, so a claim's category never matches its configured policy unless the
submitting client happens to use the exact same casing as the policy configuration (e.g. the
`002-expense-portal-ui` frontend sends `"meals"`, the seeded config has `"Meals"` — every claim is
wrongly treated as uncapped). The fix centralizes category matching behind two case-insensitive
lookup methods on `PolicyRuleSet` (`get_category_cap`, `is_weekend_exempt`) so `evaluate_claim`
and any future category-keyed rule share one normalization point, while the claim's stored/
displayed category string is left untouched (FR-005).

## Technical Context

**Language/Version**: Python 3.11+ (unchanged — existing `001` backend)

**Primary Dependencies**: Pydantic v2 (existing `PolicyRuleSet`/`ExpenseClaim` models); no new dependencies

**Storage**: N/A — `PolicyRuleSet` remains the existing in-memory default (`DEFAULT_POLICY_RULE_SET`); this feature does not change how or where policy configuration is stored

**Testing**: pytest (existing suite — `tests/unit/`)

**Target Platform**: Linux/macOS server (unchanged — same FastAPI service as `001`)

**Project Type**: Single project — a targeted fix within the existing `001-expense-policy-engine` backend; no new project, service, or directory

**Performance Goals**: No measurable change — both the case-sensitive and case-insensitive lookups are O(1)/O(n) over a handful of configured categories

**Constraints**: MUST NOT change the category string stored on or returned for a claim (FR-005); MUST NOT add, remove, or change the dollar value of any configured category cap or weekend-exempt entry (spec Assumptions) — this is a matching-logic fix only

**Scale/Scope**: 2 new methods on `PolicyRuleSet`, 2 call-site changes in `evaluate_claim.py`, ~3 currently-configured categories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Requirement | Status | Notes |
|---|---|---|---|
| I.1 | No code without an approved specification | PASS | `spec.md` exists and passed its requirements-quality checklist (16/16, no open `[NEEDS CLARIFICATION]`) before this plan was generated. |
| I.2 | Diffs that violate spec.md or add unrequested scope are rejected | PASS | This plan implements FR-001..FR-005 exactly: case-insensitive matching only. It explicitly does not add/change any category's configured cap or exemption (spec Assumptions), which would be unrequested scope. |
| II.1 | Every business policy rule MUST have a corresponding synthetic test case | PASS (adapted) | This feature doesn't add a new policy rule; it corrects the matching behavior of two existing ones (`over_category_cap`/`uncapped_category`, `weekend_policy_violation`). Its equivalent obligation: each affected rule gets a casing-mismatch test case (spec SC-001/SC-003), plus a dedicated unit test suite for the new `PolicyRuleSet` matching methods themselves. Enforced in Phase 2 tasks. |
| II.2 | Generated code MUST pass 100% of deterministic unit tests and static linters | CARRIED FORWARD | Enforced at implementation/CI time (`pytest`, `ruff`, `black`), not a design-time gate. |
| III.1 | Pure business logic MUST remain decoupled from HTTP/API transport layers | PASS | The new matching methods live on the `PolicyRuleSet` Pydantic model and are called from `evaluate_claim` (already pure, no HTTP/storage imports per its own module docstring); no transport-layer code is touched. |
| III.2 | Models MUST strictly use Pydantic v2 validation contracts | PASS | `PolicyRuleSet` is already a Pydantic v2 `BaseModel`; the new lookup methods are added to that same model, not a parallel ad hoc structure. |

No violations requiring justification — Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-case-insensitive-categories/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/                                        # Existing 001-expense-policy-engine backend
├── models/
│   └── policy_rule_set.py                  # MODIFIED: add get_category_cap(), is_weekend_exempt()
├── services/
│   └── policy_engine/
│       └── evaluate_claim.py               # MODIFIED: call the new methods instead of raw dict/list access
├── repositories/
│   └── policy_rule_set_repository.py       # Unchanged — same DEFAULT_POLICY_RULE_SET values
└── api/                                    # Unchanged — no API surface change

tests/
└── unit/
    ├── test_policy_rule_set_category_matching.py   # NEW: case-insensitive matching unit tests
    ├── test_evaluate_claim_cap.py                   # EXTENDED: casing-mismatch cases
    ├── test_evaluate_claim_uncapped.py              # EXTENDED: still-uncapped-under-any-casing case
    └── test_evaluate_claim_weekend.py               # EXTENDED: casing-mismatch case for exemption
```

**Structure Decision**: Single project (Option 1) — this is a targeted fix inside the existing
`001-expense-policy-engine` backend layering (models → services/policy_engine), touching no other
layer. No new project, service, or directory is introduced; `frontend/` (from `002`) is unaffected
since this fix only changes backend-internal matching logic, not any request/response shape.

## Complexity Tracking

*No violations — table omitted.*
