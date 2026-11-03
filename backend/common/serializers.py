from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = (
            'id', 'occurred_at', 'actor_id', 'actor_username', 'actor_role',
            'ip_address', 'event_type', 'resource_type', 'resource_id', 'details',
        )
        read_only_fields = fields
