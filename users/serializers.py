from rest_framework import serializers

from authentication.models import User
from dashboard.models import Address, Location
# from dashboard.serializers import AddressSerializer
from roles.models import Role
from rest_framework.exceptions import ValidationError
from rest_framework import serializers

class ResetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    rewrite_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["current_password"] != attrs["rewrite_password"]:
            raise serializers.ValidationError(
                {"rewrite_password": "Passwords do not match."}
            )
        return attrs

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields="__all__"

class UserSerializer(serializers.ModelSerializer):
    role=serializers.CharField(required=False)
    address_line_one = serializers.CharField(required=False)
    address_line_two = serializers.CharField(required=False)
    email=serializers.EmailField(required=False)
    country = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    pin_code = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    access_level = serializers.BooleanField(required=False)
    profile_pic=serializers.ImageField(required=False)
    class Meta:
        model=User
        fields=['full_name','email','phone','password','department','role','access_level','location','profile_pic','address_line_one','address_line_two','country',
            'state','city','pin_code']
        
    # def format_role_type(self,role):
    #     if role:
    #         return role.id
    #     return None
    
    def validate_email(self,email):
        domain='@'
        if domain not in email:
            raise serializers.ValidationError("Email is not valid")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists")
        return email
    
    def create(self, validated_data):
        role_id = validated_data.pop('role', None)

        address_fields = {
            'address_line_one': validated_data.pop('address_line_one', None),
            'address_line_two': validated_data.pop('address_line_two', None),
            'country': validated_data.pop('country', None),
            'state': validated_data.pop('state', None),
            'city': validated_data.pop('city', None),
            'pin_code': validated_data.pop('pin_code', None),
        }

        try:
            # password handling
            password = validated_data.get("password", "")

            # role handling
            role = None
            if role_id:
                role = Role.objects.filter(
                    id=int(role_id),
                    organization=self.context["request"].user.organization
                ).first()

                if not role:
                    raise ValueError("Invalid role selected")

            address = Address.objects.create(**address_fields)

            user = User.objects.create(
                **validated_data,
                role=role,
                address=address,
                organization=self.context["request"].user.organization
            )

            if password:
                user.set_password(password)
                user.save()

            return user

        except Exception as e:
            raise ValueError(str(e))

    
    def update(self, instance, validated_data):
        request = self.context["request"]

        # Extract fields
        role_value = validated_data.pop("role", None)

        address_fields = {
            "address_line_one": validated_data.pop("address_line_one", None),
            "address_line_two": validated_data.pop("address_line_two", None),
            "country": validated_data.pop("country", None),
            "state": validated_data.pop("state", None),
            "city": validated_data.pop("city", None),
            "pin_code": validated_data.pop("pin_code", None),
        }

        # ROLE HANDLING (string → int)
        if role_value not in [None, ""]:
            if not str(role_value).isdigit():
                raise ValidationError({"role": "Role must be a numeric value"})

            role = Role.objects.filter(
                id=int(role_value),
                organization=request.user.organization
            ).first()

            if not role:
                raise ValidationError({"role": "Invalid role selected"})

            instance.role = role

        # ADDRESS UPDATE
        if any(address_fields.values()):
            address = instance.address
            if not address:
                raise ValidationError({"address": "User has no address"})

            for attr, value in address_fields.items():
                if value is not None:
                    setattr(address, attr, value)
            address.save()

        # USER FIELDS UPDATE
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


    # Search based on user name ,email,role,department,status
    # def search(self,search_text):
    #     full_name=
    #     if search_text:
    #     else:
    #         return None
    #     return search_text


class SearchUserSerializer(serializers.ModelSerializer):
    search_text=serializers.CharField(required=False)
    role=serializers.CharField(required=False)
    status=serializers.CharField(required=False)
    class Meta:
        model=User
        fields=['search_text','role','status']
    
    def validate(self, search_text):
        if not search_text:
            return None
        return search_text