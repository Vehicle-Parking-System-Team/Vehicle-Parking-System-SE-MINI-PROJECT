from rest_framework import serializers
from common.exceptions import Conflict
from vehicles.models import Vehicle
from vehicles.services import normalize_registration_number, is_valid_registration_number


class VehicleSerializer(serializers.ModelSerializer):
    """
    Serializer for vehicle registration and profile representation.
    Ensures safe ownership derivation from authenticated user and validates
    canonical vehicle types (Two-Wheeler, Compact, SUV, EV Charging).
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

    def validate(self, attrs):
        # Resolve plate from either registration_number or plate_number
        has_plate_key = 'registration_number' in attrs or 'plate_number' in attrs
        raw_reg = attrs.get('registration_number') or attrs.get('plate_number')

        if self.partial and not has_plate_key:
            # During partial update (PATCH), if plate is not provided, registration_number remains unchanged
            pass
        else:
            if not raw_reg or not str(raw_reg).strip():
                raise serializers.ValidationError(
                    {'registration_number': ['This field is required.']}
                )

            normalized = normalize_registration_number(raw_reg)
            if len(normalized) > 20:
                raise serializers.ValidationError(
                    {'registration_number': ['Ensure this field has no more than 20 characters.']}
                )

            if not is_valid_registration_number(normalized):
                raise serializers.ValidationError(
                    {'registration_number': ['Invalid vehicle registration number format. Supported formats include standard state plates (e.g. KA-01-AB-1234, DL3CBB1122) and BH-series (e.g. 22-BH-1234-AA).']}
                )

            attrs['registration_number'] = normalized

            # Check for duplicate registration before database write (returns HTTP 409 Conflict)
            duplicate_qs = Vehicle.objects.filter(registration_number=normalized)
            if self.instance:
                duplicate_qs = duplicate_qs.exclude(pk=self.instance.pk)
            if duplicate_qs.exists():
                raise Conflict('A vehicle with this registration number already exists.')

        # Remove write-only alias from validated attrs
        attrs.pop('plate_number', None)

        if 'owner_name' in attrs and isinstance(attrs['owner_name'], str):
            attrs['owner_name'] = attrs['owner_name'].strip()
        if 'owner_phone' in attrs and isinstance(attrs['owner_phone'], str):
            attrs['owner_phone'] = attrs['owner_phone'].strip()

        return attrs

    def create(self, validated_data):
        # Prevent client from overriding owner from payload
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['owner'] = request.user
            if not validated_data.get('owner_name'):
                validated_data['owner_name'] = request.user.get_full_name() or request.user.username

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Ensure owner is immutable through vehicle profile updates
        validated_data.pop('owner', None)
        return super().update(instance, validated_data)


class VehicleParkingStatusSerializer(serializers.Serializer):
    """
    Serializer representing real-time parking status for a vehicle (FR-11 / US-07).
    """
    is_parked = serializers.BooleanField()
    status = serializers.CharField()
    session_id = serializers.IntegerField(allow_null=True, required=False)
    check_in_time = serializers.CharField(allow_null=True, required=False)
    slot = serializers.DictField(allow_null=True, required=False)
    message = serializers.CharField()


class VehicleSearchResultSerializer(serializers.ModelSerializer):
    """
    Serializer for US-07 / FR-11 vehicle search results.
    Combines core vehicle profile details with active parking status.
    """
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
