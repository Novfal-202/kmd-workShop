# UI Component Contracts

These are the internal interfaces the portal's components must honor, so components, the status-mapping logic, and tests can all be built/verified independently of each other and of the live backend.

## `mapClaimToStatusBadge`

```ts
function mapClaimToStatusBadge(claim: ExpenseClaimApiResponse): StatusBadge
```

- **Pure function** — no network calls, no component/render dependency. See `research.md` §5 for the mapping rule and `data-model.md` for `StatusBadge`.
- Must return `{ label: "Pending Review", tone: "neutral", rawStatus: claim.status }` for any `claim.status` value not in the known enum (FR-017) — never throws on an unrecognized status.
- **Verified against**: every entry in `contracts/mock-responses.json` — each mock's `ui_status` field is the expected `label` this function must return for that mock's `body`.

## `<StatusBadge>` component

```ts
<StatusBadge badge={StatusBadge} />
```

- Renders `badge.label` with Tailwind classes selected purely from `badge.tone` (never from `badge.label` string-matching, so a future 6th status still renders correctly via its `tone`).
- Pure/presentational — accepts only the already-computed `StatusBadge`, never a raw claim.

## `<ViolationTag>` component

```ts
<ViolationTag violation={ViolationReasonApi} />
```

- Renders `violation.detail`; `violation.code` is used only to select an icon/tone, never displayed raw to the user.

## `<ClaimForm>` component

- Owns a `ClaimFormDraft` via React Hook Form + the Zod schema from research.md §3, including the required `employeeName` field (FR-001, FR-018, research.md §9).
- Exposes `onSubmit(draft: ClaimFormDraft): Promise<void>` to its parent (the API-calling `NewClaimPage`) — the form component itself performs no `fetch`/API calls, so it can be rendered and validated in isolation in tests.
- MUST disable its submit control whenever either (a) any Zod validation error is present, or (b) `submissionState.phase === "submitting"` is passed in as a prop.
- The submit control MUST render as a footer bar directly attached to the form's own container (FR-020, research.md §10), not as a standalone element separated from the fields by its own margin.

## `<ReceiptAttachment>` component

- Manages one `ReceiptAttachmentDraft`, calling an injected `uploadReceipt(input: File | {url: string}): Promise<ReceiptReference>` prop rather than importing an API client directly — keeps the component testable with a fake uploader.
- Emits the resulting `receiptId`/`previewLabel` up to the parent form; performs client-side type/size (file) or well-formedness (URL) checks before calling `uploadReceipt` at all (FR-005 fast-fail path).

## `<ClaimHistoryList>` component

- Accepts `claims: ExpenseClaimApiResponse[]` (already fetched by its parent via TanStack Query) and renders as an HTML `<table>` (FR-013), one row per claim, each computing its own badge via `mapClaimToStatusBadge`.
- Performs no fetching/pagination logic itself — purely presentational over the array it's given, so it can be rendered against `contracts/mock-responses.json` directly in tests without a network layer.
- Each row MUST have enough vertical padding that its status badge and violation tag(s) read as clearly separated from the adjacent row (FR-019, research.md §10).

## Backend contracts this feature consumes/extends

- `specs/001-expense-policy-engine/contracts/api.yaml` — consumed as-is (`POST /claims`, `GET /claims`, `GET /claims/{id}`, `POST /claims/{id}/withdraw`) for everything except receipt transport and the additive `employee_name` field (research.md §9).
- `contracts/receipts-api.yaml` (this feature) — new, additive `POST /receipts` / `DELETE /receipts/{id}`, plus the new optional `receipt_id` field on the existing `ClaimSubmission` request body.

## Mock verification fixture

- `contracts/mock-responses.json` — the 8 payloads (2 per status + edge fallback/error variants) used to verify `mapClaimToStatusBadge`, `<StatusBadge>`, and `<ClaimHistoryList>` render correctly before the live backend/receipts API exists, per MSW setup in `research.md` §7.
