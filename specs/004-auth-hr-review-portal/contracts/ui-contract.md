# UI Component Contracts (this feature's additions)

These extend `specs/002-expense-portal-ui/contracts/ui-contract.md` — that contract's existing
components (`StatusBadge`, `ViolationTag`, `ClaimHistoryList`, `mapClaimToStatusBadge`) are reused
unmodified by the HR portal; nothing below redefines them.

## `useSession` (in `frontend/src/lib/authClient.ts`)

```ts
function useSession(): { status: 'loading' | 'authenticated' | 'unauthenticated'; role?: 'employee' | 'hr'; displayName?: string }
```

- Calls `GET /auth/me` once on mount (via TanStack Query) to determine whether a valid session
  cookie already exists, so a page reload restores the correct portal without re-prompting sign-in
  (FR-006).
- `status: 'unauthenticated'` on a `401` response — never throws, so callers can render a sign-in
  redirect rather than an error boundary.

## `<RequireRole>` route guard (`frontend/src/components/RequireRole.tsx`)

```ts
<RequireRole role="employee" | "hr"><...></RequireRole>
```

- While `useSession()` is `'loading'`, renders nothing (or a minimal loading state) rather than
  flashing the wrong screen.
- If `'unauthenticated'`, redirects to `/login` (FR-001).
- If authenticated but `session.role !== role`, redirects to that session's own portal root
  (`/` for employee, `/hr` for HR) rather than rendering the mismatched children (FR-003) — this is
  the single place that enforces role separation, so no individual page needs its own role check.
- If the role matches, renders its children unchanged.

## `<LoginPage>` (`frontend/src/pages/LoginPage.tsx`)

- A single username/password form (research.md §3) — no role selector.
- On submit, calls `POST /auth/login`; on success, redirects based on the returned `role`
  (`employee` → `/`, `hr` → `/hr`); on `401`, shows one generic error message
  ("Invalid username or password") without indicating which field was wrong (FR-004).
- Disables the submit control while the request is in flight, and re-enables it on failure so the
  employee/HR user can retry — same in-flight discipline `002`'s `ClaimForm` already established.

## `<EmployeeListPage>` (`frontend/src/pages/EmployeeListPage.tsx`)

- Fetches `GET /employees` (via a `useEmployeeList` TanStack Query hook) and renders one row per
  `EmployeeListEntry`, each linking to `/hr/employees/{employeeId}`.
- Shows a clear empty state when the list is empty (FR-014's first case).
- Performs no filtering/pagination logic of its own — purely presentational over the array it's
  given, matching `002`'s `<ClaimHistoryList>` convention.

## `<EmployeeClaimsPage>` (`frontend/src/pages/EmployeeClaimsPage.tsx`)

- Fetches `GET /employees/{employeeId}/claims` and renders the result through `002`'s existing
  `<ClaimHistoryList>` component unmodified — the response shape is identical to `GET /claims`'s
  `ExpenseClaim[]`, so no new rendering logic is needed for the claim rows themselves.
- Shows a clear empty state when the selected employee has no claims (FR-014's second case).
- For each claim currently in a decidable status (`pending_review` or `needs_information` — same
  `DECIDABLE_STATUSES` the backend already enforces), renders `<ReviewDecisionControls>` alongside
  it; for any other status, renders no decision controls at all (FR-012).

## `<ReviewDecisionControls>` (`frontend/src/components/ReviewDecisionControls.tsx`)

```ts
<ReviewDecisionControls claimId={string} onDecided={() => void} />
```

- Three actions: Approve, Reject, Request Clarification — each calling
  `POST /claims/{claimId}/decisions` with the corresponding `decision` value
  (`approved` | `rejected` | `needs_information`, from `001`'s existing `ReviewDecisionType`).
- The Reject action requires a non-empty reason before it can be submitted (FR-011) — mirrors the
  backend's existing 422 guard, enforced client-side first for immediate feedback.
- On a `409` response (the claim was already decided by someone else — `001`'s existing
  first-write-wins guard), shows a clear "this claim was already decided" message and calls
  `onDecided()` so the parent can refetch and remove the now-stale controls (FR-013).
- On success, calls `onDecided()` so the parent list reflects the new status without a full page
  reload.

## Traceability

| Requirement | Component(s) |
|---|---|
| FR-001, FR-006 | `useSession`, `<RequireRole>` |
| FR-002 | `<LoginPage>` (role-based redirect) |
| FR-003 | `<RequireRole>` |
| FR-004 | `<LoginPage>` |
| FR-005 | `authClient.logout()` (sign-out action in nav) |
| FR-008 | `<EmployeeListPage>` |
| FR-009 | `<EmployeeClaimsPage>` |
| FR-010, FR-011 | `<ReviewDecisionControls>` |
| FR-012 | `<EmployeeClaimsPage>` (conditional rendering of controls) |
| FR-013 | `<ReviewDecisionControls>` (409 handling) |
| FR-014 | `<EmployeeListPage>`, `<EmployeeClaimsPage>` (empty states) |
| FR-015 | `NewClaimPage`/`ClaimHistoryPage` spacing edits (no new component — a styling-only change) |
