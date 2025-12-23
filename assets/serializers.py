import json
from rest_framework import serializers
from assets.models import Asset, AssetImage, AssetStatus, AssignAsset
from dashboard.models import CustomField
from common.convert_base64_image import convert_image
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
    custom_fields = serializers.ListField(child=serializers.DictField(), required=False)
    purchase_date = serializers.DateField(required=False, allow_null=True)
    warranty_expiry_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Asset
        fields = [
            'tag', 'name', 'product', 'vendor', 'location', 'serial_no',
            'price', 'purchase_type', 'purchase_date', 'warranty_expiry_date',
            'images', 'custom_fields','description'
        ]

    # Fix: Only decode, never remove or pop keys in to_internal_value
    def to_internal_value(self, data):
        print("to_internal_value",data,"\n")
        data = data.copy()
        if (data.get("images") or "") == "":
            data.pop("images", None)

        for field in ["purchase_date", "warranty_expiry_date"]:
            if data.get(field) == "":
                data[field] = None
        if data.get("custom_fields") in ["", None]:
            data.pop("custom_fields", None)
        elif isinstance(data.get("custom_fields"), str):
            data["custom_fields"] = json.loads(data.get("custom_fields"))[0]

        return super().to_internal_value(data)

    def validate_tag(self, value):
        if self.partial and value in (None, ""):
            return value
        if not value:
            raise serializers.ValidationError("Tag can not be empty")
        return value

    def validate_name(self, value):
        if self.partial and value in (None, ""):
            return value
        if not value:
            raise serializers.ValidationError("Name can not be blank")
        return value

    def validate_product(self, value):
        if "product" in self.initial_data and not value:
            raise serializers.ValidationError("Product can not be blank")
        return value
    
    def validate(self, attrs):
        for field in ["purchase_date", "warranty_expiry_date"]:
            if attrs.get(field) in ["", None]:
                attrs[field] = None
        return attrs

    def create(self, validated_data):
        images = validated_data.pop("images", []) or []
        #custom_fields_raw = request.data.get("custom_fields", "[]")
        #custom_fields = json.loads(custom_fields_raw)
        custom_fields = validated_data.pop("custom_fields", []) or []
        print("custom_fields",custom_fields)
        asset = Asset.objects.create(
            **validated_data,
            organization=self.context["request"].user.organization,
            asset_status=AssetStatus.objects.get(name="Available")
        )

        for image in images:
            AssetImage.objects.create(image=image, asset=asset)

        if custom_fields:
            for custom_field in custom_fields:
                if not custom_field:
                    continue

                field_name, field_value = next(iter(custom_field.items()))

                CustomField.objects.create(
                    name=field_name,
                    object_id=asset.id,
                    field_type='text',
                    field_name=field_name,
                    field_value=field_value,
                    entity_type='asset',
                    organization=self.context["request"].user.organization
                )

        return asset


    def update(self, instance, validated_data):
        print('validate_data is------->',validated_data)
        image_data = validated_data.pop('images', None)
        for attribute, value in validated_data.items():
            if value is None:
                continue
            setattr(instance, attribute, value)
        instance.save()
        if image_data is not None:
            for image in image_data:
                # image=convert_image(image)
                AssetImage.objects.create(asset=instance, image=image)
        custom_fields = validated_data.pop("custom_fields",None)
        print(custom_fields)
        if custom_fields is not None:
            for custom_field in custom_fields:
                field_name=list(custom_field.keys())[0]
                field_value=custom_field[field_name]
                print("field name is:",field_name,"\n","filed_value:",field_value)
                CustomField.objects.update_or_create(object_id=instance.id,field_name=field_name,
                defaults={'field_value':field_value,"entity_type": "asset","field_type": "text","name": field_name})
        return instance


class SearchAssetSerializer(serializers.Serializer):
    search_text=serializers.CharField(required=True)
    class Meta:
        fields=['search_text']
    
    def validate(self, search_text):
        if not search_text:
            return None
        return search_text
class AssignAssetSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(required=False, allow_null=True),
        required=False,
        allow_empty=True,
        allow_null=True,
        default=list,
    )

    def to_internal_value(self, data):
        print("to_internal_value",data,"\n")
        data = data.copy()
        if (data.get("images") or "") == "":
            data.pop("images", None)
        return super().to_internal_value(data)
    
    def validate_user(self,user):
        if not user:
            raise serializers.ValidationError("User must needed")
        return user
        
    def create(self, validated_data):
        print(validated_data)
        asset=validated_data.pop('asset',None)
        asset_images=validated_data.pop('images',[])
        assign_asset=AssignAsset.objects.create(asset=asset,**validated_data)
        asset.is_assigned=True
        asset.save()
        for image in asset_images:
            AssetImage.objects.create(asset=asset,image=image)
        return assign_asset
    class Meta:
        model=AssignAsset
        fields=['user','images']