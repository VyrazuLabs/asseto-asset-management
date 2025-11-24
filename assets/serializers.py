import json
from rest_framework import serializers
from assets.models import Asset, AssetImage, AssetStatus
from dashboard.models import CustomField
class CustomFieldSerializer(serializers.Serializer):
    field_name = serializers.CharField()
    field_value = serializers.CharField()
class AssetSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    images = serializers.ListField(
        child=serializers.ImageField(required=False, allow_null=True),
        required=False,
        allow_empty=True,
        allow_null=True,
        default=list,
    )
    custom_fields = CustomFieldSerializer(required=False)

    class Meta:
        model = Asset
        fields = [
            'tag', 'name', 'product', 'vendor', 'location', 'serial_no',
            'price', 'purchase_type', 'purchase_date', 'warranty_expiry_date',
            'images', 'custom_fields'
        ]

    # Fix: Only decode, never remove or pop keys in to_internal_value
    def to_internal_value(self, data):
        data = data.copy()
        if (data.get("images") or "") == "":
            data.pop("images", None)
        custom_field_list = json.loads(f"[{data['custom_fields']}]")
        data["custom_fields"] = custom_field_list
        
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
        custom_fields = self.initial_data.get("custom_fields",[])
        custom_field_list = json.loads(f"[{custom_fields}]")
        get_asset_status = AssetStatus.objects.get(name="Available")
        asset = Asset.objects.create(
            **validated_data,
            organization=self.context["request"].user.organization,
            asset_status=get_asset_status
        )
        asset_images = None
        for image in images:
            asset_images = AssetImage.objects.create(image=image, asset=asset)
        for custom_field in custom_field_list:
            CustomField.objects.create(
                name=custom_field['field_name'],
                object_id=asset.id,
                field_type='text',
                field_name=custom_field['field_name'],
                field_value=custom_field['field_value'],
                entity_type='asset',
                organization=self.context["request"].user.organization
            )
        return asset

    def update(self, instance, validated_data):
        image_data = validated_data.pop('images', None)
        for attribute, value in validated_data.items():
            setattr(instance, attribute, value)
        instance.save()
        if image_data is not None:
            for image in image_data:
                AssetImage.objects.create(asset=instance, image=image)
        return instance
