import json
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser,FormParser
from drf_spectacular.utils import extend_schema,OpenApiParameter
from common.API_custom_response import api_response
from common.pagination import add_pagination
from django.db.models import Q
from common.API_custom_response import api_response
from common.pagination import add_pagination
from configurations.models import TagConfiguration
from configurations.api_utils import get_tag_configurations,get_localization_configurations

class GetTagConfiguration(APIView):
    permission_classes= [IsAuthenticated]
    @extend_schema(
        parameters=[
            OpenApiParameter(name="page",type=int,default=1,description="page number for pagination")])
    def get(self,request):
        try:
            data=get_tag_configurations(request)
            # page=int(request.GET.get('page'))
            # paginated_data=add_pagination(data,page=page)
            return api_response(data=data, message="Tag Configuration")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))
        
class GetLocalizationConfiguration(APIView):
    permission_classes= [IsAuthenticated]
    @extend_schema(
        parameters=[
            OpenApiParameter(name="page",type=int,default=1,description="page number for pagination")])
    def get(self,request):
        try:
            data=get_localization_configurations(request)
            # page=int(request.GET.get('page'))
            # paginated_data=add_pagination(data,page=page)
            return api_response(data=data, message="Tag Configuration")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))