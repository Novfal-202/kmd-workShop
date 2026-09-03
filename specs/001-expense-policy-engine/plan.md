# Implementation Plan: Corporate Expense Reimbursement & Policy Engine

**Branch**: `001-expense-policy-engine` | **Date**: 2026-09-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-expense-policy-engine/spec.md`

## Summary

Build a policy engine that evaluates every submitted expense claim against configurable business rules (per-category spending caps, receipt-required threshold, weekend policy, duplicate detection, late-submission window) and either auto-approves it instantly or routes it to a reviewer queue with the specific violation reason(s) recorded. The engine is implemented as a pure, transport-agnostic business-logic library (per constitution Article III) sitting behind a thin HTTP API used by employees (submit/track/withdraw claims) and reviewers (resolve flagged claims), with every decision written to an immutable audit trail (FR-017). The review workflow enforces segregation of duties (a reviewer cannot decide their own claim, FR-018) and first-decision-wins concurrency control (FR-019), and employees may withdraw a claim while it is still awaiting review (FR-020).

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Pydantic v2 (mandated by constitution Article III.2, used for all claim/policy/decision data contracts); FastAPI for the thin HTTP transport layer (routes/serialization only — no business logic); pytest for the test suite.

**Storage**: Relational store (SQLite for local/dev, swappable to a server RDBMS in production) accessed through a repository interface, so the pure policy-engine functions never depend on a specific storage technology. Holds claims, review decisions, and the append-only audit log. The repository's decision-recording write uses an atomic conditional update (`UPDATE ... WHERE status IN ('pending_review','needs_information')`, zero rows affected ⇒ already decided) so FR-019's first-decision-wins rule holds under real concurrent requests, not just in-process.

**Testing**: pytest, with unit tests covering every business rule from FR-002 through FR-020 individually (constitution Article II.1), contract tests against `contracts/api.yaml`, and integration tests replaying `tests/fixtures/synthetic_expenses.json` end-to-end.

**Target Platform**: Linux server (containerized backend service)

**Project Type**: Single backend service — a decoupled policy-engine library plus a thin API layer (Option 1 structure below)

**Performance Goals**: Claim evaluation (auto-approve/flag decision) completes in well under 1 second per claim (supports SC-002's "decision within seconds" with headroom), so the policy engine must run as a synchronous, non-blocking, in-process computation with no external calls in the hot path.

**Constraints**: Business rule logic (`src/services/policy_engine`) MUST NOT import or depend on HTTP/API transport types (constitution Article III.1) — it takes and returns plain Pydantic models and can be invoked from the API layer, a CLI, or a test harness identically. All claim/policy/decision models MUST be Pydantic v2 (constitution Article III.2).

**Scale/Scope**: Corporate internal tool scale — up to several thousand employees and low-thousands of claim submissions per day; no internet-scale traffic assumed.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Requirement | Status | Notes |
|---|---|---|---|
| I.1 | No code without an approved spec in the specs directory | PASS | `spec.md` exists and was validated (all requirements-quality checklist items pass) before this plan was generated. Note: the constitution's literal path is `.specify/specs/`, but this project's actual spec-kit configuration places specs at `specs/<feature>/` (confirmed via `.specify/scripts/bash/setup-plan.sh`); treated as the same requirement under the project's real directory convention. |
| I.2 | Diffs that violate spec.md or add unrequested scope are rejected | PASS (design-time) | This plan only elaborates FR-001..FR-020 and the Key Entities already in spec.md (including the 2026-09-03 clarifications on self-review, concurrent decisions, and withdrawal); no new scope introduced. |
| II.1 | Every business policy rule MUST have a corresponding synthetic test case | PASS | `tests/fixtures/synthetic_expenses.json` already covers cap violations, receipt violations, weekend violations, boundary thresholds, and malformed input (submission-time rules, FR-002..FR-006/FR-013..FR-015/FR-020). Phase 2 tasks will add unit tests for the review-workflow rules added by clarification (FR-018 self-review block, FR-019 concurrency) plus the existing FR-002..FR-017 rules, since those govern reviewer actions rather than claim submission and are not exercised by the submission-time fixture. |
| II.2 | Generated code MUST pass 100% of deterministic unit tests and static linters | CARRIED FORWARD | Enforced at implementation/CI time (tasks.md + CI config), not a design-time gate; no violation at planning stage. |
| III.1 | Pure business logic MUST remain decoupled from HTTP/API transport layers | PASS | Project structure below isolates `src/services/policy_engine/` (pure functions, no FastAPI/HTTP imports) from `src/api/` (routing/serialization only). |
| III.2 | Models MUST strictly use Pydantic v2 validation contracts | PASS | All entities in `data-model.md` are specified as Pydantic v2 models; chosen as the Primary Dependency above. |

No violations requiring justification — Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-expense-policy-engine/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/            # Phase 1 output (/speckit-plan command)
│   ├── api.yaml
│   └── policy-engine-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── models/               # Pydantic v2 data contracts (constitution III.2)
│   ├── expense_claim.py
│   ├── policy_rule_set.py
│   ├── review_decision.py
│   └── audit_log_entry.py
├── services/
│   └── policy_engine/    # Pure business logic (constitution III.1) — no HTTP imports
│       ├── evaluate_claim.py     # FR-002..FR-006, FR-013..FR-015: cap/receipt/weekend/duplicate/late checks
│       ├── review_workflow.py    # FR-008..FR-011, FR-018, FR-019: approve/reject/needs-information transitions, self-review block, first-decision-wins
│       ├── withdrawal.py         # FR-020: employee withdraws a claim still in pending_review/needs_information
│       └── audit_trail.py        # FR-017: records rule evaluations and outcomes
├── repositories/          # Storage-facing interfaces used by services (SQLite-backed)
│   ├── claim_repository.py
│   └── audit_repository.py
└── api/                   # Thin FastAPI transport layer — routing/serialization only
    ├── claims_routes.py   # submit claim, get claim, list employee claims, withdraw claim
    └── review_routes.py   # review queue, approve/reject/needs-information

tests/
├── unit/                  # One test module per policy rule (constitution II.1)
├── contract/              # Validates src/api/ against contracts/api.yaml
├── integration/            # End-to-end runs against tests/fixtures/synthetic_expenses.json
└── fixtures/
    └── synthetic_expenses.json   # Already generated
```

**Structure Decision**: Single-project backend (Option 1) split into four layers — `models` (data contracts), `services/policy_engine` (pure, transport-free business rules), `repositories` (storage access), and `api` (thin HTTP transport). This directly satisfies constitution Article III.1's decoupling requirement: `services/policy_engine` can be unit-tested and reused without any FastAPI/HTTP dependency, and `api/` contains no business rule logic of its own.

## Complexity Tracking

*No violations — table omitted.*
