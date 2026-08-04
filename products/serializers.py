import json
from rest_framework import serializers

from products.models import Product, ProductImage
from common.convert_base64_image import convert_image


class CustomFieldSerializer(serializers.Serializer):
    field_name = serializers.CharField()
    field_value = serializers.CharField()


class DictionaryListField(serializers.ListField):
    def get_value(self, dictionary):
        if isinstance(dictionary.get(self.field_name), list) and all(
            isinstance(item, dict) for item in dictionary[self.field_name]
        ):
            return dictionary[self.field_name]
        elif isinstance(dictionary.get(self.field_name), list):
            # There can be some cases where custom fields will be a list of list of dictionaries
            # The following remedies it
            dictionary_copy = dictionary.copy()
            dictionary_copy[self.field_name] = next(
                iter(dictionary[self.field_name]), []
            )
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
            return value
        elif isinstance(value, list):
            # There can be some cases where custom fields will be a list of list of dictionaries
            # The following remedies it
            value = next(iter(value), [])
            if not all(isinstance(item, dict) for item in value):
                raise serializers.ValidationError(
                    "Each custom field must be a dictionary"
                )
            return value
        raise serializers.ValidationError(
            "Custom fields must be a list of dictionaries"
        )

    def to_internal_value(self, data):
        data = data.copy()
        if not data.get("images"):
            data.pop("images", None)
        if data.get("custom_fields") in ["", None]:
            data.pop("custom_fields", None)
        elif isinstance(data.get("custom_fields"), str):
            data["custom_fields"] = json.loads(data.get("custom_fields"))

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
        images = validated_data.pop("images")
        custom_fields = validated_data.pop("custom_fields", None)
        product = Product.objects.create(
            **validated_data, organization=self.context["request"].user.organization
        )

        product_image = None
        for image in images:
            # image=convert_image(image)
            product_image = ProductImage.objects.create(image=image, product=product)


        return product, product_image

    def update(self, instance, validated_data):
        image_data = validated_data.pop("images", [])
        custom_fields = validated_data.pop("custom_fields", [])

        for attribute, value in validated_data.items():
            if value is not None:
                setattr(instance, attribute, value)
        instance.save()

        for image in image_data:
            ProductImage.objects.create(product=instance, image=image)



        return instance

    class Meta:
        model = Product
        fields = [
            "name",
            "manufacturer",
            "model",
            "eol",
            "description",
            "product_sub_category",
            "product_type",
            "images",
            "custom_fields",
        ]
