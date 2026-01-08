import json
from rest_framework import serializers
from dashboard.models import CustomField
from products.models import Product, ProductImage
from common.convert_base64_image import convert_image

class CustomFieldSerializer(serializers.Serializer):
    field_name = serializers.CharField()
    field_value = serializers.CharField()

class DictionaryListField(serializers.ListField):
    def get_value(self, dictionary):
        if isinstance(dictionary.get(self.field_name), list) and all(isinstance(item, dict) for item in dictionary[self.field_name]):
            return dictionary[self.field_name]
        elif isinstance(dictionary.get(self.field_name), list):
            # There can be some cases where custom fields will be a list of list of dictionaries
            # The following remedies it
            dictionary_copy = dictionary.copy()
            print("custom fields:", dictionary[self.field_name])
            dictionary_copy[self.field_name] = next(iter(dictionary[self.field_name]), [])
            return dictionary_copy[self.field_name]
        return super().get_value(dictionary)

class ProductSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(required=False, allow_null=True),
        required=False,
        allow_empty=True,
        allow_null=True,
        default=list,
    )
    # custom_fields = serializers.ListField(child=serializers.DictField(), required=False)
    custom_fields = DictionaryListField(child=serializers.DictField(), required=False)

    def validate_name(self, value):
        if self.partial and value in (None, ""):
            return value
        if not value:
            raise serializers.ValidationError("Name can not be blank")
        return value

    def validate_product_type(self, value):
        if self.partial and value in (None, ""):
            return value
        if not value:
            raise serializers.ValidationError("Product Type can not be blank")
        return value

    def validate_product_category(self, value):
        if self.partial and value in (None, ""):
            return value
        if not value:
            raise serializers.ValidationError("Product Category can not be blank")
        return value
    
    def validate_custom_fields(self, value):
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            print("Passed 1st condition", value)
            return value
        elif isinstance(value, list):
            # There can be some cases where custom fields will be a list of list of dictionaries
            # The following remedies it
            value = next(iter(value), [])
            if not all(isinstance(item, dict) for item in value):
                raise serializers.ValidationError("Each custom field must be a dictionary")

            print("Passed 2nd condition")
            return value
        raise serializers.ValidationError("Custom fields must be a list of dictionaries")

    def to_internal_value(self, data):
        data = data.copy()
        print("to_internal_value",data,"\n")
        if not data.get("images"):
            data.pop("images", None)
        if data.get("custom_fields") in ["", None]:
            data.pop("custom_fields", None)
        elif isinstance(data.get("custom_fields"), str):
            data["custom_fields"] = json.loads(data.get("custom_fields"))

        print("to_internal_value-after",data,"\n")
        return super().to_internal_value(data)
        # custom_fields = data.get("custom_fields")
        # if isinstance(custom_fields, str):
        #     try:
        #         custom_fields = json.loads(custom_fields)
        #     except json.JSONDecodeError:
        #         raise serializers.ValidationError({
        #             "custom_fields": "Invalid JSON"
        #         })

        # if not isinstance(custom_fields, list):
        #     raise serializers.ValidationError({
        #         "custom_fields": "Expected a list"
        #     })

        # data["custom_fields"] = custom_fields

    def create(self, validated_data):
        images=validated_data.pop("images")
        custom_fields = validated_data.pop("custom_fields",None)
        product=Product.objects.create(**validated_data,organization=self.context['request'].user.organization)

        product_image=None
        for image in images:
            # image=convert_image(image)
            product_image=ProductImage.objects.create(image=image,product=product)

        if custom_fields is not None:
            for custom_field in custom_fields:
                field_name = list(custom_field.keys())[0]
                field_value = custom_field[field_name]
                CustomField.objects.create(
                    name=field_name,
                    object_id=product.id,
                    field_type='text',
                    field_name=field_name,
                    field_value=field_value,
                    entity_type='product',
                    organization=self.context["request"].user.organization
                )
        return product,product_image
    
    def update(self, instance, validated_data):
        image_data = validated_data.pop("images", [])
        custom_fields = validated_data.pop("custom_fields", [])

        # 🔹 Update normal fields
        for attribute, value in validated_data.items():
            if value is not None:
                setattr(instance, attribute, value)
        instance.save()

        # 🔹 Save images
        for image in image_data:
            ProductImage.objects.create(product=instance, image=image)

        # 🔹 Existing custom fields from DB
        existing_qs = CustomField.objects.filter(
            object_id=instance.id,
            entity_type="product"
        )
        existing_field_names = {cf.field_name for cf in existing_qs}

        # 🔹 Incoming field names
        incoming_field_names = {
            next(iter(cf.keys()))
            for cf in custom_fields
            if isinstance(cf, dict) and cf
        }

        # 🔥 Delete removed fields
        deleted_field_names = existing_field_names - incoming_field_names
        if deleted_field_names:
            CustomField.objects.filter(
                object_id=instance.id,
                field_name__in=deleted_field_names,
                entity_type="product"
            ).delete()

        # 🔹 Create / Update incoming fields
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
                entity_type="product"
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
                    entity_type="product",
                    field_type="text",
                    name=field_name
                )

        return instance

            
    class Meta:
        model=Product
        fields=['name','manufacturer','model','eol','description','product_sub_category','product_type','images','custom_fields']