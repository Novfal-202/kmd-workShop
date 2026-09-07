# Phase 1 Data Model: Case-Insensitive Expense Category Matching

No new entities are introduced. This feature adds behavior to one existing entity
(`PolicyRuleSet`) and changes how one existing entity's field is compared (`ExpenseClaim`/
`ExpenseClaimInput.category`) — it does not change either entity's stored shape.

## PolicyRuleSet (existing entity, `src/models/policy_rule_set.py`) — behavior addition

| Field | Type | Notes |
|---|---|---|
| `category_caps` | `dict[str, Decimal]` | **Unchanged shape.** Keys remain exactly as configured today (e.g. `"Meals"`); no migration of existing keys is needed since matching, not storage, is what changes. |
| `weekend_exempt_categories` | `list[str]` | **Unchanged shape.** Same as above. |

**New methods** (the actual fix — see `contracts/policy-rule-set-matching-contract.md`):

| Method | Signature | Notes |
|---|---|---|
| `get_category_cap` | `(category: str) -> Decimal \| None` | Case-insensitive replacement for `category_caps.get(category)`. Returns `None` when no configured category matches under any casing — identical external behavior to today's "uncapped" case, just reachable via more input casings. |
| `is_weekend_exempt` | `(category: str) -> bool` | Case-insensitive replacement for `category in weekend_exempt_categories`. |

Both methods case-fold their input and the configured keys/values internally (research.md §1–2);
neither method mutates `category_caps` or `weekend_exempt_categories`, and neither is a Pydantic
field — they are plain instance methods on the existing model, so no schema/serialization change
occurs (a `PolicyRuleSet` still serializes with exactly the two fields above).

## ExpenseClaim / ExpenseClaimInput (existing entity, `src/models/expense_claim.py`) — unchanged

| Field | Type | Notes |
|---|---|---|
| `category` | `string` | **No change.** Continues to store exactly what the client submitted, in its original casing (FR-005). Only `evaluate_claim`'s *comparison* of this value against `PolicyRuleSet` changes, via the two new methods above. |

## Relationships

- `evaluate_claim` (existing pure function, `src/services/policy_engine/evaluate_claim.py`) now
  calls `rule_set.get_category_cap(claim.category)` in place of
  `rule_set.category_caps.get(claim.category)`, and `rule_set.is_weekend_exempt(claim.category)`
  in place of `claim.category not in rule_set.weekend_exempt_categories`. No other relationship
  between entities changes.

## State transitions

None — this feature does not add, remove, or alter any `ClaimStatus` transition. A claim that was
previously miscategorized as `pending_review` (via `uncapped_category`) due to a casing mismatch
may now instead resolve to `auto_approved` or a correctly-attributed `over_category_cap` violation,
but the set of possible statuses and the transitions between them are unchanged.
