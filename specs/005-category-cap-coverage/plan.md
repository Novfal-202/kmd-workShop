# Implementation Plan: Category Cap Coverage

**Branch**: `005-category-cap-coverage` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-category-cap-coverage/spec.md`

## Summary

Close a configuration-coverage gap found by `/speckit-analyze`: the portal's claim form offers 5
categories (Meals, Travel, Lodging, Supplies, Entertainment), but the backend's default
`PolicyRuleSet.category_caps` only configures 3 categories (`Meals`, `Travel`, `Equipment`) — none
of which is `Lodging`, `Supplies`, or `Entertainment`. Since `003-case-insensitive-categories`
already made cap lookup case-insensitive, this is purely a *data* gap, not a logic gap: add three
missing entries to `DEFAULT_POLICY_RULE_SET.category_caps`. No code path changes.

## Technical Context

**Language/Version**: Python 3.11+ (unchanged — existing `001` backend)

**Primary Dependencies**: None new — this only edits an existing `Decimal`-valued dict literal in `src/repositories/policy_rule_set_repository.py`

**Storage**: N/A — `PolicyRuleSet` remains the existing in-memory default; this feature only changes its literal values, not how/where it's stored

**Testing**: pytest (existing suite — `tests/unit/`)

**Target Platform**: Linux/macOS server (unchanged — same FastAPI service as `001`)

**Project Type**: Single project — a data-only change within the existing `001-expense-policy-engine` backend

**Performance Goals**: No change — `get_category_cap` (already case-insensitive per `003`) is unaffected in behavior, only in which lookups now succeed

**Constraints**: MUST NOT change the Meals/Travel cap values or remove the Equipment cap (spec FR-004/FR-005) — additive only

**Scale/Scope**: 3 new dict entries in one file; no new models, endpoints, or migrations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Requirement | Status | Notes |
|---|---|---|---|
| I.1 | No code without an approved specification | PASS | `spec.md` exists and passed its requirements-quality checklist (16/16, no open `[NEEDS CLARIFICATION]`) before this plan was generated. |
| I.2 | Diffs that violate spec.md or add unrequested scope are rejected | PASS | This plan implements FR-001..FR-005 exactly: adds caps for the 3 missing portal-offered categories, touches nothing else (Meals/Travel/Equipment untouched per FR-004/FR-005). |
| II.1 | Every business policy rule MUST have a corresponding synthetic test case | PASS (adapted) | This feature adds no new rule — `over_category_cap`/`uncapped_category` already exist and are tested. Its obligation: a test case per newly-capped category confirming it now evaluates against a real cap instead of always producing `uncapped_category`. Enforced in Phase 2 tasks. |
| II.2 | Generated code MUST pass 100% of deterministic unit tests and static linters | CARRIED FORWARD | Enforced at implementation/CI time (`pytest`, `ruff`, `black`), not a design-time gate. |
| III.1 | Pure business logic MUST remain decoupled from HTTP/API transport layers | PASS | No logic changes at all — `evaluate_claim`/`get_category_cap` are untouched; only the data `PolicyRuleSetRepository` seeds is edited. |
| III.2 | Models MUST strictly use Pydantic v2 validation contracts | PASS | `PolicyRuleSet` is already a Pydantic v2 `BaseModel`; this only changes the literal `category_caps` values passed to its existing constructor. |

No violations requiring justification — Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/005-category-cap-coverage/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

*No `contracts/` — this feature changes no API surface, request/response shape, or internal
component contract; it is a configuration-data-only change consumed entirely inside
`PolicyRuleSetRepository`.*

### Source Code (repository root)

```text
src/                                        # Existing 001-expense-policy-engine backend
└── repositories/
    └── policy_rule_set_repository.py       # MODIFIED: add Lodging/Supplies/Entertainment to category_caps

tests/
└── unit/
    ├── test_evaluate_claim_cap.py                   # EXTENDED: casing already covered by 003; add cases for the 3 newly-capped categories
    └── test_evaluate_claim_uncapped.py               # EXTENDED: confirm a genuinely-uncapped category (unchanged from 003) still behaves correctly
```

**Structure Decision**: Single project (Option 1) — a one-file data change inside the existing
`001-expense-policy-engine` backend's repository layer. No new project, service, endpoint, or
directory; `frontend/` (`002`) is unaffected since it sends the same category strings it always
has — only the backend's cap lookup for those strings now succeeds instead of falling through to
`uncapped_category`.

## Complexity Tracking

*No violations — table omitted.*
