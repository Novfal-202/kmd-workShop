# Quickstart: Validating Category Cap Coverage

## Prerequisites

- The `001-expense-policy-engine` backend running locally:

  ```bash
  source .venv/bin/activate
  uvicorn src.api.main:app --reload
  ```

- The updated `DEFAULT_POLICY_RULE_SET` (`src/repositories/policy_rule_set_repository.py`):
  `Meals` $50.00, `Travel` $1000.00, `Equipment` $500.00 (all unchanged), plus new caps for
  `Lodging` $300.00, `Supplies` $100.00, `Entertainment` $150.00.

## Scenario 1 — A previously-uncapped category now evaluates against a real cap (FR-001, FR-002, FR-003)

```bash
curl -s -X POST http://localhost:8000/claims -H "Content-Type: application/json" \
  -d '{"category":"entertainment","amount":100.00,"expense_date":"2026-01-05","receipt_attached":true}' \
  | python3 -m json.tool
```

**Expected**: `status: "auto_approved"` (or `pending_review` for an unrelated reason like late
submission, but critically **not** an `uncapped_category` violation) — `$100.00` is under the new
`$150.00` Entertainment cap.

Repeat with `amount: 200.00`:

**Expected**: `status: "pending_review"` with an `over_category_cap` violation citing the
`$150.00` cap — not `uncapped_category`.

Repeat both checks for `"category":"lodging"` (cap $300.00) and `"category":"supplies"`
(cap $100.00).

## Scenario 2 — Meals, Travel, and Equipment are unchanged (FR-004, FR-005)

```bash
curl -s -X POST http://localhost:8000/claims -H "Content-Type: application/json" \
  -d '{"category":"meals","amount":40.00,"expense_date":"2026-01-05","receipt_attached":false}' \
  | python3 -m json.tool
```

**Expected**: identical outcome to before this feature — evaluated against the unchanged $50.00
Meals cap.

## Scenario 3 — A genuinely out-of-scope category remains uncapped (FR-005, spec Acceptance Scenario 3)

```bash
curl -s -X POST http://localhost:8000/claims -H "Content-Type: application/json" \
  -d '{"category":"miscellaneous","amount":10.00,"expense_date":"2026-01-05","receipt_attached":false}' \
  | python3 -m json.tool
```

**Expected**: `uncapped_category` violation, unchanged — this feature only covers the portal's 5
offered categories, not every conceivable category string.

## Frontend verification (optional)

With the `002-expense-portal-ui` dev server pointed at this backend
(`frontend/README.md` → "Running against the real backend"), submit a modest claim in each of the
5 dropdown categories and confirm none of them show "has no configured spending cap" for a
reasonable amount.

## Traceability

| Scenario | Requirements exercised |
|---|---|
| 1 | FR-001, FR-002, FR-003 |
| 2 | FR-004 |
| 3 | FR-005 |
