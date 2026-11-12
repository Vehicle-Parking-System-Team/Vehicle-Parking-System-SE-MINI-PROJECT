from rest_framework import serializers

from .models import AuditEvent


class AuditEventFilterSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=100, required=False)
    actor_id = serializers.CharField(max_length=64, required=False)
    actor = serializers.CharField(max_length=150, required=False)
    resource_type = serializers.CharField(max_length=100, required=False)
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if 'start' in attrs and 'end' in attrs and attrs['start'] >= attrs['end']:
            raise serializers.ValidationError({'end': 'End must be later than start.'})
        return attrs


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = (
            'id', 'occurred_at', 'actor_id', 'actor_username', 'actor_role',
            'ip_address', 'event_type', 'resource_type', 'resource_id', 'details',
        )
        read_only_fields = fields
