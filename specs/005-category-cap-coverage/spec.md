# Feature Specification: Category Cap Coverage

**Feature Branch**: `[005-category-cap-coverage]`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "Short spec for category cap coverage: every expense category the portal actually offers to employees should have a decided, documented spending cap, instead of some categories (lodging, supplies, entertainment) silently having no cap at all — which today means those categories can never be auto-approved and always route to manual review with an 'uncapped_category' violation, and this was never an explicit business decision anywhere, just an artifact of the caps that happened to be hardcoded in the backend's default configuration."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every Portal Category Has a Decided Spending Cap (Priority: P1)

An employee submits a claim in any category the portal actually offers them (meals, travel, lodging, supplies, or entertainment). Whether their claim can be auto-approved depends on the amount compared to that category's cap — not on whether anyone happened to remember to configure a cap for that particular category.

**Why this priority**: Today, 3 of the portal's 5 offered categories (lodging, supplies, entertainment) have no configured cap at all, so every claim in those categories is forced into manual review regardless of amount — not because a reviewer decided that's the right threshold, but because nobody ever decided a cap for them. This silently defeats the auto-approval flow for most of the portal's category list.

**Independent Test**: Can be fully tested by submitting a modest, policy-compliant claim in each of the portal's 5 offered categories and confirming each is evaluated against an actual configured cap (auto-approved if under it, flagged with a specific over-cap reason if over it) — never flagged as merely "uncapped."

**Acceptance Scenarios**:

1. **Given** an employee submits a claim in any category the portal's claim form offers, **When** the amount is at or under that category's configured cap, **Then** the claim is not flagged as uncapped (it may still be auto-approved or flagged for other reasons, e.g. a missing receipt).
2. **Given** an employee submits a claim in any category the portal's claim form offers, **When** the amount exceeds that category's configured cap, **Then** the claim is flagged with the specific over-cap reason and the configured cap amount, not a generic "no cap configured" message.
3. **Given** the backend also accepts a category the portal's own claim form does not offer as an option (a category outside this feature's scope), **When** a claim is submitted for it, **Then** it may still be flagged as uncapped — this feature only guarantees cap coverage for the portal's own offered category list, not every conceivable category string.

---

### Edge Cases

- What happens if the portal's offered category list changes in the future (a category is added or renamed)? This feature does not automate keeping caps in sync with the category list going forward — it establishes cap coverage for today's list; keeping them in sync as the list changes is a process concern for whoever maintains both, not a one-time technical fix.
- What happens to a category cap that exists today but the portal doesn't offer as an option (e.g. a cap configured for a category name no employee can actually select)? It is left as-is; this feature does not remove or judge cap configuration for categories outside the portal's own offered list, since the backend that owns that configuration may serve callers other than this portal's claim form.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST have a configured, non-zero spending cap for every expense category the portal's claim form offers as a selectable option.
- **FR-002**: When a claim's amount is at or under its category's configured cap, the system MUST NOT produce an "uncapped category" violation for that claim.
- **FR-003**: When a claim's amount exceeds its category's configured cap, the system MUST produce an over-cap violation identifying the specific cap amount that was exceeded.
- **FR-004**: This feature MUST NOT change the cap amount for any category that already has one configured and is offered by the portal (e.g. Meals), unless that existing value is later found to conflict with a documented business decision.
- **FR-005**: This feature MUST NOT remove or alter cap configuration for any category not offered by the portal's own claim form, even if that category currently has a cap (e.g. a cap configured under a name the portal's category list doesn't include).

### Key Entities

- **Category Cap**: A configured maximum spending amount associated with one expense category, used to decide whether a claim in that category can be auto-approved. Every category the portal's claim form offers MUST have one.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the portal's offered expense categories have a configured, non-zero spending cap.
- **SC-002**: 0% of claims submitted in a portal-offered category are flagged as "uncapped" solely because that category was never configured — every such claim's outcome depends on comparing its amount to an actual cap.

## Assumptions

- The portal's offered category list is exactly the five categories in `frontend/src/lib/validationSchema.ts`'s `EXPENSE_CATEGORIES`: Meals, Travel, Lodging, Supplies, Entertainment (matched case-insensitively per `003-case-insensitive-categories`). This feature treats that list as the authoritative set of categories needing cap coverage, since it's what an employee can actually select.
- Meals ($50.00) and Travel ($1000.00) already have configured caps and are left unchanged, since no business signal suggests those values are wrong — only the three missing categories are this feature's actual gap.
- Reasonable default cap amounts are assigned for the three currently-uncapped categories, based on relative spending norms for each category type and the one existing illustrative reference value already used elsewhere in this codebase's UI mock fixtures (Entertainment: $150.00, matching `frontend/src/mocks/fixtures/mock-responses.json`): Lodging $300.00, Supplies $100.00, Entertainment $150.00. These are starting defaults, not audited finance policy — an organization should replace them with real approved amounts when available, the same way Meals/Travel's existing values were always documented as configurable, not fixed.
- The backend's existing "Equipment" category cap ($500.00) is not offered as a category option anywhere in the portal's claim form; per FR-005 this feature leaves it untouched rather than removing it, since the backend API is not necessarily restricted to only the portal's own category list.
