from rest_framework import serializers
from .models import CustomFieldDefinition, CustomFieldValue

class CustomFieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFieldDefinition
        fields = [
            "id", "module", "field_label", "field_key", 
            "field_type", "is_required", "is_active", "created_at"
        ]
        read_only_fields = ["id", "created_at"]

class CustomFieldValueSerializer(serializers.ModelSerializer):
    field_key = serializers.CharField(source="definition.field_key", read_only=True)
    
    class Meta:
        model = CustomFieldValue
        fields = ["id", "entity_uuid", "field_key", "value_text", "created_at"]
        read_only_fields = ["id", "created_at"]
