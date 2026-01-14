from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.db.models import Count
from products.models import Product
from assets.models import Asset
from .serializers import SearchSerializer
from authentication.models import User
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from drf_spectacular.utils import extend_schema
from common.API_custom_response import api_response,format_validation_errors
from assets.api_utils import asset_data, convert_to_list, delete_images, get_asset
from common.API_custom_response import api_response, format_validation_errors, get_detailed_errors_info, log_error_to_terminal
from users.utils import user_data
from .api_utils import convert_product_to_list,convert_asset_to_list
class GlobalSearch(APIView):
    permission_classes=[IsAuthenticated]
    parser_classes=[FormParser,JSONParser]
    @extend_schema(request=SearchSerializer)
    def post(self, request):
        # search_text = request.GET.get('search_text', '').strip()
        serializer=SearchSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                    status=400,error_type="Validation_error",
                    error_location="Serializer",
                    validation_errors=format_validation_errors(serializer.errors)
                )
        # search_text=serializer.validated_data["search_text"]
        search_text = serializer.validated_data.get("search_text").strip()
        if not search_text or not search_text.strip():
            return api_response(data=[], message="No Data found")
        # users=None
        # products
        try:
            org_filter = Q(organization=request.user.organization) | Q(organization=None)
            get_product_obj = Product.undeleted_objects.filter(
                org_filter & (
                    Q(name__icontains=search_text)
                )
                ).annotate(
                    total_assets=Count('asset'),
                    available_assets=Count('asset', filter=Q(asset__is_assigned=False))
                ).order_by('-created_at')[:10]
            if get_product_obj.exists():
                # data=convert_product_to_list(request,get_product_obj)
                # print("data",data)
                return api_response(data=convert_product_to_list(request,get_product_obj),message="Product found")

            get_asset_obj = Asset.undeleted_objects.filter(
                org_filter & (
                    Q(tag__icontains=search_text) |
                    Q(name__icontains=search_text)
                )
            ).order_by('-created_at')[:10]
            if get_asset_obj.exists():
                # data=convert_asset_to_list(request,get_asset_obj)
                # print("data",data)
                return api_response(data=convert_asset_to_list(request,get_asset_obj),message="Asset found")
            # get_user_obj=None
            if request.user.is_superuser:
                get_user_obj = User.undeleted_objects.filter(org_filter & 
                            Q(is_superuser=False) & (Q(full_name__icontains=search_text))).exclude(pk=request.user.id).order_by('-created_at')[:10]
                if get_user_obj.exists():
                    # data=user_data(request,get_user_obj)
                    # print("data",data)
                    return api_response(data=user_data(request,get_user_obj),message="User found")
            # if get_product_obj.exists:
            #     data=convert_product_to_list(request,get_product_obj)
            #     print("data",data)
            #     return api_response(data=data,message="Product found")
            # if get_asset_obj.exists:
            #     data=convert_asset_to_list(request,get_asset_obj)
            #     print("data",data)
            #     return api_response(data=data,message="Asset found")
            # if not get_product_obj.exists and not get_asset_obj.exists and get_user_obj.exists:
            #     data=user_data(request,get_user_obj)
            #     print("data",data)
            #     return api_response(data=data,message="User found")
            return api_response(data=[], message="Data not found")
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
 
            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])
        # print(assets,)
        # context = {
        #     'products': products,
        #     'assets': assets,
        #     'users':users,
        #     'search_text': search_text,
        # }
