from rest_framework import serializers

from authentication.models import User
from dashboard.models import Address, Location

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields="__all__"

class UserSerializer(serializers.ModelSerializer):
    address_line_one = serializers.CharField(required=False)
    address_line_two = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    pin_code = serializers.CharField(required=False)
    
    password = serializers.CharField(required=False)
    access_level = serializers.BooleanField(required=False)
    profile_pic=serializers.ImageField(required=False)
    class Meta:
        model=User
        fields=['full_name','email','phone','password','department','role','access_level','location','address','profile_pic','address_line_one','address_line_two','country',
            'state','city','pin_code']
    
    def validate_email(self,email):
        domain='@'
        if domain not in email:
            raise serializers.ValidationError("Email is not valid")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists")
        return email
    
    def create(self,validate_data):

        address_fields = {
            'address_line_one': validate_data.pop('address_line_one', None),
            'address_line_two': validate_data.pop('address_line_two', None),
            'country': validate_data.pop('country', None),
            'state': validate_data.pop('state', None),
            'city': validate_data.pop('city', None),
            'pin_code': validate_data.pop('pin_code', None),
        }
        try:
            if "password" not in validate_data:
                validate_data["password"] = ""
            address = Address.objects.create(**address_fields)
            user=User.objects.create(address=address_fields, **validate_data,organization=self.context["request"].user.organization)
            if user.password:
                user.set_password(user.password)
        except Exception as e:
            raise ValueError("Data did not add for user",e)
        
        user.save()
        return user
    
    def update(self, instance, validated_data):
        address_data=validated_data.pop('address',None)
        address=instance.address
        if address_data:
            try:
                for attributes,value in address_data.items():
                    setattr(address,attributes,value)
                address.save()
            except:
                raise ValueError("Address didn't update")
   
        try:
            for attributes,value in validated_data.items():
                setattr(instance,attributes,value)
            instance.save()
        except:
            raise ValueError("User data didnt update")
        
        return instance

