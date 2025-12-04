import json
from rest_framework import serializers
from audit.models import Audit, AuditImage
# from dashboard.models import CustomField
# class CustomFieldSerializer(serializers.Serializer):
#     field_name = serializers.CharField()
#     field_value = serializers.CharField()
class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audit
        fields = [
            'audited_by', 'created_at', 'assigned_to', 'asset', 'organization', 'condition', 'notes'
        ]

    # Fix: Only decode, never remove or pop keys in to_internal_value
    def to_internal_value(self, data):
        data = data.copy()
        if (data.get("images") or "") == "":
            data.pop("images", None)
        # custom_field_list = json.loads(f"[{data['custom_fields']}]")
        # data["custom_fields"] = custom_field_list
        
        return super().to_internal_value(data)

    def validate_tag(self, tag):
        if not tag:
            raise serializers.ValidationError("Tag can not be empty")
        return tag

    def validate_name(self, name):
        if not name:
            raise serializers.ValidationError("Name can not be blank")
        return name

    def validate_product(self, product):
        if not product:
            raise serializers.ValidationError("Product can not be blank")
        return product

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        # custom_fields = self.initial_data.get("custom_fields",[])
        audit = Audit.objects.create(
            **validated_data,
            # organization=self.context["request"].user.organization,
        )
        asset_images = None
        for image in images:
            AuditImage.objects.create(image=image, audit=audit)
        return audit

    def update(self, instance, validated_data):
        image_data = validated_data.pop('images', None)
        for attribute, value in validated_data.items():
            if value is None:
                continue
            setattr(instance, attribute, value)
        instance.save()
        if image_data is not None:
            for image in image_data:
                AuditImage.objects.create(audit=instance, image=image)
        
        return instance
