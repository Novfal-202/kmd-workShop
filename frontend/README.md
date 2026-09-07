# Corporate Expense Portal — Web UI

React + TypeScript + Tailwind single-page client for the Corporate Expense Reimbursement &
Policy Engine backend (`../src`). See `../specs/002-expense-portal-ui/` for the full spec, plan,
and task list.

## Prerequisites

- Node.js 20+
- npm

## Install

```bash
npm install
```

## Run the dev server

```bash
npm run dev
```

The dev server runs against [Mock Service Worker](https://mswjs.io/) by default (see
`src/mocks/`), so no live backend is required to exercise the 4 status badges, receipt
attachment, and claim history flows.

## Running against the real backend

1. Start the backend (from the repo root, in a separate terminal — see the root `README.md`):

   ```bash
   source .venv/bin/activate
   uvicorn src.api.main:app --reload
   ```

2. Disable MSW mocking so requests hit the network, and restart the dev server:

   ```bash
   VITE_ENABLE_MOCKS=false npm run dev
   ```

   `vite.config.ts` proxies `/claims` and `/receipts` to `http://localhost:8000`, so the browser
   never makes a cross-origin request (the backend has no CORS middleware configured).

**Known gap**: `POST /receipts` doesn't exist on the backend yet — it's new, additive scope this
feature depends on (see `../specs/002-expense-portal-ui/contracts/receipts-api.yaml`) that hasn't
been implemented on the `001` service. Claim submission and claim history work end-to-end against
the real backend; receipt upload/link attachment will 404 until that endpoint is built.

To point at a backend running somewhere other than `localhost:8000`, set `VITE_API_BASE_URL` in a
`.env` file instead of relying on the dev proxy (useful for a non-dev/preview build).

## Run tests

```bash
npm test          # single run
npm run test:watch
```

Tests use Vitest + React Testing Library, with MSW intercepting network calls at the request
layer (`tests/setup.ts` boots the MSW Node server; individual integration tests override handlers
per-scenario via `server.use(...)`).

## Lint

```bash
npm run lint
```

## Project structure

```text
src/
├── components/   # Presentational + form components
├── pages/        # Route-level page components
├── lib/          # Pure logic: status mapping, validation, API client, draft persistence
├── types/        # Shared TypeScript types mirroring the backend contract
└── mocks/        # MSW handlers + fixtures
tests/
├── unit/         # Pure function tests
├── component/    # Component-level tests
└── integration/  # Full-page flows against MSW mocks
```
