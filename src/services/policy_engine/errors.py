"""Domain errors raised by the pure policy-engine layer. Transport-agnostic (constitution
Article III.1) — src/api/ maps these to HTTP status codes; a CLI or test harness can catch
them directly with no HTTP concept involved.
"""


class DomainValidationError(Exception):
    """Invalid input: malformed claim data, or a decision missing a required rejection reason.
    API layer maps this to HTTP 422."""


class SelfReviewError(Exception):
    """FR-018: a reviewer attempted to decide on their own submitted claim.
    API layer maps this to HTTP 403."""


class AlreadyDecidedError(Exception):
    """FR-019: the claim already left pending_review/needs_information via another decision
    or a withdrawal. API layer maps this to HTTP 409."""


class NotFoundError(Exception):
    """The referenced claim does not exist. API layer maps this to HTTP 404."""
