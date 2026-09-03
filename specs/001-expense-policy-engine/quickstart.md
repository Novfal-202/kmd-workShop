# Quickstart: Validating the Expense Reimbursement & Policy Engine

This guide proves the feature works end-to-end against the acceptance scenarios in `spec.md`. It assumes the implementation described in `plan.md` (FastAPI + policy engine + repository) has been built per `tasks.md`.

## Prerequisites

- Python 3.11+ environment with project dependencies installed (`pip install -e .` or equivalent, per the eventual `pyproject.toml`).
- The service running locally (`uvicorn src.api.main:app --reload` or the project's chosen entrypoint), backed by the dev SQLite database.
- The synthetic dataset at `tests/fixtures/synthetic_expenses.json` (already generated).

## 1. Run the automated test suite

```bash
pytest tests/unit          # one test per FR-002..FR-020 policy rule
pytest tests/contract       # src/api/ verified against contracts/api.yaml
pytest tests/integration    # replays tests/fixtures/synthetic_expenses.json end-to-end
```

**Expected outcome**: 100% pass (constitution Article II.2). The integration run asserts, for every one of the 20 fixture claims, that the engine's actual `status` and `violations` match that claim's `expected_status` / `expected_violations`.

## 2. Manually validate User Story 1 (instant decision) — P1

1. Submit a compliant, low-value claim:
   ```bash
   curl -X POST http://localhost:8000/claims -H 'Content-Type: application/json' \
     -d '{"category":"Meals","amount":35.00,"expense_date":"2026-08-19","receipt_attached":false}'
   ```
   **Expected**: HTTP 201, `status: "auto_approved"`, `violations: []` — matches fixture `HP-01`.

2. Submit a claim that exceeds its category cap:
   ```bash
   curl -X POST http://localhost:8000/claims -H 'Content-Type: application/json' \
     -d '{"category":"Meals","amount":65.00,"expense_date":"2026-08-19","receipt_attached":true}'
   ```
   **Expected**: HTTP 201, `status: "pending_review"`, `violations` contains `over_category_cap` — matches fixture `PV-01`.

3. Submit an invalid claim (negative amount):
   ```bash
   curl -X POST http://localhost:8000/claims -H 'Content-Type: application/json' \
     -d '{"category":"Meals","amount":-25.00,"expense_date":"2026-08-19"}'
   ```
   **Expected**: HTTP 422 — matches fixture `EM-01`.

## 3. Manually validate User Story 2 (reviewer resolves flagged claims) — P2

1. List the review queue: `GET /review-queue` — the claim from step 2 above should appear with `over_category_cap` as its violation reason (Acceptance Scenario 1).
2. Approve it:
   ```bash
   curl -X POST http://localhost:8000/claims/{claimId}/decisions -H 'Content-Type: application/json' \
     -d '{"decision":"approved"}'
   ```
   **Expected**: `status` becomes `approved`; `GET /claims/{claimId}/audit-trail` shows the original `pending_review` evaluation entry still intact (append-only).
3. Reject a different flagged claim **without** a reason:
   ```bash
   curl -X POST http://localhost:8000/claims/{otherClaimId}/decisions -H 'Content-Type: application/json' \
     -d '{"decision":"rejected"}'
   ```
   **Expected**: HTTP 422 (FR-009 — reason required to reject).
4. As the same employee who submitted a flagged claim, attempt to decide on it yourself:
   ```bash
   curl -X POST http://localhost:8000/claims/{ownClaimId}/decisions -H 'Content-Type: application/json' \
     -d '{"decision":"approved"}'
   ```
   **Expected**: HTTP 403 — self-review blocked (FR-018, Acceptance Scenario 5); the claim remains in `pending_review`, unchanged.
5. Simulate a decision race: fire two decisions at the same flagged claim back-to-back (e.g., two terminals or a small script issuing both requests concurrently) — one `approved`, one `rejected`.
   **Expected**: exactly one succeeds (HTTP 200) and sets the final status; the other receives HTTP 409 "already decided" (FR-019). `GET /claims/{claimId}` afterward shows only the winning decision in `review_decisions`.

## 4. Manually validate User Story 3 (employee claim history) — P3

```bash
curl http://localhost:8000/claims
```

**Expected**: every claim submitted by the current employee appears with its current status, and the claim approved in step 3.2 above now shows `status: "approved"` without any further employee action (Acceptance Scenario 2).

Now withdraw a still-pending claim:
```bash
curl -X POST http://localhost:8000/claims/{pendingClaimId}/withdraw
```
**Expected**: HTTP 200, `status: "withdrawn"`; the claim disappears from `GET /review-queue` but still appears in `GET /claims` with `status: "withdrawn"` (Acceptance Scenario 3, FR-020). Repeating the same withdraw call, or attempting to withdraw a claim that is already `approved`/`rejected`/`auto_approved`, returns HTTP 409.

## 5. Spot-check boundary and compound-violation behavior

- Submit the `BL-05` fixture claim (`Equipment`, `$200.00`, receipt attached, weekday) — **expected**: `auto_approved` (inclusive threshold).
- Submit the `PV-05` fixture claim (`Meals`, `$120.00`, Sunday, no receipt) — **expected**: `pending_review` with all three violations (`over_category_cap`, `missing_required_receipt`, `weekend_policy_violation`) present simultaneously, not just the first one detected.

If all of the above match, the implementation satisfies SC-001 through SC-006 for the scenarios that can be checked without production traffic volume (SC-001's 70% auto-approval rate and SC-005's 2-business-day review turnaround require monitoring in a running environment over time, not a single quickstart pass).
