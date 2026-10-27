from django.urls import reverse
from rest_framework import serializers

from .models import BillingReceipt


class GenerateReceiptRequestSerializer(serializers.Serializer):
    record_id = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        extra_fields = set(self.initial_data) - {'record_id'}
        if extra_fields:
            raise serializers.ValidationError({
                field: 'This field is not accepted.' for field in extra_fields
            })
        return attrs


class BillingReceiptSerializer(serializers.ModelSerializer):
    receipt_id = serializers.UUIDField(source='receipt_number', read_only=True)
    invoice_number = serializers.CharField(read_only=True)
    parking_record_id = serializers.IntegerField(read_only=True)
    total_fee = serializers.DecimalField(
        source='fee_amount', max_digits=14, decimal_places=2, read_only=True,
    )
    duration_display = serializers.SerializerMethodField()
    print_url = serializers.SerializerMethodField()

    class Meta:
        model = BillingReceipt
        fields = [
            'receipt_id', 'invoice_number', 'parking_record_id',
            'registration_number', 'vehicle_type', 'slot_number', 'zone_name',
            'check_in_time', 'check_out_time', 'duration_seconds',
            'duration_display', 'billable_hours', 'hourly_rate', 'base_amount',
            'vehicle_multiplier', 'multiplier_adjustment', 'grace_period_minutes',
            'total_fee',
            'currency', 'created_at', 'print_url',
        ]
        read_only_fields = fields

    def get_duration_display(self, receipt):
        hours, remaining = divmod(receipt.duration_seconds, 3600)
        minutes, seconds = divmod(remaining, 60)
        parts = []
        if hours:
            parts.append(f'{hours}h')
        if minutes:
            parts.append(f'{minutes}m')
        if seconds or not parts:
            parts.append(f'{seconds}s')
        return ' '.join(parts)

    def get_print_url(self, receipt):
        return reverse(
            'billing:receipt-print',
            kwargs={'receipt_number': receipt.receipt_number},
        )
