# Feature Specification: Authentication and HR Review Portal

**Feature Branch**: `[004-auth-hr-review-portal]`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "Add authentication and a full HR review workflow to the Corporate Expense Portal. Today the portal has no login of any kind — every request is silently treated as the same fixed hardcoded employee/reviewer, and there is no HR-facing screen at all (only "New Claim" and "Claim History" exist, both employee-only). We need: (1) An employee login and an HR login, replacing the current direct-to-screen behavior — a user must sign in before reaching either the employee portal or the HR portal, and lands on the correct one for their role. (2) The employee-facing experience stays as today's submit-new-claim and view-my-claim-history (with each claim's current status: approved, rejected, or otherwise), now gated behind employee login. (3) A new HR-facing experience: HR sees a list of all employees; clicking an employee shows that employee's submitted claims; for each claim HR can approve it, reject it, or request clarification (send it back to the employee for more information) — reusing the existing backend review-queue/decision capability, which today has no UI attached to it. (4) Separately, the existing employee portal UI needs a visual polish pass — insufficient margin/spacing around content is making it look cramped/unpolished; this is a cross-cutting improvement to fold into this same feature rather than treated as its own initiative."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Employee and HR Each Sign In to Their Own Portal (Priority: P1)

Anyone opening the portal is first presented with a sign-in screen instead of landing directly on a form. An employee signs in and lands on the employee portal (their claim submission and history). An HR user signs in and lands on the HR portal (the employee list and review screens). Each person only ever sees the portal that matches their role.

**Why this priority**: This is the foundational gate for everything else in this feature — without it, there is no way to distinguish an employee from an HR user, no way to know whose claims are being submitted or reviewed, and the HR review screens described in User Story 3 have no way to know who is allowed to see them. Nothing else in this feature can be meaningfully delivered without this first.

**Independent Test**: Can be fully tested by signing in as an employee and confirming the employee portal (not the HR portal) loads, then signing out and signing in as an HR user and confirming the HR portal (not the employee portal) loads, without ever landing on any screen before completing sign-in.

**Acceptance Scenarios**:

1. **Given** the portal is opened with no active session, **When** the page loads, **Then** a sign-in screen is shown and no claim-submission, claim-history, or HR screen is reachable without first signing in.
2. **Given** a person signs in with employee credentials, **When** sign-in succeeds, **Then** they land on the employee portal (new claim / claim history) and cannot navigate to any HR-only screen.
3. **Given** a person signs in with HR credentials, **When** sign-in succeeds, **Then** they land on the HR portal (employee list) and cannot navigate to the employee claim-submission screen.
4. **Given** a signed-in user closes and reopens the portal within a reasonable session window, **When** the page loads, **Then** they return to their own portal without being asked to sign in again; once the session has expired, they are returned to the sign-in screen.
5. **Given** a signed-in user chooses to sign out, **When** sign-out completes, **Then** they are returned to the sign-in screen and cannot reach either portal until they sign in again.

---

### User Story 2 - Employee Submits Claims and Tracks Their Status (Priority: P1)

Once signed in, an employee has the same submission and history experience the portal already provides — they fill out and submit a new claim, and can see a list of all claims they've submitted along with each one's current status (for example: still awaiting a decision, approved, rejected, or sent back for more information).

**Why this priority**: This is the portal's existing, already-delivered core value (from `002-expense-portal-ui`) — this feature does not change that experience, it only requires the person be signed in as an employee to reach it. It is P1 because it is the reason the portal exists at all; it is listed here to make explicit that sign-in must not break or degrade it.

**Independent Test**: Can be fully tested by signing in as an employee, submitting a claim, and confirming it appears in that employee's claim history with its current status, exactly as today, with the only difference being that sign-in was required first.

**Acceptance Scenarios**:

1. **Given** an employee is signed in, **When** they open the portal, **Then** they can submit a new claim exactly as before this feature.
2. **Given** an employee is signed in, **When** they view their claim history, **Then** they see every claim they have submitted along with its current status, exactly as before this feature.
3. **Given** an employee is signed in, **When** an HR user later approves, rejects, or requests clarification on one of their claims, **Then** that updated status is reflected in the employee's claim history the next time it loads.

---

### User Story 3 - HR Reviews an Employee's Claims (Priority: P1)

Once signed in, HR sees a list of employees. Choosing an employee from that list shows every claim that employee has submitted. For each claim, HR can approve it, reject it, or request clarification (sending it back to the employee for more information) — using the same decision options and outcomes the backend already supports.

**Why this priority**: This is the other half of the portal's core value loop — claims that aren't auto-approved need somewhere for a human to actually make a decision, and today there is no way to do that at all. Without this, every non-auto-approved claim is permanently stuck.

**Independent Test**: Can be fully tested by signing in as HR, selecting an employee from the employee list, confirming their submitted claims are shown, and performing each of the three decisions (approve, reject, request clarification) on different claims, then confirming each decision is recorded and reflected correctly.

**Acceptance Scenarios**:

1. **Given** HR is signed in, **When** they open the HR portal, **Then** they see a list of employees who have submitted at least one claim.
2. **Given** HR selects an employee from the list, **When** that employee's claims load, **Then** HR sees each of that employee's claims with its amount, category, date, current status, and any violation reason(s).
3. **Given** HR is viewing a claim that is awaiting a decision, **When** HR chooses to approve it, **Then** the claim's status updates to approved and is no longer awaiting a decision.
4. **Given** HR is viewing a claim that is awaiting a decision, **When** HR chooses to reject it, **Then** HR is required to provide a reason, and the claim's status updates to rejected with that reason recorded.
5. **Given** HR is viewing a claim that is awaiting a decision, **When** HR chooses to request clarification, **Then** the claim is sent back to the employee for more information and is no longer awaiting an HR decision until the employee responds.
6. **Given** a claim has already been decided (approved, rejected, or is not otherwise awaiting a decision), **When** HR views it, **Then** approve/reject/request-clarification are not offered as actions for that claim.

---

### User Story 4 - The Employee Portal Looks Polished, Not Cramped (Priority: P3)

The employee-facing screens (new claim form, claim history) currently render with little to no breathing room around their content, making the portal look unfinished. Page and section content should have consistent, comfortable spacing so the portal reads as a finished product rather than an unstyled prototype.

**Why this priority**: This is a visual-quality issue, not a functional gap — the portal works correctly without it. It's included in this feature as a cross-cutting improvement per explicit request, rather than shipped separately, but it does not block or gate any of the sign-in or HR review functionality above.

**Independent Test**: Can be fully tested by visually inspecting the new-claim and claim-history screens at both desktop and mobile widths and confirming content is no longer flush against the edges of the viewport or of its containing sections.

**Acceptance Scenarios**:

1. **Given** an employee views the new-claim or claim-history screen on a desktop-width browser, **When** the page renders, **Then** page content has clear, consistent margin from the edges of the browser window and comfortable spacing between sections, rather than appearing flush or cramped.
2. **Given** an employee views the same screens on a mobile-width browser, **When** the page renders, **Then** the same comfortable, consistent spacing is preserved without introducing horizontal scrolling or obscured controls.

---

### Edge Cases

- What happens when someone enters the wrong credentials? The sign-in screen MUST show a clear error and MUST NOT reveal whether the username or the password was the incorrect part.
- What happens when an HR user tries to directly navigate to an employee-only URL (or vice versa) without signing out? The portal MUST block the navigation and route them back to their own portal rather than exposing the other role's screens.
- What happens when HR requests clarification on a claim, and the employee then edits and resubmits it? The claim MUST re-enter the state where it is awaiting an HR decision, following the same behavior the backend already provides for a re-evaluated claim.
- What happens when two HR users attempt to decide the same claim at nearly the same time? Only the first decision MUST be recorded; the second HR user MUST see a clear message that the claim was already decided, without silently overwriting the first decision — reusing the existing backend safeguard for this race.
- What happens when HR opens the employee list but no employee has submitted any claims yet? The portal MUST show a clear empty state rather than an empty or broken-looking list.
- What happens when an employee has zero claims after being selected from the HR employee list? HR MUST see a clear empty state for that employee rather than an empty or broken-looking claim list.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST require a successful sign-in before any employee-facing or HR-facing screen is reachable; no screen is available to an unauthenticated visitor.
- **FR-002**: The portal MUST support two distinct kinds of sign-in — employee and HR — and MUST route a signed-in user only to the portal matching their kind.
- **FR-003**: The portal MUST prevent a signed-in user of one kind from reaching the other kind's screens, whether by navigation link or direct URL entry.
- **FR-004**: The portal MUST show a clear, non-specific error when sign-in fails, without indicating which part of the submitted credentials was incorrect.
- **FR-005**: The portal MUST provide a sign-out action that ends the session and returns the user to the sign-in screen.
- **FR-006**: The portal MUST preserve a signed-in session across a page reload within a reasonable session window, and MUST require sign-in again once that session has expired.
- **FR-007**: The employee-facing claim submission and claim history experience MUST remain functionally unchanged from the existing portal (per `002-expense-portal-ui`), now reachable only after employee sign-in.
- **FR-008**: The HR-facing portal MUST display a list of employees who have submitted at least one claim.
- **FR-009**: Selecting an employee from the HR employee list MUST display that employee's submitted claims, each showing amount, category, expense date, current status, and any violation reason(s).
- **FR-010**: HR MUST be able to approve, reject, or request clarification on any claim that is currently awaiting a decision, using the existing backend review-decision capability.
- **FR-011**: The portal MUST require a reason when HR rejects a claim, and MUST NOT allow a rejection to be recorded without one.
- **FR-012**: The portal MUST NOT offer approve/reject/request-clarification actions on a claim that is not currently awaiting a decision.
- **FR-013**: When a second HR user attempts to decide a claim that has already been decided by someone else, the portal MUST show a clear message that the claim was already decided, and MUST NOT record the second, conflicting decision.
- **FR-014**: The portal MUST show a clear empty state when the HR employee list has no employees with submitted claims, and when a selected employee has no claims.
- **FR-015**: The employee-facing screens (new claim, claim history) MUST render with consistent margin/spacing around page and section content at both desktop and mobile widths, rather than content appearing flush against viewport or container edges.

### Key Entities

- **User Account**: A person who can sign in, with a role of either Employee or HR, distinct from the underlying `submitter_id`/reviewer identity the backend already tracks per claim.
- **Session**: The signed-in state for a User Account, bounded by a reasonable expiration window, ending on explicit sign-out or expiry.
- **Employee List Entry (HR view)**: A summary reference to one employee, shown to HR, sufficient to identify them and see that they have at least one submitted claim.
- **Review Decision**: An HR action taken on a claim — approve, reject (with a required reason), or request clarification — using the outcome types the backend's existing review-decision capability already defines.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of screens (employee and HR) are unreachable without a successful sign-in first.
- **SC-002**: 100% of signed-in employees only ever see employee screens, and 100% of signed-in HR users only ever see HR screens, across both navigation and direct URL attempts.
- **SC-003**: An HR user can go from signing in to recording a decision (approve, reject, or request clarification) on a specific employee's specific claim in under 60 seconds.
- **SC-004**: 100% of claims awaiting a decision become resolvable by HR without any workaround outside the portal (e.g., no direct API calls needed).
- **SC-005**: Zero conflicting/duplicate decisions are recorded when two HR users attempt to decide the same claim at nearly the same time.
- **SC-006**: On a visual review of the employee-facing screens at both desktop and mobile widths, no page or section content appears flush against the viewport or container edges.

## Assumptions

- "HR" refers to whoever is authorized to review and decide claims in this organization — the same role the backend already calls "reviewer"; this spec uses "HR" throughout to match the terms used when this feature was requested, and both terms refer to the same role.
- Credential provisioning (how an employee or HR user initially gets an account/password) is out of scope for this feature; this feature covers signing in and being routed to the correct portal, not account creation or organizational directory sync. A reasonable default account store is assumed to exist or be seeded for initial use.
- The set of "employees" HR sees in the employee list is derived from who has submitted at least one claim (per the backend's existing claim history), not from a separate, full company directory that this feature would need to introduce.
- Session expiration follows standard web-application session norms (a period of hours, not minutes or days) unless a specific compliance requirement says otherwise; no such requirement was stated for this feature.
- This feature reuses the existing backend review-queue and decision capability (`GET /review-queue`, `POST /claims/{claimId}/decisions`) and existing claim-history capability as-is; it does not change what decisions are possible, only who can reach the screen to make them and how that screen is organized (by employee, rather than a flat queue).
- The visual-polish requirement (User Story 4) is scoped to spacing/margin only; it does not include a broader visual redesign (colors, typography, layout restructuring) beyond what is needed to stop content from appearing flush against edges.
