# Feature Specification: Case-Insensitive Expense Category Matching

**Feature Branch**: `[003-case-insensitive-categories]`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "Category matching in the expense policy engine must be case-insensitive. Currently, expense claim categories are matched against configured category caps (in PolicyRuleSet.category_caps) using an exact, case-sensitive string comparison. This causes every claim to be incorrectly treated as "uncapped" (routed to manual review via the uncapped_category violation) whenever the submitted category's casing doesn't exactly match the casing used in the policy configuration (e.g. "meals" from the web UI vs "Meals" in the configured caps). Category matching (for spending caps, weekend-exempt categories, and any other category-keyed policy lookup) must be case-insensitive so that a claim's category is correctly matched against policy configuration regardless of casing differences between the submitting client and the policy configuration."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Claim Category Is Matched Regardless of Casing (Priority: P1)

An employee submits an expense claim with a category value whose casing differs from how that same category is written in the organization's policy configuration (for example, the claim says "meals" while the configured spending cap is recorded against "Meals"). The policy engine MUST still recognize these as the same category and apply the configured cap, rather than treating the claim as belonging to an unconfigured category.

**Why this priority**: This is the core defect. Today, every claim is silently misevaluated as "uncapped" — the policy engine can never actually enforce a configured cap for any category, undermining the entire auto-approval/review-routing decision the system exists to make. Nothing else in this feature has value until category matching itself is reliable.

**Independent Test**: Can be fully tested by configuring a cap for a category using one casing (e.g. "Meals"), then submitting claims for that same category using a variety of different casings (e.g. "meals", "MEALS", "MeAlS") and confirming each is evaluated against the configured cap rather than being flagged as uncapped.

**Acceptance Scenarios**:

1. **Given** a category cap of $50.00 is configured for "Meals", **When** an employee submits a claim with category "meals" (lowercase) for $40.00, **Then** the claim is evaluated against the $50.00 cap and is not flagged with an uncapped-category violation.
2. **Given** a category cap of $50.00 is configured for "Meals", **When** an employee submits a claim with category "MEALS" (all uppercase) for $75.00, **Then** the claim is flagged as exceeding the $50.00 cap (an over-cap violation), not as uncapped.
3. **Given** a category is configured as weekend-exempt (e.g. "Travel"), **When** an employee submits a weekend-dated claim with category "travel" (lowercase), **Then** the claim is correctly treated as weekend-exempt and no weekend-policy violation is recorded.
4. **Given** no cap is configured for a category under any casing (e.g. nothing configured for "supplies" or "Supplies"), **When** an employee submits a claim for that category, **Then** the claim is still correctly flagged as uncapped and routed to manual review — this feature only fixes casing mismatches, it does not add caps for categories that were never configured.

---

### User Story 2 - Consistent Category Matching Across All Policy Lookups (Priority: P2)

Beyond spending caps, the policy engine uses an expense category to look up other policy configuration (e.g. whether a category is exempt from the weekend-submission policy). All such category-keyed lookups must apply the same case-insensitive matching rule, so that fixing one lookup doesn't leave others still vulnerable to the same casing defect.

**Why this priority**: A partial fix (case-insensitive caps but still case-sensitive weekend-exemption, for example) would leave the same class of bug in place for other rules and would surprise whoever configures policy next. It's lower priority than User Story 1 only because caps are the highest-traffic, most commonly hit lookup today.

**Independent Test**: Can be fully tested by auditing every place the policy engine reads a category-keyed configuration value, configuring each with one casing, then submitting claims using differently-cased category values and confirming every such lookup — not just spending caps — resolves correctly.

**Acceptance Scenarios**:

1. **Given** "Travel" and "Lodging" are configured as weekend-exempt categories, **When** an employee submits a weekend-dated claim with category "LODGING" (uppercase), **Then** the claim is treated as weekend-exempt.
2. **Given** any current or future category-keyed policy configuration, **When** a claim is evaluated, **Then** the category comparison does not depend on the exact casing used at submission time versus the casing used in configuration.

---

### Edge Cases

- What happens when the submitted category has leading/trailing whitespace in addition to different casing (e.g. " meals " vs "Meals")? Whitespace differences are a separate concern from casing and are out of scope for this fix — only casing is normalized.
- What happens when two differently-cased category names are both explicitly configured with different caps (e.g. someone accidentally configures both "Meals" and "meals" as separate keys with different values)? The system MUST treat this as a single logical category and use one authoritative configured value; the specific tie-breaking rule (e.g. first-configured wins) is an implementation detail resolved during planning, not a business ambiguity, since this is a configuration-authoring mistake this feature does not need to newly support.
- What happens to a category name containing non-ASCII characters or mixed scripts? Case-insensitive comparison MUST behave consistently for the categories currently in use (plain ASCII English words); broader internationalization of category names is out of scope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The policy engine MUST match a submitted claim's category against configured category spending caps without regard to letter casing.
- **FR-002**: The policy engine MUST match a submitted claim's category against the configured weekend-exempt category list without regard to letter casing.
- **FR-003**: The policy engine MUST apply the same case-insensitive matching rule to any other current or future policy configuration that is keyed by expense category, so no category-keyed lookup remains case-sensitive while another is fixed.
- **FR-004**: When a category has no configured value under any casing, the policy engine MUST continue to treat it as unconfigured (e.g. continue producing the existing uncapped-category violation for spending caps) — this feature corrects casing mismatches only and does not change behavior for genuinely unconfigured categories.
- **FR-005**: The claim record MUST continue to store and display the category exactly as the employee submitted it (original casing preserved); case-insensitive matching applies only to policy lookups, not to what is shown back to the employee or reviewer.

### Key Entities

- **Expense Category**: The category name attached to a claim (e.g. "Meals", "Travel"). Its identity for policy-matching purposes is now case-insensitive, while its displayed/stored form remains exactly as submitted.
- **Policy Rule Set**: The configured category-keyed policy values (spending caps, weekend-exempt categories) that a claim's category is matched against.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of claims submitted with a category that matches a configured category under any casing are evaluated against that category's configured policy (cap, weekend-exemption), never treated as uncapped/unconfigured due to a casing difference alone.
- **SC-002**: 0% of claims for genuinely unconfigured categories (no matching configuration under any casing) incorrectly receive a configured category's treatment.
- **SC-003**: Every existing category-keyed policy lookup in the system passes the same casing-mismatch test (e.g. submitting a differently-cased category value than what was configured), with no lookup remaining case-sensitive.

## Assumptions

- Expense category names in this system are plain ASCII English words (e.g. "Meals", "Travel", "Supplies"); case-insensitive comparison is defined in terms of standard ASCII case-folding and does not need to account for locale-specific casing rules.
- Whitespace and other non-casing formatting differences in category values are a separate, out-of-scope concern from this fix.
- This feature does not add, remove, or change the dollar value of any configured category cap, weekend-exemption entry, or other policy configuration — it only fixes how a submitted category is matched against whatever is already (or will be) configured.
- This feature does not change what category value is stored on or displayed for a claim — only the internal comparison used during policy evaluation.
