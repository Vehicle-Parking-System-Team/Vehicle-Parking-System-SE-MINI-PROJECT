"""Deterministic ordinary parking fees used by checkout."""

from decimal import Decimal, ROUND_HALF_UP

from common.exceptions import Conflict


HOUR_MICROSECONDS = 3_600_000_000
MAX_HOURLY_RATE = Decimal('99999999.99')
MAX_VEHICLE_MULTIPLIER = Decimal('999.99')
MAX_FEE = Decimal('999999999999.99')
CENT = Decimal('0.01')
DEFAULT_VEHICLE_MULTIPLIER = Decimal('1.00')


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


def calculate_parking_fee(
    duration,
    hourly_rate,
    grace_period_minutes,
    vehicle_multiplier=DEFAULT_VEHICLE_MULTIPLIER,
):
    if (
        not isinstance(hourly_rate, Decimal) or not hourly_rate.is_finite()
        or hourly_rate < 0 or hourly_rate > MAX_HOURLY_RATE
        or hourly_rate != hourly_rate.quantize(CENT)
    ):
        raise Conflict('The configured hourly rate is invalid.')
    if (
        not isinstance(vehicle_multiplier, Decimal)
        or not vehicle_multiplier.is_finite()
        or vehicle_multiplier < 0 or vehicle_multiplier > MAX_VEHICLE_MULTIPLIER
        or vehicle_multiplier != vehicle_multiplier.quantize(CENT)
    ):
        raise Conflict('The configured vehicle multiplier is invalid.')

    amount = hourly_rate * billable_hours(duration, grace_period_minutes) * vehicle_multiplier
    if amount > MAX_FEE:
        raise Conflict('The parking fee exceeds the supported amount.')
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)
