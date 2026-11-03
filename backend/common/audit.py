"""Record explicit server-selected audit fields; never copy request payloads."""

from ipaddress import ip_address as parse_ip_address

from .models import AuditEvent


EVENT_DETAIL_FIELDS = {
    'auth.login_succeeded': {'outcome'},
    'auth.login_failed': {'outcome'},
    'auth.logout': {'outcome'},
    'auth.password_changed': set(),
    'account.created': {'role', 'status'},
    'account.updated': {'previous_state', 'new_state'},
    'parking_slot.maintenance_changed': {'previous_status', 'status'},
    'parking_zone.deactivated': {'previous_is_active', 'is_active', 'affected_slot_count'},
    'billing.payment_recorded': {'payment_status', 'payment_method', 'payment_amount'},
    'billing.fee_waived': {'payment_status', 'fee_amount'},
    'reservation.cancelled': {'previous_status', 'status'},
    'tariff.created': {'new_state'},
    'tariff.updated': {'previous_state', 'new_state'},
}

STATE_FIELDS = {
    'role', 'status', 'vehicle_type', 'hourly_rate',
    'vehicle_multiplier', 'grace_period_minutes',
    'penalty_fee',
}


def _validated_details(event_type, details):
    allowed = EVENT_DETAIL_FIELDS.get(event_type)
    if allowed is None:
        raise ValueError('Unknown audit event type.')
    details = {} if details is None else details
    if not isinstance(details, dict) or details.keys() - allowed:
        raise ValueError('Unexpected audit detail fields.')
    for key, value in details.items():
        if key in ('previous_state', 'new_state'):
            if not isinstance(value, dict) or value.keys() - STATE_FIELDS:
                raise ValueError('Unexpected audit state fields.')
            if any(not isinstance(item, (str, int, bool, type(None))) for item in value.values()):
                raise ValueError('Audit state must contain scalar values.')
        elif not isinstance(value, (str, int, bool, type(None))):
            raise ValueError('Audit details must contain scalar values.')
    return details


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
    details = _validated_details(event_type, details)
    ip_address = None
    if request is not None:
        # REMOTE_ADDR is the connected peer. Do not trust user-supplied X-Forwarded-For.
        try:
            ip_address = str(parse_ip_address(request.META.get('REMOTE_ADDR')))
        except ValueError:
            pass

    actor_is_authenticated = bool(actor and getattr(actor, 'is_authenticated', False))
    return AuditEvent.objects.create(
        actor_id=str(actor.pk) if actor_is_authenticated else None,
        actor_username=actor.get_username() if actor_is_authenticated else '',
        actor_role=getattr(actor, 'role', '') if actor_is_authenticated else '',
        ip_address=ip_address,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else '',
        details=details,
    )
