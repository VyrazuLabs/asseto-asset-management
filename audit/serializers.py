import json
from rest_framework import serializers
from audit.models import Audit, AuditImage
from common.convert_base64_image import convert_image
from assets.models import Asset
# from dashboard.models import CustomField
# class CustomFieldSerializer(serializers.Serializer):
#     field_name = serializers.CharField()
#     field_value = serializers.CharField()
class AuditSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(required=False, allow_null=True),
        required=False,
        allow_empty=True,
        allow_null=True,
        default=list,
    )
    class Meta:
        model = Audit
        fields = [
            'images','audited_by', 'created_at', 'assigned_to', 'asset', 'organization', 'condition', 'notes'
        ]

    # Fix: Only decode, never remove or pop keys in to_internal_value
    def to_internal_value(self, data):
        print(type(data), "/////data in to_internal_value", data)
        data = data.copy()
        if (data.get("images") or "") == "":
            data.pop("images", None)

        return super().to_internal_value(data)

    def validate_tag(self, tag):
        get_tag=Asset.objects.filter(tag=tag).exists()
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
        print("images",images)
        # custom_fields = self.initial_data.get("custom_fields",[])
        audit = Audit.objects.create(
            **validated_data,
            # organization=self.context["request"].user.organization,
        )
        print("audit",validated_data,audit)
        asset_images = None
        for image in images:
            # image=convert_image(image)
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
