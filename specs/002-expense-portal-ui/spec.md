# Feature Specification: Corporate Expense Portal Web UI

**Feature Branch**: `[002-expense-portal-ui]`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: "Build a modern React + Tailwind web UI for the Corporate Expense Portal. Allow employees to input expense details, upload/link receipts, submit claims to the backend API, and view real-time policy evaluation status (Auto-Approved, Requires Manager, Audit Flagged, Rejected) with visual violation badges and dynamic field validation."

## Clarifications

### Session 2026-09-07

- Q: Should employees type their name into the new-claim form now, as a temporary stand-in until the separate sign-in feature ships, or should the form wait to get the employee's name automatically once login is built? → A: Add it now as a plain "Your name" field on the claim form, independent of the separate sign-in/HR-portal effort, which will be scoped and delivered on its own timeline.
- Q: Should the claim history view keep its current card/list presentation or switch to a table layout? → A: Switch to a table — one row per claim, with a column per attribute (employee name, amount, category, date, status, violations).
- Q: When reducing page whitespace, does that mean the excess empty page area around/below content, or the padding/margins inside the form and table (added to fix the earlier "no margin, cramped" complaint)? → A: The excess empty page area around/below content — the padding/margins inside the form and table stay as they are; the page itself should not appear to have a disproportionate amount of blank space around a comparatively short page.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Employee Submits an Expense Claim Through the Portal (Priority: P1)

An employee opens the expense portal, fills in a claim form (amount, category, expense date, and a receipt), and submits it. The portal validates the fields as they type, sends the claim to the backend, and immediately displays the outcome of policy evaluation — whether the claim was auto-approved or needs further review, along with the reason.

**Why this priority**: This is the primary reason the portal exists — without a working submission flow that reflects the backend's real-time decision, there is no usable product. All other stories build on this one.

**Independent Test**: Can be fully tested by filling out the claim form with valid data, submitting it, and confirming the portal displays the correct evaluation outcome and reason returned by the backend within seconds.

**Acceptance Scenarios**:

1. **Given** an employee is on the "New Claim" form, **When** they enter a valid amount, category, expense date, and attach a receipt, **Then** the submit action is enabled and, upon submission, the claim is sent to the backend and the portal displays the returned status (e.g., "Auto-Approved") with a visual badge.
2. **Given** an employee submits a claim that the backend flags as requiring review, **When** the response is received, **Then** the portal displays a "Requires Manager" or "Audit Flagged" status badge along with the specific violation reason(s) returned by the backend.
3. **Given** an employee submits a claim that the backend rejects outright (e.g., invalid amount), **When** the response is received, **Then** the portal displays a "Rejected" status badge with the rejection reason and keeps the entered data available for correction.
4. **Given** the backend request fails (e.g., network error, server unavailable), **When** submission is attempted, **Then** the portal displays a clear error message, does not show a false success/decision state, and allows the employee to retry without re-entering all fields.

---

### User Story 2 - Employee Gets Immediate Field-Level Guidance While Filling the Form (Priority: P2)

As an employee fills out the claim form, the portal validates each field as it is entered (or on blur) and shows inline guidance — e.g., flags a missing receipt above the required threshold, an invalid or future expense date, or a non-numeric/negative amount — before the claim is ever submitted.

**Why this priority**: Catching errors before submission reduces wasted round-trips to the backend and rejected claims, directly improving the auto-approval experience promised in the core flow, but the portal is still usable (with more backend rejections) without it.

**Independent Test**: Can be fully tested by entering invalid values into each form field individually (negative amount, missing category, future/invalid date, no receipt above threshold) and confirming each triggers a specific, field-adjacent validation message without needing to submit the form.

**Acceptance Scenarios**:

1. **Given** an employee enters a zero, negative, or non-numeric amount, **When** they move to the next field, **Then** the portal shows an inline error on the amount field and disables submission until corrected.
2. **Given** an employee selects an expense date in the future or leaves the date empty, **When** they move to the next field, **Then** the portal shows an inline error on the date field.
3. **Given** an employee has not attached or linked a receipt for a claim, **When** they attempt to submit, **Then** the portal shows an inline warning near the receipt field if the amount is at or above the receipt-required threshold communicated by the backend/policy configuration.
4. **Given** all fields are valid, **When** the employee reviews the form, **Then** no validation errors are shown and the submit action is enabled.

---

### User Story 3 - Employee Attaches Receipts by Upload or by Link (Priority: P2)

An employee can provide proof of an expense either by uploading a receipt file (e.g., photo or PDF) or by pasting a link to a receipt hosted elsewhere, and can see a preview or confirmation of what was attached before submitting.

**Why this priority**: Receipt evidence directly drives a major policy check (missing-receipt violations); giving employees a flexible, low-friction way to attach one reduces avoidable review flags, but claims can still be submitted (and correctly flagged) without this convenience.

**Independent Test**: Can be fully tested by uploading a file in one claim and pasting a receipt link in another, confirming both are accepted, previewed/confirmed in the UI, and correctly transmitted with the claim submission.

**Acceptance Scenarios**:

1. **Given** an employee chooses to upload a receipt, **When** they select a supported file, **Then** the portal shows a filename/thumbnail confirmation and includes the file with the submitted claim.
2. **Given** an employee chooses to link a receipt instead, **When** they paste a URL, **Then** the portal validates it looks like a well-formed link and includes it with the submitted claim.
3. **Given** an employee selects an unsupported file type or an oversized file, **When** they attempt to attach it, **Then** the portal rejects the attachment with a clear message and does not include it with the claim.
4. **Given** an employee has attached a receipt, **When** they decide to remove it before submitting, **Then** the portal removes the attachment and re-evaluates whether a receipt-related warning should be shown.

---

### User Story 4 - Employee Reviews Their Claim History and Status Changes (Priority: P3)

An employee views a list of all claims they have submitted through the portal, each showing its amount, category, date, current status (Auto-Approved, Requires Manager, Audit Flagged, Rejected, or a later reviewer decision), and — for flagged claims — the violation reason(s), with the list reflecting status changes made later by reviewers.

**Why this priority**: Gives employees self-service visibility and builds trust in the automated decisions, but the portal's core submission value is delivered without this view (status could otherwise only be checked by asking someone).

**Independent Test**: Can be fully tested by submitting several claims with different outcomes, then confirming the claim history list in the portal shows the correct status and reasons for each, and that it reflects an updated status after a backend-side reviewer decision.

**Acceptance Scenarios**:

1. **Given** an employee has submitted multiple claims, **When** they open their claim history, **Then** each claim is listed with its amount, category, date, and current status badge.
2. **Given** a claim has one or more recorded violations, **When** the employee views that claim in their history, **Then** the specific violation reason(s) are shown alongside its status badge.
3. **Given** a flagged claim is later decided by a reviewer on the backend, **When** the employee reloads or revisits their claim history, **Then** the displayed status reflects the reviewer's decision.

---

### Edge Cases

- What happens when the backend policy evaluation returns a status the portal doesn't recognize? The portal MUST display it as a generic "Pending Review" state with the raw status/reason text rather than failing to render or showing a misleading badge.
- What happens when a receipt upload is large or slow? The portal MUST show upload progress and MUST NOT allow duplicate submission while an attachment is still uploading.
- What happens when an employee submits a claim, the backend accepts it, but the network then drops before the decision response arrives? The portal MUST distinguish "submitted, awaiting result" from a confirmed failure and MUST NOT silently show no feedback at all.
- What happens when an employee double-clicks submit or presses submit twice in quick succession? The portal MUST prevent a duplicate submission of the same claim.
- What happens when an employee's session/authentication expires while filling out a long form? The portal MUST preserve the entered (unsubmitted) field values and prompt re-authentication rather than silently discarding the draft.
- How does the portal behave on a small (mobile-width) screen? All core actions (submit a claim, attach a receipt, view status/history) MUST remain usable and legible without horizontal scrolling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST provide a claim submission form capturing, at minimum: the employee's name, amount, expense category, date the expense was incurred, and a receipt (uploaded file or linked URL, optional per backend policy).
- **FR-002**: The portal MUST validate form fields dynamically (as the employee types or moves between fields) and surface field-specific error/warning messages before submission, without requiring a round-trip to the backend for basic format checks (e.g., non-numeric amount, empty required field, future-dated expense).
- **FR-003**: The portal MUST disable claim submission while any known field-level validation error is present.
- **FR-004**: The portal MUST allow attaching a receipt either by uploading a file or by pasting a link, and MUST show a confirmation (filename, thumbnail, or validated link) before submission.
- **FR-005**: The portal MUST reject, at the attachment step, files of unsupported type or exceeding the maximum allowed size, with a clear on-screen message identifying the problem.
- **FR-006**: The portal MUST allow an employee to remove an attached receipt before submitting the claim.
- **FR-007**: The portal MUST submit the completed claim (fields plus receipt reference) to the backend expense-claim API and await the policy evaluation result.
- **FR-008**: The portal MUST display the returned evaluation outcome using one of four visually distinct status badges: "Auto-Approved," "Requires Manager," "Audit Flagged," or "Rejected," mapped from the backend's returned status.
- **FR-009**: The portal MUST display any violation reason(s) returned by the backend alongside a non-"Auto-Approved" status badge, using a visually distinct violation indicator (badge/tag) per reason.
- **FR-010**: The portal MUST prevent duplicate submission of the same claim (e.g., from a double-click or repeated submit action) while a submission is in flight.
- **FR-011**: The portal MUST display a distinct in-progress ("submitting"/"awaiting decision") state between submission and receipt of the backend's evaluation result.
- **FR-012**: The portal MUST display a clear, actionable error message (distinct from any policy-status badge) when the submission request fails due to a network or server error, and MUST allow the employee to retry without losing entered field values.
- **FR-013**: The portal MUST provide a claim history view, presented as a table (one row per claim), listing all claims submitted by the currently signed-in employee, each row showing the employee name, amount, category, expense date, current status badge, and violation reason(s) if any.
- **FR-018**: The portal MUST require a non-empty employee name before allowing claim submission, captured directly on the claim form; this is an interim capture mechanism, independent of and not blocked by the separate sign-in feature that will eventually supply this identity automatically.
- **FR-014**: The portal MUST reflect status updates made later by a reviewer (e.g., a flagged claim subsequently approved or rejected) the next time the claim history is loaded or refreshed.
- **FR-015**: The portal MUST remain usable — submission, attachment, and status/history viewing — on both desktop and mobile-width screens.
- **FR-016**: The portal MUST preserve entered but unsubmitted form data if the employee's session expires mid-entry, and MUST prompt re-authentication rather than discarding the draft.
- **FR-017**: The portal MUST render an unrecognized/unknown backend status as a generic "Pending Review" state, including the raw status/reason text, rather than failing to display or misrepresenting it as one of the four known outcomes.
- **FR-019**: The portal MUST give each claim history table row enough vertical spacing that its status badge and violation tag(s) read as clearly separated from adjacent rows, rather than appearing crowded or overlapping.
- **FR-020**: The portal MUST present the claim form's submit action as a visually integrated part of the form (e.g., directly attached to the fields above it) rather than as an isolated element surrounded by excess empty space.
- **FR-021**: The portal MUST NOT surround page content with a disproportionate amount of empty page area on taller viewports, while preserving the comfortable internal spacing within the form and table established by FR-015's mobile/desktop usability requirement.

### Key Entities

- **Expense Claim (UI representation)**: The employee-facing view of a claim — employee name, amount, category, expense date, receipt reference (file or link), current status badge, violation reason(s), and submission timestamp.
- **Status Badge**: A visual indicator mapping a backend evaluation outcome to one of "Auto-Approved," "Requires Manager," "Audit Flagged," "Rejected," or a fallback "Pending Review" state.
- **Violation Indicator**: A visual tag representing a single policy violation reason attached to a claim (e.g., "over category cap," "missing receipt," "weekend policy").
- **Receipt Attachment**: Either an uploaded file (with type/size constraints) or a pasted link, associated with a single claim.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An employee can complete and submit a new, valid expense claim in under 90 seconds.
- **SC-002**: 100% of submitted claims display a decision or an explicit in-progress/error state within 5 seconds of submission under normal network conditions — the employee is never left without feedback.
- **SC-003**: At least 95% of field-level input errors (invalid amount, missing/future date, missing required receipt) are caught by the portal before submission, without needing a backend round-trip.
- **SC-004**: Employees can correctly identify why a claim was not auto-approved, using only the on-screen violation indicators, in 100% of flagged/rejected cases.
- **SC-005**: The portal remains fully operable (submit, attach receipt, view history) on a mobile-width screen with no loss of functionality compared to desktop.
- **SC-006**: Zero duplicate claim submissions are recorded as a result of repeated/accidental submit actions.

## Assumptions

- The backend expense-claim API (per the existing Corporate Expense Reimbursement & Policy Engine feature) already exposes endpoints to submit a claim, receive a policy evaluation outcome, and list an employee's claim history; this feature is the web client consuming that API, not a redefinition of it.
- The four portal-facing status labels ("Auto-Approved," "Requires Manager," "Audit Flagged," "Rejected") are presentation-layer labels the portal maps from whatever status values the backend returns (e.g., `auto_approved`, `pending_review`, `needs_information`/manager escalation, `rejected`); exact backend-to-label mapping is a design detail resolved during planning, not a business ambiguity.
- Employee identity/authentication is provided by an existing corporate sign-in system; this feature assumes a signed-in employee context is available and does not define the login mechanism itself. Until that sign-in feature ships, the employee's name is captured directly on the claim form (FR-001, FR-018) as an interim measure; this typed name is not itself an authentication mechanism.
- Receipt file constraints (accepted types, maximum size) follow reasonable common defaults (e.g., image and PDF formats, a modest size cap) unless the backend policy configuration specifies otherwise.
- "Requires Manager" and "Audit Flagged" are treated as two distinct non-auto-approved outcomes the backend can return (e.g., routine manager review vs. a more serious audit-flagged violation); this feature displays whichever distinct statuses the backend provides without altering the underlying review workflow.
- Only the currently signed-in employee's own claims are shown in their claim history; any reviewer/manager-facing review queue or dashboard is out of scope for this feature (it is covered by the existing backend/reviewer capability, not this employee-facing portal).
