from rest_framework import serializers
from assets.models import Asset, AssetImage, AssetStatus

class AssetSerializer(serializers.ModelSerializer):
    name=serializers.CharField(required=False)
    images = serializers.ListField(
        child=serializers.ImageField(required=False, allow_null=True),
        required=False,
        allow_empty=True,
        allow_null=True,
        default=list,
    )

    class Meta:
        model=Asset
        fields=['tag','name','product','vendor','location','serial_no','price','purchase_type','purchase_date','warranty_expiry_date', 'images']

    def to_internal_value(self, data):
        if (data.get("images") or "") == "":
            data = data.copy()
            data.pop("images")
        return super().to_internal_value(data)

    def validate_tag(self, tag):
        if not tag:
            raise ValueError("Tag can not be empty")
        return tag

    def validate_name(self, name):
        if not name:
            raise ValueError("Name can not be blank")
        return name
    def validate_product(self,product):
        if not product:
            raise ValueError("Product can not be blank")
        return product

    def create(self, validated_data):
        try:
            images=validated_data.pop("images")
            get_asset_status=AssetStatus.objects.get(name="Available")
            asset=Asset.objects.create(**validated_data,organization=self.context["request"].user.organization,asset_status=get_asset_status)
            asset_images=None
            for image in images:
                asset_images=AssetImage.objects.create(image=image,asset=asset)
        except Exception as e:
            print(e)
            raise ValueError('data did not entered',str(e))
        
        return asset,asset_images
    
    def update(self, instance, validated_data):
        image_data=validated_data.pop('images',None)
        
        for attribute, value in validated_data.items():
            setattr(instance,attribute,value)
        instance.save()
        if image_data is not None:
            for image in image_data:
                AssetImage.objects.create(asset=instance,image=image)
        
        return instance