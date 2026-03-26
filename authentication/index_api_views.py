from datetime import datetime, timedelta
from rest_framework.views import APIView
from django.db.models import Q
from assets.models import Asset, AssignAsset
from authentication.models import User
from authentication.utils import asset_datas,user_information,asset_data_util,totp_and_qrcode_generation,handle_user_totp, location_datas, user_datas, vendor_datas, generate_totp_secret,generate_qrcode,verify_totp
from common.API_custom_response import api_response
from rest_framework.permissions import IsAuthenticated
from dashboard.models import Location
from products.models import Product
from authentication.utils import product_datas
from vendors.models import Vendor
# from authentication.utils import user_information
from authentication.serializers import LoginOTPSerializer
from django.utils import timezone
from rest_framework.response import Response
from authentication.models import UserTotp,PhoneOtp
from authentication.serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenViewBase
from drf_spectacular.utils import extend_schema,OpenApiParameter
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
class CustomTokenObtainPairView(TokenViewBase):
    serializer_class = CustomTokenObtainPairSerializer

class LoginOtp(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='email', type=str, description="Email"),
            OpenApiParameter(name='otp', type=str, description="OTP"),
        ]
    )
    def post(self, request):
        try:
            # Use request.data (NOT query_params for POST)
            print("Request method:", request.query_params)  # Debug log
            serializer = LoginOTPSerializer(
                data=request.query_params,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)

            email = serializer.validated_data['email']
            entered_otp = serializer.validated_data['otp']

            # Get user
            user = User.objects.filter(email=email).first()
            if not user:
                return Response({
                    'success': False,
                    'message': 'Invalid credentials'
                }, status=400)

            is_valid,secret = handle_user_totp(request,entered_otp,user)
            print(f"Verifying OTP: secret={secret}, entered_otp={entered_otp}, is_valid={is_valid}")  # Debug log
            if not is_valid:
                # Optional: increment failed attempts
                # user_totp.failed_attempts = f'failed_attempts' + 1
                # user_totp.save(update_fields=['failed_attempts'])

                return Response({
                    'success': False,
                    'message': 'Invalid or expired OTP'
                }, status=400)

            # Reset failed attempts after success
            # user_totp.failed_attempts = 0
            # user_totp.last_verified_at = timezone.now()
            # user_totp.save(update_fields=['failed_attempts', 'last_verified_at'])

            # Generate login response
            refresh_token = RefreshToken.for_user(user)
            access_token = str(refresh_token.access_token)
            # response = user_information(request, user)
            response = {
                "access": access_token,
                "refresh": str(refresh_token),
            }
            return Response(response, status=200)

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Something went wrong'
            }, status=500)
        
class GenerateTOTP(APIView):
    def post(request):
        try:
            qrcode,user_logged_in,user_totp=totp_and_qrcode_generation(request)

            return Response({'success': True, 'message': 'Open your authenticator app and scan this QR code to register for authenticator app login. Then use the otp to verify yourself', 'data': {'qrcode': qrcode,"user_logged_in":user_logged_in,"user_totp":user_totp}})

        except Exception as e:
            return Response({'success': False, 'message': str(e)})

class AssetData(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            data=asset_data_util(request)
            return api_response(data=data, message="asset data for dashboard get successfully")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500,error_message=str(e))

class UsersData(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            users_count = User.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).exclude(is_superuser=True).count()
            latest_users_list = User.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).exclude(is_superuser=True).order_by('created_at').reverse()[0:5]
            data=user_datas(latest_users_list,users_count)
            return api_response(data=data,message='user data for dashboard get successfully')
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))
        
class ProductData(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            product_count = Product.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).count()
            latest_product_list = Product.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).order_by('created_at').reverse()[0:5]
            data=product_datas(latest_product_list,product_count)
            return api_response(data=data, message="product data for dashboard get successfully")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))
        
class VendorData(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            vendor_count = Vendor.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).count()
            latest_vendor_list = Vendor.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).order_by('created_at').reverse()[0:5]
            data=vendor_datas(vendor_count,latest_vendor_list)
            return api_response(data=data, message="Vendors data for dashboard get successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=400, system_message=str(e))

class LocationData(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            location_count = Location.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).count()
            all_location_list = Location.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).order_by('created_at').reverse()[0:5]
            data=location_datas(location_count,all_location_list)
            return api_response(data=data, message="Location data for dashboard get successfully")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))