from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.API_custom_response import api_response, format_validation_errors
from gate_pass.models import GatePass
from gate_pass.serializers import (GatePassCreateSerializer,
                                   SearchGatePassSerializer)
from gate_pass.utils import (GatePassFilterService, GatePassRepositoryImpl,
                             GatePassSerializer, GatePassService)
from django.shortcuts import get_object_or_404

class GatePassList(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = GatePassService(GatePassRepositoryImpl())

    @extend_schema(parameters=[OpenApiParameter(name='page', type=int, default=1, description="Page number for pagination")])
    def get(self, request):
        try:
            page = int(request.GET.get("page") or 1)
            data = self.service.get_list_with_stats(page,request)
            return api_response(success=True, status=200, data=data)

        except ValueError as e:
            return api_response(success=False, status=400, message=str(e))

        except Exception as e:
            return api_response(status=500, success=False, error_message=str(e), message="Something went wrong!")

class GatePassSearch(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository= GatePassRepositoryImpl()
        self.filter_service=GatePassFilterService()

    @extend_schema(description='from frontend the search field name must be "search_text"',
        parameters=[
            OpenApiParameter(name='search_text',type=OpenApiTypes.STR,location=OpenApiParameter.QUERY,required=False,
                description='Text to search across Gate-Pass fields',
        ),]
    )
    def get(self, request):
        try:
            serializer=SearchGatePassSerializer(data=request.GET)
            if not serializer.is_valid():
                return api_response(
                        status=400,error_type="Validation_error",
                        error_location="Serializer",
                        validation_errors=format_validation_errors(serializer.errors)
                    )
            queryset= self.filter_service.apply_filters(self.repository.get_all(), request.GET)
            
            data=[GatePassSerializer.serialize_list_item(item,request) for item in queryset]

            return api_response(status=200, success=True,data=data)
        except ValueError as e:
            return api_response(status=400, success=False, message=str(e))
        except Exception as e:
            return api_response(status=500, success=False, error_message=str(e), message="Something went wrong!")
    
class GatePassCreate(APIView):

    @extend_schema(request={"multipart/form-data":GatePassCreateSerializer})
    def post(self, request):
        serializer = GatePassCreateSerializer(data=request.data, context={"request": request})
        
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data, message="GatePass created successfully")

        return api_response(
            data=serializer.errors,
            message="Validation failed",
            status=status.HTTP_400_BAD_REQUEST
        )    
    
class GatePassApprove(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service= GatePassService(GatePassRepositoryImpl())

    @extend_schema(description='from frontend name must be "id"',
        parameters=[
            OpenApiParameter(name='id',type=OpenApiTypes.STR,location=OpenApiParameter.QUERY,required=False,
                description='Text to filter by gatepass-id to approve/unapprove the gatepass',
        ),]
    )
    def post(self, request, gate_pass_id):
        try:
            gate_pass = get_object_or_404(GatePass, id=gate_pass_id)        
            action=self.service.approved_or_reject(request, gate_pass)
            return api_response(success=True, status=200, message=action)
        
        except ValueError as e:
            return api_response(status=400, success=False, message=str(e))
        
        except Exception as e:
            return api_response(status=500, success=False, error_message=str(e), message="Something went wrong!")
