"""US-03 account-change event contract and best-effort signal dispatcher."""
import logging
from dataclasses import dataclass
from typing import Any, Dict

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
    """Notify downstream consumers without failing an already-persisted request.

    Receivers are best-effort. A receiver exception is logged and does not turn
    a successful database mutation into an HTTP 500. Durable delivery belongs
    in a transactional outbox if a future requirement demands guaranteed delivery.
    """
    for receiver, result in user_account_changed.send_robust(
        sender=UserAccountChangeEvent, event=event
    ):
        if isinstance(result, Exception):
            logger.error(
                "Account change receiver %r failed for event %s (target id=%s)",
                receiver,
                event.event_type,
                event.target_user_id,
                exc_info=(type(result), result, result.__traceback__),
            )
    logger.info(
        "User account change event: actor=%s (id=%d) target=%s (id=%d) type=%s previous=%s new=%s timestamp=%s",
        event.actor_username,
        event.actor_id,
        event.target_username,
        event.target_user_id,
        event.event_type,
        event.previous_state,
        event.new_state,
        event.timestamp,
    )
