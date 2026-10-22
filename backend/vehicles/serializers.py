from rest_framework import serializers
from common.exceptions import Conflict
from vehicles.models import Vehicle
from vehicles.services import normalize_registration_number


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
            'registration_number': {'required': False},
        }

    def validate(self, attrs):
        # Resolve plate from either registration_number or plate_number
        raw_reg = attrs.get('registration_number') or attrs.get('plate_number')
        if not raw_reg or not str(raw_reg).strip():
            raise serializers.ValidationError(
                {'registration_number': ['This field is required.']}
            )

        normalized = normalize_registration_number(raw_reg)
        if len(normalized) > 20:
            raise serializers.ValidationError(
                {'registration_number': ['Ensure this field has no more than 20 characters.']}
            )

        attrs['registration_number'] = normalized
        # Remove write-only alias from validated attrs
        attrs.pop('plate_number', None)

        if 'owner_name' in attrs and isinstance(attrs['owner_name'], str):
            attrs['owner_name'] = attrs['owner_name'].strip()
        if 'owner_phone' in attrs and isinstance(attrs['owner_phone'], str):
            attrs['owner_phone'] = attrs['owner_phone'].strip()

        # Check for duplicate registration before database write (returns HTTP 409 Conflict)
        if Vehicle.objects.filter(registration_number=normalized).exists():
            raise Conflict('A vehicle with this registration number already exists.')

        return attrs

    def create(self, validated_data):
        # Prevent client from overriding owner from payload
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['owner'] = request.user
            if not validated_data.get('owner_name'):
                validated_data['owner_name'] = request.user.get_full_name() or request.user.username

        return super().create(validated_data)
