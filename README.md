# Corporate Expense Reimbursement & Policy Engine

Evaluates every submitted expense claim against configurable business rules — per-category
spending caps, a receipt-required threshold, a weekend policy, duplicate detection, and a
late-submission window — auto-approving safe low-value claims instantly and routing
everything else to a reviewer queue with the specific violation reason(s) attached.

Full design docs: [`specs/001-expense-policy-engine/`](specs/001-expense-policy-engine/)
(spec, plan, data model, API contract, quickstart).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the service

```bash
source .venv/bin/activate
uvicorn src.api.main:app --reload
```

The dev database is a local SQLite file (`expense_policy_engine.db` by default); override
with the `EXPENSE_ENGINE_DB_URL` environment variable.

## Run the tests

```bash
source .venv/bin/activate
pytest tests/          # unit + contract + integration (74 tests)
ruff check src tests   # lint
black --check src tests
```

## Try it end-to-end

See [`specs/001-expense-policy-engine/quickstart.md`](specs/001-expense-policy-engine/quickstart.md)
for a full curl-based walkthrough covering instant auto-approval, policy violations,
reviewer decisions (including the self-review block and decision-race handling), claim
withdrawal, and the boundary/compound-violation cases from
[`tests/fixtures/synthetic_expenses.json`](tests/fixtures/synthetic_expenses.json).

## Project layout

```text
src/
├── models/               # Pydantic v2 data contracts
├── services/
│   ├── policy_engine/    # Pure business logic — no HTTP/storage imports
│   └── notifications.py
├── repositories/         # SQLite-backed storage
└── api/                  # Thin FastAPI transport layer

tests/
├── unit/          # One suite per business rule
├── contract/      # src/api/ verified against specs/.../contracts/api.yaml
├── integration/   # End-to-end flows, including the synthetic fixture replay
└── fixtures/synthetic_expenses.json
```
