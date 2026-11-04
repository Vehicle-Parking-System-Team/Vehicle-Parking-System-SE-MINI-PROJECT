"""Query validation for read-only occupancy and revenue reports."""

from datetime import timedelta
from zoneinfo import ZoneInfo

from rest_framework import serializers

from billing.models import BillingReceipt
from vehicles.models import Vehicle

REPORT_TIMEZONE = ZoneInfo('Asia/Kolkata')


class OccupancyQuerySerializer(serializers.Serializer):
    start = serializers.DateTimeField(default_timezone=REPORT_TIMEZONE)
    end = serializers.DateTimeField(default_timezone=REPORT_TIMEZONE)
    interval = serializers.ChoiceField(choices=('hour', 'day'), default='day')
    zone = serializers.IntegerField(min_value=1, required=False)

    def validate(self, attrs):
        if attrs['end'] <= attrs['start']:
            raise serializers.ValidationError({'end': 'End must be later than start.'})
        if attrs['end'] - attrs['start'] > timedelta(days=366):
            raise serializers.ValidationError({'end': 'Request at most 366 days per report.'})
        return attrs


class RevenueQuerySerializer(serializers.Serializer):
    start = serializers.DateTimeField(default_timezone=REPORT_TIMEZONE)
    end = serializers.DateTimeField(default_timezone=REPORT_TIMEZONE)
    interval = serializers.ChoiceField(choices=('hour', 'day'), default='day')
    payment_method = serializers.ChoiceField(choices=BillingReceipt.PaymentMethod.choices, required=False)
    vehicle_type = serializers.ChoiceField(choices=Vehicle.VEHICLE_TYPE_CHOICES, required=False)

    def validate(self, attrs):
        if attrs['end'] <= attrs['start']:
            raise serializers.ValidationError({'end': 'End must be later than start.'})
        if attrs['end'] - attrs['start'] > timedelta(days=366):
            raise serializers.ValidationError({'end': 'Request at most 366 days per report.'})
        return attrs


class ExportQuerySerializer(OccupancyQuerySerializer):
    report = serializers.ChoiceField(choices=('logs', 'occupancy', 'revenue'), default='logs')
    export_format = serializers.ChoiceField(choices=('csv', 'pdf'), default='csv')
    status = serializers.ChoiceField(choices=('ACTIVE', 'COMPLETED'), required=False)
    payment_method = serializers.ChoiceField(choices=BillingReceipt.PaymentMethod.choices, required=False)
    vehicle_type = serializers.ChoiceField(choices=Vehicle.VEHICLE_TYPE_CHOICES, required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        allowed = {
            'logs': {'zone', 'status', 'vehicle_type'},
            'occupancy': {'zone', 'interval'},
            'revenue': {'payment_method', 'vehicle_type', 'interval'},
        }[attrs['report']]
        for field in self.initial_data:
            if field not in allowed | {'report', 'export_format', 'start', 'end'}:
                raise serializers.ValidationError({field: 'Unsupported filter for this report.'})
        return attrs
