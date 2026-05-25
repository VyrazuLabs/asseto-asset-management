from rest_framework import serializers
from gate_pass.models import GatePass

class SearchGatePassSerializer(serializers.Serializer):
    """Validates the search_text query parameter for gate pass search."""

    search_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        attrs['search_text'] = attrs.get('search_text') or ''
        return attrs
    
class GatePassCreateSerializer(serializers.Serializer):
    asset_id = serializers.UUIDField(required=True)
    movement_type = serializers.ChoiceField(choices=[(0,'Outward'),(1,'Inward')], required=True)
    destination_vendor_id = serializers.UUIDField(required=True)
    expected_return_date = serializers.DateField(required=False, allow_null=True)
    purpose_of_movement = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)
    raised_by_id = serializers.UUIDField(required=False, allow_null=True)
    authorised_by_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=[(0,'Pending'),(1,'Approved'),(2,'Draft'),(3,'Rejected')], required=False, default=0)
    class Meta:
        fields = ['asset_id', 'movement_type', 'destination_vendor_id', 'expected_return_date', 'purpose_of_movement', 'raised_by_id', 'authorised_by_id', 'status']

    def create(self, validated_data):
        """Create a GatePass scoped to the request user's organization."""
        request = self.context.get('request')
        return GatePass.objects.create(
            organization=request.user.organization,
            asset_id=validated_data.get('asset_id'),
            movement_type=validated_data.get('movement_type'),
            destination_vendor_id=validated_data.get('destination_vendor_id'),
            expected_return_date=validated_data.get('expected_return_date'),
            purpose_of_movement=validated_data.get('purpose_of_movement'),
            raised_by_id=validated_data.get('raised_by_id'),
            authorised_by_id=validated_data.get('authorised_by_id'),
            status=validated_data.get('status', 0),
        )