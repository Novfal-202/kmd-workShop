# Quickstart: Validating Authentication and the HR Review Portal

## Prerequisites

- The `001-expense-policy-engine` backend running locally, with this feature's seeded accounts
  applied (research.md §5):

  ```bash
  source .venv/bin/activate
  uvicorn src.api.main:app --reload
  ```

- The `002-expense-portal-ui` frontend running with mocks disabled (`frontend/README.md` →
  "Running against the real backend"):

  ```bash
  cd frontend
  VITE_ENABLE_MOCKS=false npm run dev
  ```

- Seeded development credentials (documented here, not committed anywhere as plaintext outside
  this file): one employee account and one HR account, e.g. `employee1` / `hr-manager`, each with
  a fixed development password shown in the running app's seed-data log line on backend startup.

## Scenario 1 — No screen is reachable before sign-in (US1, FR-001)

1. Open the frontend at `http://localhost:5173` with no prior session.
2. **Expected**: the sign-in screen renders; navigating directly to `/`, `/history`, `/hr`, or
   `/hr/employees/<any-id>` all redirect back to `/login` rather than rendering any content.

## Scenario 2 — Employee sign-in reaches the employee portal only (US1, US2, FR-002, FR-007)

1. Sign in with the employee account's credentials.
2. **Expected**: lands on the "New Claim" screen; submitting a claim and viewing claim history
   work exactly as in `002`'s own quickstart scenarios.
3. Attempt to navigate to `/hr`.
4. **Expected**: redirected back to `/` (the employee's own portal) — the HR screen is never
   rendered (FR-003).

## Scenario 3 — HR sign-in reaches the HR portal only (US1, US3, FR-002, FR-008)

1. Sign out, then sign in with the HR account's credentials.
2. **Expected**: lands on the employee list, showing the employee account from Scenario 2 (since
   it now has at least one submitted claim) with its claim count.
3. Attempt to navigate to `/` (the employee new-claim screen).
4. **Expected**: redirected back to `/hr` — the employee-only screen is never rendered (FR-003).

## Scenario 4 — HR reviews and decides a claim (US3, FR-009, FR-010, FR-011, FR-012)

1. From the HR employee list, click into the employee from Scenario 2.
2. **Expected**: their claims render with amount, category, date, status badge, and any violation
   reasons — identical presentation to the employee's own claim history view.
3. For a claim still awaiting a decision, click Reject without entering a reason.
4. **Expected**: the rejection is blocked client-side until a reason is entered (FR-011).
5. Enter a reason and confirm the rejection.
6. **Expected**: the claim's status updates to "Rejected" and its decision controls disappear
   (FR-012) — it is no longer awaiting a decision.
7. Submit a second new claim as the employee (Scenario 2's account) and, as HR, choose Request
   Clarification on it instead.
8. **Expected**: the claim's status reflects "awaiting more information" and, on the employee's
   own claim history, the same updated status is visible on next load (US2 Acceptance Scenario 3).

## Scenario 5 — Concurrent decisions on the same claim (US3, FR-013)

1. Submit a claim that lands in a decidable status.
2. In two separate browser tabs signed in as HR, open that claim's decision controls.
3. In tab A, approve the claim. In tab B (without reloading), attempt to reject the same claim.
4. **Expected**: tab A's approval succeeds; tab B's rejection is rejected with a clear
   "already decided" message, and the claim's final status reflects only tab A's decision — no
   silent overwrite (SC-005).

## Scenario 6 — Empty states (US3, FR-014)

1. As HR, view the employee list before any employee has submitted a claim (a fresh database).
2. **Expected**: a clear "no employees yet" empty state, not a blank or broken-looking list.
3. As HR, view an employee who has zero claims (if reachable via a direct link).
4. **Expected**: a clear "no claims yet" empty state for that employee.

## Scenario 7 — Visual polish (US4, FR-015)

1. View the employee "New Claim" and "Claim History" screens at both a desktop width and a
   375px mobile width (per `002`'s existing quickstart Scenario 6 device check).
2. **Expected**: page and section content has visible, consistent margin from the viewport edges
   at both widths — no content flush against the edge, no horizontal scrolling introduced.

## Traceability

| Scenario | Requirements exercised |
|---|---|
| 1 | FR-001 |
| 2 | FR-002, FR-003, FR-007 |
| 3 | FR-002, FR-003, FR-008 |
| 4 | FR-009, FR-010, FR-011, FR-012 |
| 5 | FR-013, SC-005 |
| 6 | FR-014 |
| 7 | FR-015, SC-006 |
