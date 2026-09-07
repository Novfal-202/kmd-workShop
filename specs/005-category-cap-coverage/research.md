# Phase 0 Research: Category Cap Coverage

No Technical Context unknowns — this is a data-only change with an already-proven case-insensitive
lookup mechanism (`003-case-insensitive-categories`). The one real decision is the actual cap
values.

## 1. Cap values for the three currently-uncapped categories

- **Decision**: Add `Lodging: $300.00`, `Supplies: $100.00`, `Entertainment: $150.00` to
  `DEFAULT_POLICY_RULE_SET.category_caps` in `src/repositories/policy_rule_set_repository.py`,
  alongside the existing `Meals: $50.00`, `Travel: $1000.00`, `Equipment: $500.00` (all three left
  unchanged, per spec FR-004/FR-005).
- **Rationale**: `Entertainment: $150.00` reuses a value already assumed by this codebase's own UI
  mock fixtures (`frontend/src/mocks/fixtures/mock-responses.json`), so it isn't a new number
  invented for this feature — it's making the real backend match what the UI's own test data
  already anticipated. `Lodging` is set higher than `Meals` (single-night hotel costs typically
  exceed a single meal) but below `Travel` (a category that already includes larger transportation
  costs, e.g. flights). `Supplies` is set at a modest mid-range value consistent with routine
  office-supply purchases. All three follow the same "reasonable default, explicitly documented as
  configurable, not audited finance policy" framing the `001` spec already established for Meals.
- **Alternatives considered**: Deriving values from `tests/fixtures/synthetic_expenses.json`
  (rejected — that fixture only exercises `Meals`/`Travel`/`Equipment`, it has no data for the
  three missing categories to draw from); asking the user for exact finance-approved amounts
  (rejected as a blocking dependency — spec Assumptions explicitly frame these as replaceable
  starting defaults, consistent with how `Meals`/`Travel` were already introduced without a
  documented finance sign-off).

## 2. Whether any lookup-logic change is needed

- **Decision**: None. `PolicyRuleSet.get_category_cap()` (added in `003`) already does a
  case-insensitive scan over `category_caps`; adding entries to the dict is sufficient for the new
  categories to be found by every existing call site (`evaluate_claim`'s `over_category_cap`/
  `uncapped_category` check).
- **Rationale**: Confirms this is purely additive data, not a second logic change layered on top of
  `003`'s casing fix.
- **Alternatives considered**: N/A — no alternative implementation approach exists for a pure data
  addition to an already-correct lookup function.

## Outstanding NEEDS CLARIFICATION

None.
