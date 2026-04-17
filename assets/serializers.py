import json
from rest_framework import serializers
from django.db import transaction
from assets.models import Asset, AssetImage, AssetStatus, AssignAsset
from dashboard.models import CustomField
from common.convert_base64_image import convert_image
from django.utils import timezone
from datetime import timedelta
from notifications.models import UserNotification
from .api_utils import get_base_segment

class NotificationSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='notification.notification_title')
    body = serializers.CharField(source='notification.notification_text')
    link = serializers.CharField(source='notification.link')
    created_at = serializers.DateTimeField(source='notification.created_at')
    object_id = serializers.CharField(source='notification.object_id')
    object_type = serializers.SerializerMethodField()

    class Meta:
        model = UserNotification
        fields = [
            'id',
            'title',
            'body',
            'is_seen',
            'link',
            'object_type',
            'created_at',
            'object_id'
        ]

    def get_object_type(self, obj):
        link = obj.notification.link
        return get_base_segment(link) if link else None

class DictionaryListField(serializers.ListField):
    def get_value(self, dictionary):
        if isinstance(dictionary.get(self.field_name), list) and all(isinstance(item, dict) for item in dictionary[self.field_name]):
            return dictionary[self.field_name]
        elif isinstance(dictionary.get(self.field_name), list):
            # There can be some cases where custom fields will be a list of list of dictionaries
            # The following remedies it
            dictionary_copy = dictionary.copy()
            dictionary_copy[self.field_name] = next(iter(dictionary[self.field_name]), [])
            return dictionary_copy[self.field_name]
        return super().get_value(dictionary)
    
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
    custom_fields = DictionaryListField(child=serializers.DictField(), required=False)
    purchase_date = serializers.DateTimeField(format='iso-8601', required=False, allow_null=True)
    warranty_expiry_date = serializers.DateTimeField(format='iso-8601', required=False, allow_null=True)

    class Meta:
        model = Asset
        fields = [
            'tag', 'name', 'product', 'vendor', 'location', 'serial_no',
            'price', 'purchase_type', 'purchase_date', 'warranty_expiry_date',
            'images', 'custom_fields','description'
        ]

    # Fix: Only decode, never remove or pop keys in to_internal_value
    def to_internal_value(self, data):
        mutable_data = {}
        # Handle QueryDict (multipart/form-data)
        if hasattr(data, "getlist"):
            for key in data.keys():
                if key == "images":
                    continue

                value = data.get(key)
                if value not in ["", None]:
                    mutable_data[key] = value

            # Handle images
            images = data.getlist("images")
            images = [img for img in images if img not in ["", None]]
            if images:
                mutable_data["images"] = images

        else:
            for key, value in data.items():
                if key == "images":
                    if isinstance(value, (list, tuple)):
                        images = [img for img in value if img not in ["", None]]
                        if images:
                            mutable_data["images"] = images
                    elif value not in ["", None]:
                        mutable_data["images"] = value
                elif value not in ["", None]:
                    mutable_data[key] = value

        # Normalize date fields
        for field in ["purchase_date", "warranty_expiry_date"]:
            if mutable_data.get(field) == "":
                mutable_data[field] = None

        # Handle custom_fields safely
        custom_fields = mutable_data.get("custom_fields")

        if custom_fields in ["", None]:
            mutable_data.pop("custom_fields", None)

        elif isinstance(custom_fields, str):
            try:
                mutable_data["custom_fields"] = json.loads(custom_fields)
            except json.JSONDecodeError:
                raise serializers.ValidationError({
                    "custom_fields": "Invalid JSON format"
                })

        return super().to_internal_value(mutable_data)
    
    # def to_internal_value(self, data):
    # # Convert QueryDict safely → plain dict
    #     if hasattr(data, "lists"):
    #         data = {k: v[0] if len(v) == 1 else v for k, v in data.lists()}
    #     else:
    #         data = dict(data)

    #     # Remove empty images field
    #     if not data.get("images"):
    #         data.pop("images", None)

    #     # Handle custom_fields safely
    #     custom_fields = data.get("custom_fields")

    #     if not custom_fields:
    #         data.pop("custom_fields", None)
    #     elif isinstance(custom_fields, str):
    #         try:
    #             data["custom_fields"] = json.loads(custom_fields)
    #         except json.JSONDecodeError:
    #             raise serializers.ValidationError({
    #                 "custom_fields": "Invalid JSON format"
    #             })

    #     return super().to_internal_value(data)

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
    
    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value
    
    def validate_purchase_date(self, value):
        if value:
            today = timezone.now()
            if value > today:
                raise serializers.ValidationError(
                    "Purchase date must be today or less than today's date."
                )
        return value

    @transaction.atomic
    def create(self, validated_data):
        images = validated_data.pop("images", []) or []
        custom_fields = validated_data.pop("custom_fields", []) or []
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


    @transaction.atomic
    def update(self, instance, validated_data):
        image_data = validated_data.pop("images", [])
        # custom_fields = validated_data.pop("custom_fields", None)

        # for attribute, value in validated_data.items():
        #     if value is not None:
        #         setattr(instance, attribute, value)
        # instance.save()

        # for image in image_data:
        #     AssetImage.objects.create(asset=instance, image=image)

        # existing_qs = CustomField.objects.filter(
        #     object_id=instance.id,
        #     entity_type="asset"
        # )
        # existing_field_names = {cf.field_name for cf in existing_qs}

        # incoming_field_names = {
        #     next(iter(cf.keys()))
        #     for cf in custom_fields
        #     if isinstance(cf, dict) and cf
        # }

        # deleted_field_names = existing_field_names - incoming_field_names
        # if deleted_field_names:
        #     CustomField.objects.filter(
        #         object_id=instance.id,
        #         field_name__in=deleted_field_names,
        #         entity_type="asset"
        #     ).delete()

        # # Create / Update incoming fields
        # for custom_field in custom_fields:
        #     if not isinstance(custom_field, dict):
        #         continue

        #     field_name = next(iter(custom_field.keys()), None)
        #     field_value = custom_field.get(field_name)

        #     if not field_name:
        #         continue

        #     qs = CustomField.objects.filter(
        #         object_id=instance.id,
        #         field_name=field_name,
        #         entity_type="asset"
        #     )

        #     if field_value is None:
        #         qs.delete()
        #     elif qs.exists():
        #         qs.update(
        #             field_value=field_value,
        #             field_type="text",
        #             name=field_name
        #         )
        #     else:
        #         CustomField.objects.create(
        #             object_id=instance.id,
        #             field_name=field_name,
        #             field_value=field_value,
        #             entity_type="asset",
        #             field_type="text",
        #             name=field_name
        #         )

        # return instance
        custom_fields = validated_data.pop("custom_fields", None)

    # Update normal fields
        for attribute, value in validated_data.items():
            if value is not None:
                setattr(instance, attribute, value)
        instance.save()

        # Handle images
        for image in image_data:
            AssetImage.objects.create(asset=instance, image=image)

        # 🚀 ONLY RUN IF USER SENT custom_fields
        if custom_fields is not None:

            existing_qs = CustomField.objects.filter(
                object_id=instance.id,
                entity_type="asset"
            )
            existing_field_names = {cf.field_name for cf in existing_qs}

            incoming_field_names = {
                next(iter(cf.keys()))
                for cf in custom_fields
                if isinstance(cf, dict) and cf
            }

            deleted_field_names = existing_field_names - incoming_field_names

            if deleted_field_names:
                CustomField.objects.filter(
                    object_id=instance.id,
                    field_name__in=deleted_field_names,
                    entity_type="asset"
                ).delete()

            for custom_field in custom_fields:
                if not isinstance(custom_field, dict):
                    continue

                field_name = next(iter(custom_field.keys()), None)
                field_value = custom_field.get(field_name)

                if not field_name:
                    continue

                qs = CustomField.objects.filter(
                    object_id=instance.id,
                    field_name=field_name,
                    entity_type="asset"
                )

                if field_value is None:
                    qs.delete()
                elif qs.exists():
                    qs.update(
                        field_value=field_value,
                        field_type="text",
                        name=field_name
                    )
                else:
                    CustomField.objects.create(
                        object_id=instance.id,
                        field_name=field_name,
                        field_value=field_value,
                        entity_type="asset",
                        field_type="text",
                        name=field_name
                    )

        return instance
    
    # def validate(self, attrs):
    #     for field in ["purchase_date", "warranty_expiry_date"]:
    #         if attrs.get(field) in ["", None]:
    #             attrs[field] = None
    #     purchase_date = attrs.get("purchase_date")
    #     warranty_expiry_date = attrs.get("warranty_expiry_date")

    #     # Cross-field validation
    #     if purchase_date and warranty_expiry_date:
    #         if warranty_expiry_date <= purchase_date:
    #             raise serializers.ValidationError({
    #                 "warranty_expiry_date": (
    #                     "Warranty expiry date must be greater than purchase date."
    #                 )
    #             })
    #     return attrs
    
    def validate_warranty_expiry_date(self, value):
        user=self.context["request"].user
        if user.use_expired_assets is True and value:
            return value
        else:
            tomorrow = timezone.now() + timedelta(days=1)
            if value < tomorrow:
                raise serializers.ValidationError(
                    "Warranty expiry date must be at least tomorrow."
                )
            return value


class SearchAssetSerializer(serializers.Serializer):
    search_text = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    class Meta:
        fields=['search_text']
    
    def validate(self, search_text):
        if not search_text:
            return []
        return search_text
class AssignAssetSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(required=False, allow_null=True),
        required=False,
        allow_empty=True,
        allow_null=True,
        default=list,
    )

    # def to_internal_value(self, data):
    #     data = data.copy()
    #     if (data.get("images") or "") == "":
    #         data.pop("images", None)
    #     return super().to_internal_value(data)
    # def to_internal_value(self, data):
    #     # Convert QueryDict → regular dict (no deepcopy of file objects)
    #     data = dict(data)
    #     if (data.get("images") or "") == "":
    #         data.pop("images", None)
    #     return super().to_internal_value(data)
    def to_internal_value(self, data):
        mutable_data = {}

        # Handle QueryDict safely
        if hasattr(data, "getlist"):
            for key in data.keys():
                values = data.getlist(key)

                if key == "images":
                    mutable_data[key] = [v for v in values if v not in ["", None]]
                else:
                    # Take first value if single field
                    mutable_data[key] = values[0] if values else None
        else:
            mutable_data = data.copy()

        # Remove empty images
        if mutable_data.get("images") in ["", None, []]:
            mutable_data.pop("images", None)

        return super().to_internal_value(mutable_data)

    def validate_user(self,user):
        if not user:
            raise serializers.ValidationError("User must needed")
        return user
        
    def create(self, validated_data):
        asset=validated_data.pop('asset',None)
        asset_images=validated_data.pop('images',[])
        assign_asset=AssignAsset.objects.create(asset=asset,**validated_data)
        asset.is_assigned=True
        status="Assigned"
        get_status=AssetStatus.objects.filter(name=status).first()
        asset.asset_status = get_status
        asset.save()
        for image in asset_images:
            AssetImage.objects.create(asset=asset,image=image)
        return assign_asset
    class Meta:
        model=AssignAsset
        fields=['user','images']