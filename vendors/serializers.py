from dashboard.models import Address
from vendors.models import Vendor
from rest_framework import serializers

class VendorSerializer(serializers.ModelSerializer):
    name=serializers.CharField(required=True)
    email=serializers.EmailField(required=False)
    phone=serializers.CharField(required=False)
    contact_person=serializers.CharField(required=False)
    designation=serializers.CharField(required=False)
    gstin_number=serializers.CharField(required=False)
    description=serializers.CharField(required=False)
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
        name=validated_data.pop('name',None)
        print(validated_data.pop('name',None))
        email=validated_data.pop('email',None)
        phone=validated_data.pop('phone',None)
        contact_person=validated_data.pop('contact_person',None)
        designation=validated_data.pop('designation',None)
        gstin_number=validated_data.pop('gstin_number',None)
        description=validated_data.pop('description',None)
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
        get_vendor=Vendor.objects.filter(id=instance.id).first()
        if get_vendor:
            vendor=Vendor.objects.filter(id=instance.id).update(
                name=name,
                email=email,
                phone=phone,
                contact_person=contact_person,
                designation=designation,
                gstin_number=gstin_number,
                description=description
            )
            print("vendor------>",vendor)
            # vendor.save()
        print(instance)
        return instance