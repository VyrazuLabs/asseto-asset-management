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
from .api_utils import search_utils

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
            response_data = search_utils(request,search_text)
            print("Searched Noiw")
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

        # context = {
        #     'products': products,
        #     'assets': assets,
        #     'users':users,
        #     'search_text': search_text,
        # }
