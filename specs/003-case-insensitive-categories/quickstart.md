# Quickstart: Validating Case-Insensitive Category Matching

## Prerequisites

- The `001-expense-policy-engine` backend running locally (see repo root `README.md`):

  ```bash
  source .venv/bin/activate
  uvicorn src.api.main:app --reload
  ```

- The default seeded `PolicyRuleSet` (`src/repositories/policy_rule_set_repository.py`):
  `Meals` capped at $50.00, `Travel` capped at $1000.00, `Equipment` capped at $500.00,
  `Travel`/`Lodging` weekend-exempt.

## Scenario 1 — A cap matches regardless of casing (US1, FR-001)

```bash
curl -s -X POST http://localhost:8000/claims -H "Content-Type: application/json" \
  -d '{"category":"meals","amount":40.00,"expense_date":"2026-01-05","receipt_attached":false}' \
  | python3 -m json.tool
```

**Expected**: `status: "auto_approved"`, no `uncapped_category` violation — the lowercase `"meals"`
is matched against the configured `"Meals"` cap ($50.00), and $40.00 is under it.

Repeat with `"category":"MEALS"` for `amount: 75.00`:

**Expected**: `status: "pending_review"` with an `over_category_cap` violation (not
`uncapped_category`) — $75.00 exceeds the $50.00 cap regardless of the all-caps input.

## Scenario 2 — Weekend exemption matches regardless of casing (US1/US2, FR-002)

```bash
curl -s -X POST http://localhost:8000/claims -H "Content-Type: application/json" \
  -d '{"category":"travel","amount":100.00,"expense_date":"2026-01-03","receipt_attached":true}' \
  | python3 -m json.tool
```

(2026-01-03 is a Saturday.) **Expected**: no `weekend_policy_violation` — lowercase `"travel"` is
recognized as weekend-exempt just as `"Travel"` is.

## Scenario 3 — A genuinely unconfigured category still routes to review (US1, FR-004)

```bash
curl -s -X POST http://localhost:8000/claims -H "Content-Type: application/json" \
  -d '{"category":"supplies","amount":20.00,"expense_date":"2026-01-05","receipt_attached":false}' \
  | python3 -m json.tool
```

**Expected**: `status: "pending_review"` with an `uncapped_category` violation — `"supplies"` has
no configured cap under any casing (only `Meals`/`Travel`/`Equipment` are configured today), so
this fix does not change its outcome. This confirms the fix corrects casing mismatches only and
does not fabricate caps for categories that were never configured.

## Scenario 4 — The claim's original casing is preserved (FR-005)

Re-run Scenario 1's first request and inspect the response body's `category` field.

**Expected**: `"category": "meals"` — exactly as submitted, not normalized to `"Meals"` or any
other casing, even though the cap comparison internally matched it case-insensitively.

## Traceability

| Scenario | Requirements exercised |
|---|---|
| 1 | FR-001 |
| 2 | FR-002 |
| 3 | FR-004 |
| 4 | FR-005 |

Frontend verification (optional): with the `002-expense-portal-ui` dev server pointed at this
backend (`frontend/README.md` → "Running against the real backend"), submitting a claim with any
category from the portal's category dropdown should no longer unconditionally show
`uncapped_category` for `Meals`/`Travel`/`Equipment`.
