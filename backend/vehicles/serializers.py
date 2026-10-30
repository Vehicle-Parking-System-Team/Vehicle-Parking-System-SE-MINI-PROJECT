from collections.abc import Mapping

from rest_framework import serializers

from common.exceptions import Conflict
from vehicles.models import Vehicle
from vehicles.services import (
    normalize_registration_number,
    is_valid_registration_number,
    registration_number_comparison_key,
    vehicle_registration_exists,
)


# These values are server-owned. They may appear in legacy clients' payloads,
# but are intentionally ignored and can never change vehicle ownership/metadata.
SERVER_MANAGED_INPUT_KEYS = {
    'owner', 'owner_id', 'owner_username', 'user', 'user_id',
    'id', 'created_at', 'updated_at',
}
STRING_INPUT_FIELDS = {
    'registration_number', 'plate_number', 'vehicle_type', 'owner_name', 'owner_phone',
}


class VehicleSerializer(serializers.ModelSerializer):
    """
    Strict vehicle payload schema shared by registration (US-05) and profile
    updates (US-06). US-08 adds canonical plate validation and safe sanitization.
    """

    plate_number = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='Alternative key for registration_number.',
    )
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id',
            'registration_number',
            'plate_number',
            'vehicle_type',
            'owner',
            'owner_username',
            'owner_name',
            'owner_phone',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'owner_username', 'created_at', 'updated_at']
        extra_kwargs = {
            'registration_number': {
                'required': False,
                'validators': [],
            },
        }

    def to_internal_value(self, data):
        """Reject unknown keys and non-string scalar inputs before DRF coercion."""
        if isinstance(data, Mapping):
            allowed = set(self.fields.keys()) | SERVER_MANAGED_INPUT_KEYS
            unknown = sorted(set(data.keys()) - allowed)
            if unknown:
                raise serializers.ValidationError({
                    'non_field_errors': [
                        f'Unknown field(s): {", ".join(unknown)}.'
                    ]
                })

            type_errors = {
                field: ['Expected a string.']
                for field in STRING_INPUT_FIELDS
                if field in data and not isinstance(data[field], str)
            }
            if type_errors:
                raise serializers.ValidationError(type_errors)

        return super().to_internal_value(data)

    def validate(self, attrs):
        has_registration = 'registration_number' in attrs
        has_alias = 'plate_number' in attrs
        has_plate_key = has_registration or has_alias

        if self.partial and not has_plate_key:
            # PATCH may update contact/type fields without resubmitting the plate.
            pass
        else:
            raw_registration = (
                attrs.get('registration_number')
                if has_registration
                else attrs.get('plate_number')
            )
            if not raw_registration or not raw_registration.strip():
                raise serializers.ValidationError({
                    'registration_number': ['This field is required.']
                })

            normalized = normalize_registration_number(raw_registration)

            if has_registration and has_alias:
                normalized_alias = normalize_registration_number(attrs['plate_number'])
                if len(normalized_alias) > 20 or not is_valid_registration_number(normalized_alias):
                    raise serializers.ValidationError({
                        'plate_number': [
                            'Invalid vehicle registration number format.'
                        ]
                    })
                if registration_number_comparison_key(normalized) != registration_number_comparison_key(normalized_alias):
                    raise serializers.ValidationError({
                        'registration_number': [
                            'registration_number and plate_number must identify the same vehicle.'
                        ]
                    })

            if len(normalized) > 20:
                raise serializers.ValidationError({
                    'registration_number': [
                        'Ensure this field has no more than 20 characters.'
                    ]
                })

            if not is_valid_registration_number(normalized):
                raise serializers.ValidationError({
                    'registration_number': [
                        'Invalid vehicle registration number format. Supported formats include standard state plates (e.g. KA-01-AB-1234, DL3CBB1122) and BH-series (e.g. 22-BH-1234-AA).'
                    ]
                })

            attrs['registration_number'] = normalized

            # Fast user-friendly check; the database constraint remains
            # authoritative when concurrent requests race after this query.
            if vehicle_registration_exists(
                normalized,
                exclude_vehicle_id=self.instance.pk if self.instance else None,
            ):
                raise Conflict('A vehicle with this registration number already exists.')

        attrs.pop('plate_number', None)

        if 'owner_name' in attrs:
            attrs['owner_name'] = attrs['owner_name'].strip()
        if 'owner_phone' in attrs:
            attrs['owner_phone'] = attrs['owner_phone'].strip()

        return attrs

    def create(self, validated_data):
        # Ownership always comes from the authenticated principal, never payload.
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['owner'] = request.user
            if not validated_data.get('owner_name'):
                validated_data['owner_name'] = request.user.get_full_name() or request.user.username

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Ownership and server-managed fields are immutable through profile updates.
        validated_data.pop('owner', None)
        return super().update(instance, validated_data)


class VehicleParkingStatusSerializer(serializers.Serializer):
    """Serializer representing real-time parking status for a vehicle (FR-11 / US-07)."""

    is_parked = serializers.BooleanField()
    status = serializers.CharField()
    session_id = serializers.IntegerField(allow_null=True, required=False)
    check_in_time = serializers.CharField(allow_null=True, required=False)
    slot = serializers.DictField(allow_null=True, required=False)
    message = serializers.CharField()


class VehicleSearchResultSerializer(serializers.ModelSerializer):
    """Serializer for US-07 / FR-11 vehicle search results."""

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    parking_status = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id',
            'registration_number',
            'vehicle_type',
            'owner',
            'owner_username',
            'owner_name',
            'owner_phone',
            'created_at',
            'updated_at',
            'parking_status',
        ]
        read_only_fields = fields

    def get_parking_status(self, obj):
        context_status = self.context.get('parking_status')
        if context_status is not None:
            return context_status
        from vehicles.services import get_vehicle_parking_status
        return get_vehicle_parking_status(obj)
