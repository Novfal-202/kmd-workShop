# Phase 1 Data Model: Category Cap Coverage

No new entities, fields, or relationships. This feature changes only the *values* held by one
existing entity's existing field.

## PolicyRuleSet (existing entity, `src/models/policy_rule_set.py`) — value change only

| Field | Type | Change |
|---|---|---|
| `category_caps` | `dict[str, Decimal]` | **Shape unchanged.** Three new keys added to the seeded default (`src/repositories/policy_rule_set_repository.py`): `Lodging` → `$300.00`, `Supplies` → `$100.00`, `Entertainment` → `$150.00` (research.md §1). Existing keys (`Meals`, `Travel`, `Equipment`) and their values are untouched. |

No other entity in this codebase (`ExpenseClaim`, `ViolationReason`, `UserAccount`, etc.) is
affected — this feature's entire footprint is the three new dict entries above.

## Relationships

Unchanged. `evaluate_claim` still calls `rule_set.get_category_cap(claim.category)`
(`003-case-insensitive-categories`'s case-insensitive lookup) — it simply now finds a match for
three category strings it previously didn't.

## State transitions

None. This feature doesn't change `ClaimStatus` transitions — it changes which claims *reach* the
`over_category_cap` vs. `uncapped_category` branch of the existing decision, not what happens after.
