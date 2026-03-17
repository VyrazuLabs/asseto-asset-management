from django.db.utils import ConnectionHandler
from django.core.management import call_command
from django.conf import settings
from django.db import connections
from dotenv import load_dotenv, set_key
import os
from users.serializers import UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from .serializers import RefreshTokenSerializer
import pyotp
import qrcode
import io
import base64
import random, string
from django.utils import timezone
import jwt
import datetime
from .models import PhoneOtp,UserTotp,User
from rest_framework.response import Response

def generate_otl_session_id(user):
    length = random.randint(5, 10)
    characters = string.ascii_letters + string.digits
    otl_session_id = "".join(random.choice(characters) for _ in range(length))

    # save otl_session_id in database
    user.otl_session_id = otl_session_id
    user.save()
    return otl_session_id

def generate_qr(request):
    try:
        user = request.user

        user_totp = UserTotp.objects.filter(user_id=user.id).last()
        secret = generate_totp_secret()
        print("Generated status:", user_totp.status if user_totp else "No existing TOTP")
        if not user_totp:
            # secret = generate_totp_secret()
            user_totp=UserTotp.objects.create(user_id=user.id, secret=secret)
        # else:
        #     user_totp.secret = secret
        #     user_totp.save()
        if user_totp.status == 1:
            user_totp.secret = user_totp.secret
            user_totp.status = 1
            user_totp.save()
        elif user_totp.status == 2:
            user_totp.secret = user_totp.secret
            user_totp.status = 1
            user_totp.save()
        elif user_totp.status == 0:
            user_totp.secret = secret
            user_totp.status = 1
            user_totp.save()
        qr_image = generate_qrcode(user_totp.secret, user.username)

        return qr_image  

    except Exception as e:
        print("QR generation error:", e)
        return None

def generate_access_token(user, otl_session_id=None):
    if otl_session_id is None:
        otl_session_id = user.otl_session_id

    access_token_payload = {
        'token_type' : 'access',
        'user_id': user.id,
        'otl_session_id' : otl_session_id,
        'exp': datetime.datetime + datetime.timedelta(days=0, minutes=15),
        'iat': datetime.datetime
    }

    access_token = jwt.encode(access_token_payload, settings.SECRET_KEY, algorithm='HS256')
    # PhoneOtp.objects.create(user_id=user.id, otp=access_token, expires_at=timezone.now() + datetime.timedelta(minutes=15))
    return access_token

def user_information(user):
    response = {'success': True, 'message': 'User information'}
    serializer_ = UserSerializer(user)
    response['data'] = serializer_.data
    refresh_token = RefreshToken.for_user(user)
    otl_session_id = generate_otl_session_id(user)
    access_token = generate_access_token(user, otl_session_id)
    response.update({
        'api_token': access_token,
        'refresh_token': refresh_token
    })

    return response

def generate_totp_secret():
    secret = pyotp.random_base32()
    return secret

def generate_qrcode(secret,username):
    # get_user=User.objects.filter(username=username).first()
    get_totp=UserTotp.objects.filter(secret=secret).first()
    if get_totp.status == 2:
        secret=get_totp.secret
    totp = pyotp.totp.TOTP(secret)
    # Generating provisioning URI for the QR code
    provisioning_uri = totp.provisioning_uri(name=f"Asseto: {username}")
    # Generating QR code
    qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=10,border=4,)

    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffered = io.BytesIO()

    # saving QR into bytes object
    img.save(buffered, format="PNG")
    #Dont send in bytes
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    print("SECRET OF QR CODE:", secret)
    return img_str

def verify_totp(secret,entered_otp):
    print("Verifying OTP: secret=", secret)
    totp = pyotp.TOTP(secret)
    user_provided_otp = entered_otp

    if totp.verify(user_provided_otp):
        return True
    return False
def get_tokens_for_user(user):
    if not user.is_active:
      raise AuthenticationFailed("User is not active")

    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
def create_db_connection(request, db_data):
    env_path = settings.BASE_DIR / ".env"

    # Step 1: Save new DB credentials to .env
    for key, value in db_data.items():
        set_key(env_path, key, value)

    # Step 2: Reload environment variables
    load_dotenv(env_path, override=True)

    # Step 3: Build fresh DATABASE config (stand-alone dict)
    new_config = {
        "default": {
            "ENGINE": os.environ.get("DB_ENGINE"),
            "NAME": os.environ.get("DB_NAME"),
            "USER": os.environ.get("DB_USERNAME"),
            "PASSWORD": os.environ.get("DB_PASSWORD"),
            "HOST": os.environ.get("DB_HOST"),
            "PORT": os.environ.get("DB_PORT"),
            "TEST": {"NAME": "test_asseto"},
        }
    }


    # Step 4: Replace settings.DATABASES completely
    # settings.DATABASES = new_config
    conn = connections['default']
    conn.settings_dict.update({
        "ENGINE": os.environ.get("DB_ENGINE"),
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USERNAME"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
        "TEST": {"NAME": "test_asseto"},
    })

    # Step 5: Create a new connection handler using the raw dict (NOT global settings)
    new_connections = ConnectionHandler(new_config)

    # Step 6: Replace Django’s global connection registry
    connections._connections = new_connections._connections

    # Step 7: Test connection
    try:
        conn = new_connections["default"]
        conn.ensure_connection()

        # Step 8: Apply migrations
        call_command("migrate", interactive=False, verbosity=1)
        return True

    except Exception as e:
        print("Database connection failed:", e)
        return False


def asset_datas(expiring_assets,all_asset_list,asset_count,assign_assets_counts):
    asset_details_dict={}
    total_asset_cost=0
    for asset in all_asset_list:
        if asset.price is None:
            asset.price=0
        total_asset_cost=total_asset_cost+asset.price
    asset_details_dict['total_asset_cost']=total_asset_cost
    asset_details_dict['asset_count']=asset_count
    asset_details_dict['total_assign_asset_count']=assign_assets_counts
    # asset_details_dict['total_unassign_asset_count']=asset_count - assign_assets_counts
    # asset_details_dict['expiring_assets']=[]
    if expiring_assets:
        expiring_assets_list=[{'id':expiring_asset.id, 'name':expiring_asset.name, 'warranty_expiry_date':expiring_asset.warranty_expiry_date} for expiring_asset in expiring_assets]
        # asset_details_dict['expiring_assets']=expiring_assets_list
    return asset_details_dict

def user_datas(latest_users,users_count):
    user_details_dict={}
    user_details_dict['total_user_count']=users_count
    # user_details_dict['latest_users']=[]
    # if latest_users:
    #     user_details_dict['latest_users']=[{'id':latest_user.id,'name':latest_user.full_name, 'date':latest_user.created_at.strftime("%Y-%m-%d")} for latest_user in latest_users]
    return user_details_dict

def product_datas(latest_products,product_count):
    product_details_dict={}
    product_details_dict['total_product_count']=product_count
    # product_details_dict['latest_products']=[]
    # if latest_products:
        # product_details_dict['latest_products']=[{'id':latest_product.id,'name':latest_product.name, 'date':latest_product.created_at.strftime("%Y-%m-%d")} for latest_product in latest_products]
    return product_details_dict

def vendor_datas(vendor_count,vendor_list):
    vendor_details_dict={}
    vendor_details_dict['total_vendor_count']=vendor_count
    # vendor_details_dict['latest_vendors']=[]
    # if vendor_list:
    #     vendor_details_dict['latest_vendors']=[{'id':latest_vendor.id,'name':latest_vendor.name, 'date':latest_vendor.created_at.strftime("%Y-%m-%d")} for latest_vendor in vendor_list]
    return vendor_details_dict

def location_datas(location_count, all_locations):
    location_details_dict={}
    location_details_dict['total_location_count']=location_count
    # location_details_dict['latest_locations']=[]
    # if all_locations:
    #     location_details_dict['latest_locations']=[{'id':location.id,'name':str(location), 'date':location.created_at.strftime("%Y-%m-%d")} for location in all_locations]
    return location_details_dict

            

    