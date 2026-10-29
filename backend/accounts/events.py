"""
US-03 account-change events.

The Django signal is the integration boundary for dashboard/audit consumers.
The default dispatcher also emits a structured log record; consumers can connect
receivers without coupling the accounts app to their implementation.
"""
from dataclasses import dataclass
from typing import Any, Dict
import logging

from django.dispatch import Signal

logger = logging.getLogger(__name__)
user_account_changed = Signal()


@dataclass
class UserAccountChangeEvent:
    actor_id: int
    actor_username: str
    target_user_id: int
    target_username: str
    event_type: str
    previous_state: Dict[str, Any]
    new_state: Dict[str, Any]
    timestamp: str


def dispatch_user_account_change(event: UserAccountChangeEvent) -> None:
    """Emit the event to registered Django signal receivers and log it."""
    # Receivers are best-effort; one failing consumer must not turn a persisted\n    # account change into an HTTP 500. Failures remain observable in logs.\n    for receiver, result in user_account_changed.send_robust(\n        sender=UserAccountChangeEvent, event=event\n    ):\n        if isinstance(result, Exception):\n            logger.error(\n                'Account change receiver %r failed for event %s (target id=%s)',\n                receiver, event.event_type, event.target_user_id,\n            )
    logger.info(
        "User account change event: actor=%s (id=%d) target=%s (id=%d) type=%s previous=%s new=%s timestamp=%s",
        event.actor_username, event.actor_id, event.target_username, event.target_user_id,
        event.event_type, event.previous_state, event.new_state, event.timestamp,
    )
