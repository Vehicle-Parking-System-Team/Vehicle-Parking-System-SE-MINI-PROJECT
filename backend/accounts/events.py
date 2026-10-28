"""
US-03 Account Change Events and Integration Contract.
Provides dispatch hooks for Member 4's US-25 (Admin Dashboard) and US-29 (Security Audit Log).
"""

from dataclasses import dataclass
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserAccountChangeEvent:
    """
    Contract for user account modification events.
    Fields:
      actor_id: ID of the administrator performing the action.
      actor_username: Username of the administrator.
      target_user_id: ID of the user account being created/modified.
      target_username: Username of the affected user.
      event_type: 'USER_CREATED', 'STATUS_CHANGED', 'ROLE_CHANGED', or 'ACCOUNT_UPDATED'.
      previous_state: Dictionary of attributes before modification.
      new_state: Dictionary of attributes after modification.
      timestamp: ISO 8601 formatted timestamp string.
    """
    actor_id: int
    actor_username: str
    target_user_id: int
    target_username: str
    event_type: str
    previous_state: Dict[str, Any]
    new_state: Dict[str, Any]
    timestamp: str


def dispatch_user_account_change(event: UserAccountChangeEvent) -> None:
    """
    Dispatch hook for account changes.
    Member 4 can subscribe or attach audit logging handlers to this dispatcher.
    """
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
