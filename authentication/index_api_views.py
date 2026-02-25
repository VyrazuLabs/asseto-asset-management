from datetime import datetime, timedelta
from rest_framework.views import APIView
from django.db.models import Q
from assets.models import Asset, AssignAsset
from authentication.models import User
from authentication.utils import asset_datas,user_information, location_datas, user_datas, vendor_datas, generate_totp_secret,generate_qrcode,verify_totp
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

            # Check if TOTP enabled
            user_totp = UserTotp.objects.filter(user_id=user.id).first()
            if not user_totp:
                return Response({
                    'success': False,
                    'message': 'TOTP not enabled'
                }, status=400)

            # Get secret (decrypt if needed)
            secret = user_totp.secret  # decrypt here if encrypted

            # Verify OTP using your function
            is_valid = verify_totp(secret, entered_otp)
            print(f"Verifying OTP: secret={secret}, entered_otp={entered_otp}, is_valid={is_valid}")  # Debug log
            if not is_valid:
                # Optional: increment failed attempts
                # user_totp.failed_attempts = f'failed_attempts' + 1
                # user_totp.save(update_fields=['failed_attempts'])

                return Response({
                    'success': False,
                    'message': 'Invalid or expired OTP'
                }, status=400)

            # # ✅ Reset failed attempts after success
            # user_totp.failed_attempts = 0
            # user_totp.last_verified_at = timezone.now()
            # user_totp.save(update_fields=['failed_attempts', 'last_verified_at'])

            # ✅ Generate login response
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
            user = request.user
            user_totp = UserTotp.objects.filter(user_id=user.get('id')).first()
            secret = generate_totp_secret()
            if not user_totp:
                UserTotp.objects.create(user_id=user.get('id'), secret=secret)
            else:
                user_totp.secret = secret
                # user_totp.status = 0
                user_totp.save()

            qrcode = generate_qrcode(secret, user.get('username'))

            # cache_key, response = get_cache_key_with_data(
            #     request, USER_DATA_KEY, user.get('id'))

            # remove_cache_key(cache_key)

            return Response({'success': True, 'message': 'Open your authenticator app and scan this QR code to register for authenticator app login. Then use the otp to verify yourself', 'data': {'qrcode': qrcode}})

        except Exception as e:
            return Response({'success': False, 'message': str(e)})

class AssetData(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        today = datetime.now()
        time_threshold = datetime.now() + timedelta(days=30)
        try:
            expiring_assets = Asset.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization, warranty_expiry_date__lt=time_threshold)).exclude(Q(
                warranty_expiry_date__lt=today)|Q(warranty_expiry_date=None)).order_by('warranty_expiry_date')    
            all_asset_list = Asset.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization))
            asset_count = all_asset_list.count()
            assign_assets_counts = AssignAsset.objects.filter(Q(asset__organization=None,asset__is_assigned=True) | Q(
            asset__organization=request.user.organization,asset__is_assigned=True) ).count()
            data=asset_datas(expiring_assets,all_asset_list,asset_count,assign_assets_counts)
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