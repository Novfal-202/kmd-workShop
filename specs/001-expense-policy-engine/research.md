# Phase 0 Research: Corporate Expense Reimbursement & Policy Engine

All Technical Context items had a reasonable, constitution-consistent default — no items were left as `NEEDS CLARIFICATION`. This document records the decision, rationale, and alternatives considered for each.

## 1. Language & framework

- **Decision**: Python 3.11+, FastAPI for the HTTP layer, Pydantic v2 for all data contracts.
- **Rationale**: Constitution Article III.2 mandates Pydantic v2 validation contracts, which strongly implies a Python service. FastAPI is the natural pairing — it consumes Pydantic v2 models natively for request/response validation and keeps routing code thin, which supports the Article III.1 decoupling requirement (routes just call into the policy engine and (de)serialize).
- **Alternatives considered**: Flask + separate marshmallow/pydantic validation (rejected — adds a second validation layer, weaker Pydantic v2 integration than FastAPI). Django REST Framework (rejected — heavier ORM/framework coupling than this feature needs, and DRF serializers would compete with the mandated Pydantic v2 contracts).

## 2. Storage

- **Decision**: A repository-interface pattern (`src/repositories/`) backed by SQLite for local development and CI, swappable to a server-grade RDBMS (e.g., PostgreSQL) in production via the same interface.
- **Rationale**: The spec requires persistent claim history (US3), a review queue (US2), and an audit trail (FR-017) — all relational, low-write-volume data with clear entities and relationships (see data-model.md). A relational store is the simplest fit. Hiding it behind a repository interface keeps `services/policy_engine` free of storage-technology imports, satisfying Article III.1's transport/infrastructure decoupling in spirit as well as letter.
- **Alternatives considered**: In-memory only (rejected — claim history and audit trail must survive restarts per FR-012/FR-017). Document store (rejected — the entities are relational with foreign-key-like references (claim → reviewer, claim → audit entries) and fixed schemas; no schema-flexibility requirement justifies a document store).

## 3. Testing strategy

- **Decision**: pytest, with three layers — unit tests (one per business rule, FR-002 through FR-020), contract tests (verify `src/api/` matches `contracts/api.yaml`), and integration tests that replay `tests/fixtures/synthetic_expenses.json` end-to-end and assert each claim's `expected_status`/`expected_violations` against the engine's actual output.
- **Rationale**: Directly satisfies constitution Article II.1 ("every business policy rule MUST have a corresponding synthetic test case") and II.2 (100% pass required). The synthetic fixture already exists and is partitioned by rule category (happy path, policy violation, boundary limit, edge/malformed), making it a natural source for both unit and integration assertions.
- **Alternatives considered**: Property-based testing (e.g., Hypothesis) as the sole strategy (rejected for v1 — valuable as a later addition, but the fixed synthetic fixture set gives clearer, auditable traceability from FR-### to test case, which the constitution's compliance framing favors).

## 4. Performance target

- **Decision**: p95 claim-evaluation latency (policy engine only, excluding network) under 200ms; end-to-end submit-to-decision under 1 second.
- **Rationale**: SC-002 requires a decision "within seconds" of submission with no manual wait for the routine majority. Because the policy engine does pure in-memory comparisons against a small, cached rule set (caps, thresholds, exemption list) plus one duplicate/late-submission lookup against the claim repository, sub-second performance is achievable without special optimization; the target is set with comfortable headroom rather than being a binding constraint on architecture.
- **Alternatives considered**: No explicit target (rejected — SC-002 is a measurable success criterion and needs a concrete engineering target to be testable).

## 5. Weekend-exempt categories & policy parameters

- **Decision**: Policy parameters (per-category caps, receipt-required threshold, auto-approval threshold, weekend-exempt category list) live in the `PolicyRuleSet` entity, loaded from configuration/storage at evaluation time rather than hardcoded — consistent with spec.md's Assumptions section. Example values used for illustration and the synthetic fixture: Meals cap $50.00, receipt-required threshold $100.00 (inclusive), auto-approval threshold $200.00 (inclusive), Travel/Lodging exempt from weekend policy.
- **Rationale**: The spec explicitly defers the actual company amounts to configuration; hardcoding them would violate the spirit of FR-002/FR-003/FR-004/FR-005 all being phrased as "configurable." Using the same example values already encoded in `tests/fixtures/synthetic_expenses.json` keeps the design and the existing synthetic dataset consistent.
- **Alternatives considered**: Hardcoded constants (rejected — spec assumption explicitly calls these out as configurable business parameters, and reviewers/finance admins are expected to change them without a code deploy).

## 6. First-decision-wins concurrency control (FR-019)

- **Decision**: The claim repository's decision-recording write is an atomic conditional update — `UPDATE expense_claims SET status = ?, ... WHERE id = ? AND status IN ('pending_review', 'needs_information')`. If the update affects zero rows, the claim had already left a decidable status (another decision beat it), and the API layer returns an "already decided" error (FR-019) without touching the `ReviewDecision`/`AuditLogEntry` records. No application-level locking, queueing, or claim-assignment step is introduced.
- **Rationale**: The clarification session settled on "first recorded decision wins, second attempt rejected." A single conditional `UPDATE` guarded by the current status is the simplest mechanism that is correct under real concurrent requests (not just serialized in-process calls), requires no new infrastructure (no distributed lock, no message queue), and keeps `services/policy_engine` free of concurrency-control code — the atomicity lives in the repository layer, consistent with Article III.1's decoupling.
- **Alternatives considered**: Optimistic locking via a version column (rejected — equivalent safety for this single-field transition, but adds a version field and conflict-retry logic the spec doesn't need since there's nothing to retry: a loser simply gets "already decided," it doesn't retry the write). Reviewer-claiming/assignment lock (rejected — this is the "Require explicit reviewer assignment" option considered and not chosen during clarification; it adds a workflow step FR-019 doesn't call for).

## 7. Claim withdrawal (FR-020)

- **Decision**: Withdrawal is a new terminal-ish transition (`pending_review` or `needs_information` → `withdrawn`) implemented in `src/services/policy_engine/withdrawal.py`, using the same atomic conditional-update pattern as decision-recording (`WHERE status IN ('pending_review','needs_information')`) so a claim cannot be withdrawn out from under a reviewer who has *just* decided it, and vice versa — whichever transition's conditional update commits first wins; the other gets a "no longer available" / "already decided" error.
- **Rationale**: Reuses the same concurrency-safe pattern established for FR-019 rather than inventing a second mechanism, and directly implements the clarification's answer ("employee may withdraw any time it is in pending review or needs information").
- **Alternatives considered**: Soft-delete/hide instead of a distinct `withdrawn` status (rejected — spec.md's Key Entities and US3 Acceptance Scenario 3 explicitly require `withdrawn` to remain visible in claim history with that status, not be hidden).
