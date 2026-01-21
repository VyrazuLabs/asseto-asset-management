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
        serializer = SearchSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                status=400,
                error_type="Validation_error",
                error_location="Serializer",
                validation_errors=format_validation_errors(serializer.errors)
            )

        search_text = serializer.validated_data.get("search_text", "").strip()
        if not search_text:
            return api_response(data={}, message="No Data found")

        try:
            org_filter = Q(organization=request.user.organization) | Q(organization=None)

            response_data = {
                "products": [],
                "assets": [],
                "users": []
            }

            # -------- Products --------
            products = Product.undeleted_objects.filter(
                org_filter & Q(name__icontains=search_text)
            ).annotate(
                total_assets=Count('asset'),
                available_assets=Count('asset', filter=Q(asset__is_assigned=False))
            ).order_by('-created_at')[:10]

            if products.exists():
                response_data["products"] = convert_product_to_list(request, products)

            # -------- Assets --------
            assets = Asset.undeleted_objects.filter(
                org_filter & (
                    Q(tag__icontains=search_text) |
                    Q(name__icontains=search_text)
                )
            ).order_by('-created_at')[:10]

            if assets.exists():
                response_data["assets"] = convert_asset_to_list(request, assets)

            # -------- Users (Superuser only) --------
            if request.user.is_superuser:
                users = User.undeleted_objects.filter(
                    org_filter &
                    Q(is_superuser=False) &
                    Q(full_name__icontains=search_text)
                ).exclude(pk=request.user.id).order_by('-created_at')[:10]

                if users.exists():
                    response_data["users"] = user_data(request, users)

            # -------- Final Response --------
            if not any(response_data.values()):
                return api_response(data=response_data, message="Data not found")

            return api_response(
                data=response_data,
                message="Search results found"
            )

        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)

            return api_response(
                status=500,
                error_type="server_error",
                error_location=error_info['location'],
                system_message=error_info["message"],
                trace_back=error_info['traceback']
            )

        # print(assets,)
        # context = {
        #     'products': products,
        #     'assets': assets,
        #     'users':users,
        #     'search_text': search_text,
        # }
