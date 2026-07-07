from rest_framework_simplejwt.settings import api_settings as simplejwt_api_settings
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from authentication.models import User, UserTotp
from django.shortcuts import get_object_or_404


class RefreshTokenSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not simplejwt_api_settings.ROTATE_REFRESH_TOKENS:
            data["refresh"] = attrs["refresh"]
        return data


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        # First validate username & password
        data = super().validate(attrs)
        user = get_object_or_404(User, id=self.user.id)
        user_totp = UserTotp.objects.filter(user_id=self.user.id).first()

        if user.two_factor_auth and user_totp.is_validate:

            return {"two_factor_auth": True}

        data["two_factor_auth"] = False
        return data


class LoginOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or OTP")

        attrs["user"] = user
        return attrs
