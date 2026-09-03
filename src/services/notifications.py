"""Employee notification dispatch (FR-011).

Per spec Assumptions, delivery rides whatever notification channel the organization already
has (e.g., email) — the specific mechanism is out of scope for this feature. This module is
the single seam where that integration would be wired in; for now it records dispatched
notifications in-memory so callers/tests can assert one was triggered.
"""

import uuid
from dataclasses import dataclass, field


@dataclass
class DispatchedNotification:
    claim_id: uuid.UUID
    recipient_id: str
    message: str


@dataclass
class NotificationDispatcher:
    sent: list[DispatchedNotification] = field(default_factory=list)

    def notify_status_change(self, claim_id: uuid.UUID, recipient_id: str, new_status: str) -> None:
        self.sent.append(
            DispatchedNotification(
                claim_id=claim_id,
                recipient_id=recipient_id,
                message=f"Your claim {claim_id} status changed to {new_status}",
            )
        )


default_dispatcher = NotificationDispatcher()
