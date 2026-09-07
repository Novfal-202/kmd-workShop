# PolicyRuleSet Matching Contract (internal library contract)

This is the contract for the two new methods on `src/models/policy_rule_set.py`'s `PolicyRuleSet`.
Like `src/services/policy_engine/` (`specs/001-expense-policy-engine/contracts/policy-engine-contract.md`),
these are pure, in-process methods — no I/O, no HTTP/transport types — callable identically from
`evaluate_claim`, tests, or any future caller (constitution Article III.1).

This contract **amends** (does not replace) checks 1, 2, and 4 of
`specs/001-expense-policy-engine/contracts/policy-engine-contract.md`'s `evaluate_claim` contract:
those checks now read as `rule_set.get_category_cap(claim.category)` /
`rule_set.is_weekend_exempt(claim.category)` rather than raw `dict`/`list` access. No other part of
that contract changes.

## `PolicyRuleSet.get_category_cap`

```text
get_category_cap(self, category: str) -> Decimal | None
```

- **Input**: any category string, in any casing (e.g. `"meals"`, `"MEALS"`, `"Meals"`).
- **Output**: the configured cap `Decimal` if `category` case-insensitively matches a key in
  `self.category_caps`; otherwise `None`.
- **Replaces**: `self.category_caps.get(category)` (the case-sensitive lookup at
  `evaluate_claim.py` check 1/2).
- **Guarantee**: for any two category strings that differ only in casing, this method returns the
  identical result (FR-001). For a category with no configured cap under any casing, this method
  returns `None` — identical external behavior to today (FR-004) — so the `uncapped_category`
  violation still fires exactly when it should.

## `PolicyRuleSet.is_weekend_exempt`

```text
is_weekend_exempt(self, category: str) -> bool
```

- **Input**: any category string, in any casing.
- **Output**: `True` if `category` case-insensitively matches an entry in
  `self.weekend_exempt_categories`; otherwise `False`.
- **Replaces**: `category in self.weekend_exempt_categories` (the case-sensitive membership check
  at `evaluate_claim.py` check 4).
- **Guarantee**: for any two category strings that differ only in casing, this method returns the
  identical result (FR-002).

## Non-goals (explicitly out of contract)

- Neither method changes `self.category_caps` or `self.weekend_exempt_categories` in place, and
  neither is a Pydantic field — `PolicyRuleSet.model_dump()` / serialization is unaffected.
- Neither method normalizes or mutates the `category` string on any `ExpenseClaim`/
  `ExpenseClaimInput` — the claim's stored/displayed category is untouched (FR-005). Only the
  internal comparison is case-insensitive.
- No new category caps or weekend-exempt entries are added by this contract — `Supplies` and
  `Entertainment`, for example, remain uncapped under any casing unless a future change to
  `DEFAULT_POLICY_RULE_SET` configures them (spec Assumptions; out of scope here).

## Traceability

| Requirement | Exercised by |
|---|---|
| FR-001 (case-insensitive cap matching) | `get_category_cap` unit tests + `test_evaluate_claim_cap.py` casing-mismatch cases |
| FR-002 (case-insensitive weekend-exempt matching) | `is_weekend_exempt` unit tests + `test_evaluate_claim_weekend.py` casing-mismatch case |
| FR-003 (single shared matching rule for any category-keyed lookup) | Both methods implemented via the same normalization approach (research.md §1) |
| FR-004 (genuinely unconfigured categories stay unconfigured) | `get_category_cap` unit test asserting `None` for a category absent under every casing + `test_evaluate_claim_uncapped.py` |
| FR-005 (claim's stored category casing preserved) | `evaluate_claim` integration tests asserting the returned claim/violation `detail` strings echo the claim's original submitted casing, not a normalized form |
