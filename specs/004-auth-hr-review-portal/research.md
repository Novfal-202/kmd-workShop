# Phase 0 Research: Authentication and HR Review Portal

## 1. Session mechanism

- **Decision**: A signed JWT, issued by `POST /auth/login`, carried in an httpOnly, `SameSite=Lax`
  cookie (not returned in the JSON response body); every protected route reads the cookie via a
  FastAPI dependency, never a bearer header.
- **Rationale**: httpOnly means page JavaScript cannot read the token, so an XSS bug in the React
  app cannot exfiltrate it (FR-004/FR-006's session-safety intent). A JWT needs no server-side
  session store — consistent with this project's existing preference for simple, dependency-light
  infrastructure (`PolicyRuleSetRepository`'s in-memory default, SQLite over a full RDBMS) — while
  still supporting FR-006's expiry requirement via the token's own `exp` claim, checked on every
  request with no additional lookup.
- **Alternatives considered**: A server-side session table (rejected — adds a second stateful store
  and a cleanup/expiry job for no benefit at this scale; the claims table already proves SQLite is
  an acceptable store here, so this isn't a storage-technology objection, just unnecessary
  complexity for a single-instance dev-scale app); a bearer token returned in the response body and
  stored in `localStorage` by the frontend (rejected — readable by any injected script, which is
  exactly what FR-004/FR-006 are protecting against).

## 2. Password hashing and token library

- **Decision**: `bcrypt` for password hashing (industry-standard, salted, deliberately slow); `pyjwt`
  for signing/verifying the session token (HS256, a server-held secret from an environment
  variable, mirroring `EXPENSE_ENGINE_DB_URL`'s existing environment-variable configuration
  pattern in `src/repositories/db.py`).
- **Rationale**: Both are small, widely-used, single-purpose libraries with no framework lock-in,
  consistent with the project's existing dependency philosophy (FastAPI + Pydantic + SQLAlchemy,
  nothing heavier than needed). Storing only a bcrypt hash means the seeded account store never
  holds a plaintext password anywhere, even in the codebase's seed data (research.md §5).
- **Alternatives considered**: `passlib` (rejected — a wrapper around the same underlying `bcrypt`
  library with more surface area than this project needs for one hashing scheme); a full OAuth2/
  OIDC provider (rejected — massive overkill for a two-role, seeded-account internal tool; nothing
  in the spec calls for third-party identity federation).

## 3. One login form vs. two

- **Decision**: A single sign-in screen (username + password) for both employee and HR accounts.
  The account's role (stored on `UserAccount`, not chosen at login time) determines which portal
  the person lands on after a successful sign-in.
- **Rationale**: Spec Acceptance Scenarios (US1) describe signing in "with employee credentials" or
  "with HR credentials" reaching different destinations — this only requires that different
  accounts have different roles, not that the login form itself branches. One form is simpler to
  build, test, and keep in sync with FR-004's "don't reveal which part of the credentials was
  wrong" requirement (a single failure path, not two to keep consistent).
- **Alternatives considered**: Two separate login routes/forms, e.g. `/login/employee` and
  `/login/hr` (rejected — doubles the UI and validation surface for zero behavioral difference,
  since the role comes from the account either way; would also require the person to already know
  their own role before finding the right form, which the spec doesn't ask for).

## 4. Where the HR employee list comes from

- **Decision**: `GET /employees` returns the distinct `submitter_id`s already present in the
  `claims` table (via `SELECT DISTINCT submitter_id FROM claims`), joined against `UserAccount` for
  a display name where available.
- **Rationale**: Spec Assumptions explicitly scope the employee list to "who has submitted at least
  one claim," not a separate company directory this feature would need to introduce — this matches
  FR-008 exactly and requires no new employee-roster data beyond what `claims` already records.
- **Alternatives considered**: A full `UserAccount`-table listing of every employee account
  regardless of claim history (rejected — spec Assumptions explicitly reject this; it would also
  show HR a list including employees who have never submitted anything, failing the "no
  broken-looking list" edge case in spirit by showing entries with nothing behind them).

## 5. Seed data for initial accounts

- **Decision**: `UserRepository` seeds a small fixed set of accounts on first run (mirroring
  `PolicyRuleSetRepository.DEFAULT_POLICY_RULE_SET`): a handful of employee accounts whose
  usernames match existing claim data conventions, plus one HR account. Passwords are seeded as
  bcrypt hashes of fixed, clearly-labeled development credentials (documented in `quickstart.md`,
  never committed as plaintext anywhere else).
- **Rationale**: Spec Assumptions explicitly place account creation/provisioning out of scope but
  require "a reasonable default account store is assumed to exist or be seeded for initial use" —
  this is the minimal seeding needed to make US1-US3 testable end-to-end without building an
  account-management feature that wasn't asked for.
- **Alternatives considered**: Requiring an operator to manually insert accounts before first use
  (rejected — makes the feature untestable out of the box, and spec Assumptions call for a
  seeded/default store, not a manual setup step).

## 6. Self-review guard interaction with real accounts

- **Decision**: `apply_review_decision`'s existing self-review check (reviewer_id != submitter_id,
  `001`'s FR-018) is left completely unchanged; it now compares two real, distinct account
  identities instead of the two hardcoded placeholder strings.
- **Rationale**: With real accounts, an HR account and an employee account are different people by
  construction, so this check should now essentially never trigger in normal use — but the
  guard itself is `001`'s existing, already-tested defense-in-depth, and removing or altering it
  would be unrequested, out-of-scope surgery on a different feature's already-shipped logic
  (constitution Article I.2).
- **Alternatives considered**: Removing the check as "no longer necessary" (rejected — an HR
  account could theoretically also be given employee-style claim-submission rights in some future
  extension, and the check costs nothing to keep; this feature does not need to make that call).

## Outstanding NEEDS CLARIFICATION

None — all Technical Context unknowns are resolved above.
