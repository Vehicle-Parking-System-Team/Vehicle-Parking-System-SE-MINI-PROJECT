"""Small, secret-safe entry point for recording audit events."""

from .models import AuditEvent


def record_audit_event(
    event_type,
    *,
    actor=None,
    request=None,
    resource_type='',
    resource_id='',
    details=None,
):
    """Persist an event without copying request bodies, credentials, or headers."""
    ip_address = None
    if request is not None:
        # REMOTE_ADDR is the connected peer. Do not trust user-supplied X-Forwarded-For.
        ip_address = request.META.get('REMOTE_ADDR') or None

    actor_is_authenticated = bool(actor and getattr(actor, 'is_authenticated', False))
    return AuditEvent.objects.create(
        actor_id=str(actor.pk) if actor_is_authenticated else None,
        actor_username=actor.get_username() if actor_is_authenticated else '',
        actor_role=getattr(actor, 'role', '') if actor_is_authenticated else '',
        ip_address=ip_address,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else '',
        details=details or {},
    )
