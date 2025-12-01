import json
from rest_framework import serializers
from dashboard.models import CustomField
from products.models import Product, ProductImage

class CustomFieldSerializer(serializers.Serializer):
    field_name = serializers.CharField()
    field_value = serializers.CharField()

class ProductSerializer(serializers.ModelSerializer):
    images=serializers.ListField(child=serializers.ImageField(required=False, allow_null=True),
        required=False,
        allow_empty=True,
        allow_null=True,
        default=list,
        )
    custom_fields = serializers.ListField(child=serializers.DictField(), required=False)

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
    
    def to_internal_value(self, data):
        if(data.get("images")or"")=="":
            data=data.copy()
            data.pop("images")
        return super().to_internal_value(data)
    
    def create(self, validated_data):
        images=validated_data.pop("images")
        custom_fields = validated_data.pop("custom_fields",None)
        product=Product.objects.create(**validated_data,organization=self.context['request'].user.organization)

        product_image=None
        for image in images:
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
        image_data = validated_data.pop('images', None)
        for attribute, value in validated_data.items():
            if not value:
                continue
            setattr(instance, attribute, value)
        instance.save()
        if image_data is not None:
            for image in image_data:
                ProductImage.objects.create(product=instance, image=image)
        
        custom_fields = validated_data.pop("custom_fields",[])
        for custom_field in custom_fields:
            field_name=list(custom_field.keys())[0]
            field_value=custom_field[field_name]
            CustomField.objects.filter(object_id=instance.id,field_name=field_name).update(field_value=field_value)
        return instance
            
    class Meta:
        model=Product
        fields=['name','manufacturer','model','eol','description','product_sub_category','product_type','images','custom_fields']