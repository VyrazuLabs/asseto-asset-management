from django.db.utils import ConnectionHandler
from django.core.management import call_command
from django.conf import settings
from django.db import connections
from dotenv import load_dotenv, set_key
import os
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed

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

            

    