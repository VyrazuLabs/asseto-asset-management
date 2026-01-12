from datetime import datetime, timedelta
from rest_framework.views import APIView
from django.db.models import Q
from assets.models import Asset, AssignAsset
from authentication.models import User
from authentication.utils import asset_datas, location_datas, user_datas, vendor_datas
from common.API_custom_response import api_response
from rest_framework.permissions import IsAuthenticated
from dashboard.models import Location
from products.models import Product
from authentication.utils import product_datas
from vendors.models import Vendor

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
            print(assign_assets_counts,"----assign_assets_counts---")
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