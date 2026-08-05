import re

from rest_framework import serializers

from .models import CustomFieldDefinition, CustomFieldValue


class CustomFieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFieldDefinition
        fields = [
            "id", "module", "field_label", "field_key", 
            "field_type", "is_required", "is_active", "created_at"
        ]
        read_only_fields = ["id", "created_at", "field_key"]

    @staticmethod
    def build_field_key(module, label):
        slug = re.sub(r"[^a-z0-9]+", "_", (label or "").lower()).strip("_")
        slug = re.sub(r"_+", "_", slug)
        key = f"{module}_{slug}" if module and slug else (module or "")
        return key[:100].strip("_")

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        module = attrs.get("module", getattr(instance, "module", None))
        label = attrs.get("field_label", getattr(instance, "field_label", None))
        attrs["field_key"] = (
            instance.field_key if instance else self.build_field_key(module, label)
        )
        return attrs

    def validate_field_key(self, value):
        # Ignore any client-supplied key; the value is always auto-generated.
        return value

class CustomFieldValueSerializer(serializers.ModelSerializer):
    field_key = serializers.CharField(source="definition.field_key", read_only=True)
    
    class Meta:
        model = CustomFieldValue
        fields = ["id", "entity_uuid", "field_key", "value_text", "created_at"]
        read_only_fields = ["id", "created_at"]
