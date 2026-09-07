# Phase 0 Research: Case-Insensitive Expense Category Matching

No items in Technical Context were marked `NEEDS CLARIFICATION` — this is a small, well-understood
fix within the existing `001-expense-policy-engine` stack (same language, dependencies, storage,
testing tooling). The one real design decision is *where* and *how* to normalize casing.

## 1. Where to centralize case-insensitive matching

- **Decision**: Add two methods directly on the `PolicyRuleSet` Pydantic model —
  `get_category_cap(category: str) -> Decimal | None` and
  `is_weekend_exempt(category: str) -> bool` — and have `evaluate_claim` call these instead of
  reading `category_caps`/`weekend_exempt_categories` directly.
- **Rationale**: FR-003 requires that *every* category-keyed policy lookup — today's two, and any
  added later — share the same case-insensitive rule, not just the one lookup that happened to be
  reported as buggy. Putting the normalization on the model itself (rather than duplicating a
  `.casefold()` call at each call site in `evaluate_claim`) means a future category-keyed field
  added to `PolicyRuleSet` only needs one more method following the same pattern, and there is a
  single place to unit-test the matching rule in isolation from `evaluate_claim`'s broader logic.
  This also keeps `evaluate_claim` itself pure and decoupled (constitution Article III.1) — it
  still does no I/O, and now expresses each rule as "ask the rule set" rather than "reach into the
  rule set's internal dict shape."
- **Alternatives considered**: Normalizing casing inline at each `evaluate_claim` call site
  (rejected — exactly the duplication FR-003 exists to prevent, and it is easy for a future
  category-keyed rule to forget the `.casefold()` and silently reintroduce the bug); normalizing
  `claim.category` itself at input-validation time in `ExpenseClaimInput` (rejected — FR-005
  requires the claim's original submitted casing to be preserved for storage/display, so the claim
  object itself must not be mutated; only the comparison may be normalized).

## 2. Case-folding method

- **Decision**: Use Python's `str.casefold()` (not `.lower()`) for the normalization key on both
  the configured category strings and the incoming claim's category.
- **Rationale**: `casefold()` is the same operation `.lower()` performs for the plain ASCII
  category names actually in use ("Meals", "Travel", "Lodging", "Supplies", "Entertainment") but is
  the more correct general-purpose choice for case-insensitive comparison, so there is no reason to
  reach for the weaker `.lower()` given `casefold()` costs nothing extra here.
- **Alternatives considered**: `.lower()` (behaviorally identical for the current ASCII category
  set — no functional difference today, `casefold()` is simply the more defensible default given
  the spec's Assumptions scope this to ASCII rather than mandating one method).

## 3. Handling a hypothetical duplicate-casing configuration mistake

- **Decision**: When building the normalized lookup, if two differently-cased keys in
  `category_caps` collapse to the same case-folded key (e.g. both `"Meals"` and `"meals"` were
  mistakenly configured), the value encountered first (Python dict iteration order, i.e.
  insertion order) wins; this is not expected to occur in practice since `PolicyRuleSet` is
  currently a single hand-authored default, not user-editable configuration.
- **Rationale**: Spec Edge Cases explicitly defers the exact tie-breaking rule to planning as an
  implementation detail, not a business ambiguity, since this is a configuration-authoring mistake
  the feature does not need to newly support. First-wins via normal dict construction is the
  simplest behavior that requires no additional code or validation.
- **Alternatives considered**: Raising a validation error on a detected collision (rejected as
  unnecessary complexity for a case that cannot currently occur — `DEFAULT_POLICY_RULE_SET` is a
  static, reviewed literal, not data ingested from an untrusted source).

## Outstanding NEEDS CLARIFICATION

None.
