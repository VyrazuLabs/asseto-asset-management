from dashboard.models import Address
from vendors.models import Vendor
from rest_framework import serializers

class VendorSerializer(serializers.ModelSerializer):

    address_line_one = serializers.CharField(required=False)
    address_line_two = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    pin_code = serializers.CharField(required=False)

    class Meta:
        model = Vendor
        fields = [
            'name','email','phone','contact_person','designation',
            'gstin_number','description',
            'address_line_one','address_line_two','country',
            'state','city','pin_code'
        ]

    def create(self, validated_data):
        address_fields = {
            'address_line_one': validated_data.pop('address_line_one', None),
            'address_line_two': validated_data.pop('address_line_two', None),
            'country': validated_data.pop('country', None),
            'state': validated_data.pop('state', None),
            'city': validated_data.pop('city', None),
            'pin_code': validated_data.pop('pin_code', None),
        }
        address = Address.objects.create(**address_fields)

        vendor = Vendor.objects.create(
            **validated_data,
            address=address,
            organization=self.context['request'].user.organization
        )
        return vendor
    
    def update(self, instance, validated_data):

        address_data = {
            'address_line_one': validated_data.pop('address_line_one', None),
            'address_line_two': validated_data.pop('address_line_two', None),
            'country': validated_data.pop('country', None),
            'state': validated_data.pop('state', None),
            'city': validated_data.pop('city', None),
            'pin_code': validated_data.pop('pin_code', None),
        }
        for attributes,value in validated_data.items():
            if value is None:
                continue
            setattr(instance,attributes,value)
        address_instance=instance.address if instance.address else None
        print(address_instance,address_data)
        for key, value in address_data.items():
            setattr(address_instance,key,value)
        address_instance.save()

        return instance