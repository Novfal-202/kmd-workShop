# Implementation Plan: Authentication and HR Review Portal

**Branch**: `004-auth-hr-review-portal` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-auth-hr-review-portal/spec.md`

## Summary

Add real authentication (replacing the two hardcoded identity constants `CURRENT_EMPLOYEE_ID`/
`CURRENT_REVIEWER_ID` in `001`'s backend) and a full HR review UI (the `001` backend's
`GET /review-queue`/`POST /claims/{id}/decisions` capability has existed since `001` but has never
had any UI attached to it). A cookie-based session, issued by a new `/auth/login` endpoint against
a small seeded user-account store, replaces direct-to-screen access on both the existing employee
portal (`002`) and a new HR portal added by this feature. The employee experience itself is
unchanged (FR-007); the HR portal reuses the same presentational components `002` already built
(`StatusBadge`, `ViolationTag`, `ClaimHistoryList`) rather than duplicating them. A margin/spacing
pass on the existing employee screens is folded in as a cross-cutting polish task (User Story 4).

## Technical Context

**Language/Version**: Python 3.11+ (backend, unchanged) / TypeScript 5.x, React 18 (frontend, unchanged)

**Primary Dependencies**: Existing backend stack (FastAPI, Pydantic v2, SQLAlchemy) plus two new
backend dependencies — `bcrypt` (password hashing) and `pyjwt` (session token issuance/verification,
research.md §2); existing frontend stack (React Hook Form + Zod, TanStack Query, React Router) — no
new frontend dependency is needed, the login form and route guards are built from what `002`
already installed

**Storage**: SQLite (existing `expense_policy_engine.db`) — one new `users` table, following the
same SQLAlchemy Core `Table`/engine pattern `ClaimRepository` already uses

**Testing**: pytest (backend — unit tests for password verification, JWT round-trip, and role-gating
dependencies; contract tests for the new `/auth/*` and `/employees/*` routes); Vitest + React
Testing Library (frontend — login form validation, route-guard redirect behavior, HR page rendering
against MSW mocks)

**Target Platform**: Linux/macOS server (backend, unchanged); modern evergreen browsers (frontend, unchanged)

**Project Type**: Web application (Option 2) — extends both the existing `001` backend (`src/`) and
the existing `002` frontend (`frontend/`); no new project/service is introduced

**Performance Goals**: No new goals beyond SC-003 (sign-in → recorded HR decision in under 60
seconds) and the existing SC-002 5-second submission-feedback target from `002`, both easily met by
simple CRUD + JWT verification with no external calls

**Constraints**: The session token MUST be carried in an httpOnly cookie (FR-004/FR-006 — not
readable by page JavaScript, so an XSS bug cannot exfiltrate it); the existing employee
submission/history flow and the existing `POST /claims/{id}/decisions` first-write-wins race guard
(constitution-adjacent FR-019 from `001`) MUST NOT change behavior, only who is allowed to reach
them; account creation/provisioning is explicitly out of scope (spec Assumptions) — a small seeded
set of accounts stands in for it, mirroring the existing `DEFAULT_POLICY_RULE_SET` seeding pattern

**Scale/Scope**: A handful of seeded accounts (a few employees + one HR account); 3 new backend
routes files (`auth_routes.py`, `employees_routes.py`, plus a `user_repository.py` and a small
`src/services/auth/` verification module) and 2 modified route files (`claims_routes.py`,
`review_routes.py`); on the frontend, 1 new `LoginPage`, 2 new HR pages
(`EmployeeListPage`, `EmployeeClaimsPage`), a route-guard component, and a spacing/layout pass
across the 2 existing employee pages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Requirement | Status | Notes |
|---|---|---|---|
| I.1 | No code without an approved specification | PASS | `spec.md` exists and passed its requirements-quality checklist (16/16, no open `[NEEDS CLARIFICATION]`) before this plan was generated. |
| I.2 | Diffs that violate spec.md or add unrequested scope are rejected | PASS | This plan implements FR-001..FR-015 as written. It deliberately does not add account self-service, password reset, or an org-directory sync — all explicitly out of scope per spec Assumptions — since that would be unrequested scope. |
| II.1 | Every business policy rule MUST have a corresponding synthetic test case | PASS (adapted) | This feature adds no new *claim* policy rule (approve/reject/needs_information logic is unchanged, still `001`'s `apply_review_decision`). Its equivalent obligation: every new access-control rule (FR-001..FR-003, FR-011..FR-013) gets a corresponding test — wrong-role access is blocked, rejection requires a reason, an already-decided claim offers no further action, a concurrent second decision is rejected. Enforced in Phase 2 tasks. |
| II.2 | Generated code MUST pass 100% of deterministic unit tests and static linters | CARRIED FORWARD | Enforced at implementation/CI time (`pytest`/`ruff`/`black` for the backend, `vitest`/`eslint`/`tsc` for the frontend), not a design-time gate. |
| III.1 | Pure business logic MUST remain decoupled from HTTP/API transport layers | PASS (adapted) | Password verification and JWT-claims validation (`src/services/auth/`) are pure functions with no FastAPI/route imports, mirroring how `evaluate_claim`/`apply_review_decision` stay decoupled; only `auth_routes.py`/route dependencies read and write the actual HTTP cookie. |
| III.2 | Models MUST strictly use Pydantic v2 validation contracts | PASS | The new `UserAccount` model is a Pydantic v2 `BaseModel`, following the same pattern as `ExpenseClaim`/`PolicyRuleSet`. |

No violations requiring justification — Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/004-auth-hr-review-portal/
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
src/                                         # Existing 001-expense-policy-engine backend
├── models/
│   └── user_account.py                      # NEW: UserAccount Pydantic v2 model (role: employee | hr)
├── services/
│   ├── auth/
│   │   ├── passwords.py                     # NEW: hash_password / verify_password (pure, bcrypt)
│   │   └── tokens.py                        # NEW: issue_session_token / decode_session_token (pure, pyjwt)
│   └── policy_engine/                       # Unchanged — apply_review_decision, evaluate_claim untouched
├── repositories/
│   └── user_repository.py                   # NEW: seeded UserAccount store (SQLite), mirrors ClaimRepository
└── api/
    ├── auth_routes.py                       # NEW: POST /auth/login, POST /auth/logout, GET /auth/me
    ├── employees_routes.py                  # NEW: GET /employees, GET /employees/{employeeId}/claims (HR-only)
    ├── dependencies.py                      # NEW: get_current_user / require_employee / require_hr FastAPI dependencies
    ├── claims_routes.py                     # MODIFIED: submitter_id now comes from require_employee, not CURRENT_EMPLOYEE_ID
    └── review_routes.py                     # MODIFIED: reviewer_id now comes from require_hr, not CURRENT_REVIEWER_ID

frontend/                                    # Existing 002-expense-portal-ui app
├── src/
│   ├── pages/
│   │   ├── LoginPage.tsx                    # NEW: single sign-in form for both employee and HR accounts
│   │   ├── EmployeeListPage.tsx             # NEW (HR): list of employees with submitted claims
│   │   ├── EmployeeClaimsPage.tsx           # NEW (HR): one employee's claims + approve/reject/clarify actions
│   │   ├── NewClaimPage.tsx                 # MODIFIED: spacing/layout polish only (US4)
│   │   └── ClaimHistoryPage.tsx             # MODIFIED: spacing/layout polish only (US4)
│   ├── components/
│   │   ├── RequireRole.tsx                  # NEW: route guard — redirects to /login or to the caller's own portal
│   │   ├── ReviewDecisionControls.tsx       # NEW: approve / reject(+reason) / request-clarification action group
│   │   ├── StatusBadge.tsx                  # Unchanged — reused as-is on HR's claim view
│   │   ├── ViolationTag.tsx                 # Unchanged — reused as-is
│   │   └── ClaimHistoryList.tsx             # Unchanged — reused as-is for an HR-viewed employee's claims
│   └── lib/
│       ├── authClient.ts                    # NEW: login/logout/me API calls + a useSession() hook
│       └── apiClient.ts                     # MODIFIED: add fetch credentials:'include' so the session cookie is sent
└── tests/
    ├── unit/                                # authClient/session-state pure logic
    ├── component/                           # LoginPage, RequireRole, ReviewDecisionControls
    └── integration/                         # sign-in → correct portal; HR employee-list → claims → decision flows
```

**Structure Decision**: Web application (Option 2), extending both existing halves of this
project rather than introducing a third. Backend: `src/api/` gains three files and two existing
route files swap a hardcoded constant for a real auth dependency; `src/services/policy_engine/` is
completely untouched (constitution Article III.1 boundary preserved — decision logic doesn't know
or care how the reviewer's identity was established). Frontend: `frontend/src/pages/` gains the
login screen and two HR screens; the existing employee pages get a spacing-only edit; all HR claim
rendering reuses `002`'s existing presentational components rather than forking them.

## Complexity Tracking

*No violations — table omitted.*
