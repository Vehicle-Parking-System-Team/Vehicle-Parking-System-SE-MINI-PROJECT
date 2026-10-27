"""Deterministic ordinary parking fees used by the US-10 checkout integration."""

from decimal import Decimal

from common.exceptions import Conflict


HOUR_MICROSECONDS = 3_600_000_000
MAX_FEE = Decimal('999999999999.99')


def elapsed_microseconds(duration):
    value = (duration.days * 86400 + duration.seconds) * 1_000_000 + duration.microseconds
    if value < 0:
        raise Conflict('Checkout time cannot precede check-in time.')
    return value


def billable_hours(duration, grace_period_minutes):
    if type(grace_period_minutes) is not int or grace_period_minutes < 0:
        raise Conflict('The configured grace period is invalid.')
    elapsed = elapsed_microseconds(duration)
    if elapsed <= grace_period_minutes * 60_000_000:
        return 0
    return (elapsed + HOUR_MICROSECONDS - 1) // HOUR_MICROSECONDS


def calculate_parking_fee(duration, hourly_rate, grace_period_minutes):
    if (
        not isinstance(hourly_rate, Decimal) or not hourly_rate.is_finite()
        or hourly_rate < 0 or hourly_rate > Decimal('99999999.99')
        or hourly_rate != hourly_rate.quantize(Decimal('0.01'))
    ):
        raise Conflict('The configured hourly rate is invalid.')
    amount = hourly_rate * billable_hours(duration, grace_period_minutes)
    if amount > MAX_FEE:
        raise Conflict('The parking fee exceeds the supported amount.')
    return amount.quantize(Decimal('0.01'))
