from rest_framework_simplejwt.settings import api_settings as simplejwt_api_settings
from rest_framework_simplejwt.serializers import TokenRefreshSerializer


class RefreshTokenSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not simplejwt_api_settings.ROTATE_REFRESH_TOKENS:
            data['refresh'] = attrs['refresh']
        return data