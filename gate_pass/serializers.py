from rest_framework import serializers
from gate_pass.models import GatePass

class SearchGatePassSerializer(serializers.Serializer):
    search_text = serializers.CharField(required=False, allow_blank=True,allow_null=True)

    class Meta:
        fields = ['search_text']
    
    def validate(self, search_text):
        if not search_text:
            return []
        return search_text
    
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
        asset=validated_data.get('asset_id')
        movement_type=validated_data.get('movement_type')
        destination_vendor_id=validated_data.get('destination_vendor_id')
        expected_return_date=validated_data.get('expected_return_date')
        purpose_of_movement=validated_data.get('purpose_of_movement')
        raised_by_id=validated_data.get('raised_by_id')
        authorised_by_id=validated_data.get('authorised_by_id')
        status=validated_data.get('status')
        gate_pass=GatePass.objects.create(
            asset_id=asset,
            movement_type=movement_type,
            destination_vendor_id=destination_vendor_id,    
            expected_return_date=expected_return_date,    
            purpose_of_movement=purpose_of_movement,    
            raised_by_id=raised_by_id,    
            authorised_by_id=authorised_by_id,    
            status=status,    
        )
        return gate_pass