from rest_framework import serializers

from authentication.models import User
from dashboard.models import Address, Location

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields="__all__"


class UserAdressSerializer(serializers.ModelSerializer):
    class Meta:
        model=Address
        fields=['address_line_one','address_line_two','country','state','city','pin_code']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False)
    address=UserAdressSerializer()
    class Meta:
        model=User
        fields=['full_name','email','phone','password','department','role','access_level','location','address']
    
    def validate_email(self,email):
        domain='@'
        if domain not in email:
            raise serializers.ValidationError("Email is not valid")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists")
        return email
    
    def create(self,validate_data):
        address_data=validate_data.pop('address')

        try:
            address=Address.objects.create(**address_data)
        except Exception as e:
            raise ValueError("Data did not add for address",e)
        try:
            if "password" not in validate_data:
                validate_data["password"] = ""
            user=User.objects.create(address=address, **validate_data)
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

