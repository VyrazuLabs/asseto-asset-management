import json
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from .api_utils import  get_completed_audits,get_pending_audits,audit_data_by_id,get_audit_details
# from assets.barcode import generate_barcode
from .models import Audit, AssetImage
from assets.serializers import AssetSerializer
from common.API_custom_response import api_response
from common.pagination import add_pagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser,FormParser
from drf_spectacular.utils import extend_schema,OpenApiParameter
from django.db.models import Q
from .serializers import AuditSerializer

#Get the list of Completed Audits
class CompletedAuditList(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[
        OpenApiParameter(name="page",type=int,default=1,description="page number for pagination")])
    def get(self,request):
        try:
            audit_queryset=Audit.objects.filter(organization=request.user.organization).order_by("created_at")
            data=get_completed_audits(request,audit_queryset)
            # print("-------------------------:",data)
            page=int(request.GET.get('page',"1"))
            if page is None:
                page=1
            paginated_data=add_pagination(data,page=page)
            return api_response(data=paginated_data, message="List get Successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            # raise(e)
            return api_response(status=500,system_message=str(e))

class PendingAuditList(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[
        OpenApiParameter(name="page",type=int,default=1,description="page number for pagination")])
    def get(self,request):
        try:
            # audit_queryset=Audit.objects.filter(organization=request.user.organization).order_by("created_at")
            data=get_pending_audits(request)
            page=int(request.GET.get('page',"1"))
            paginated_data=add_pagination(data,page=page)
            return api_response(data=paginated_data, message="List get Successfully")
        except ValueError as e:
            api_response(status=400,error_message=str(e))
        except Exception as e:
            api_response(status=500,system_message=str(e))

class AddAudit(APIView):
    permission_classes=[IsAuthenticated]
    parser_class=[MultiPartParser,FormParser]

    @extend_schema(request={"multipart/form-data":AuditSerializer})
    def post(self,request):
        try:
            add_audit=AuditSerializer(data=request.data,context={'request':request})
            if not add_audit.is_valid():
                raise ValueError(add_audit.errors)
            add_audit.save()
            return api_response(status=200,message='Asset data saved successfully')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))
        
class GetAuditById(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:
            # get_audit=get_object_or_404(Audit,pk=id)
            data=audit_data_by_id(request,id)
            return api_response(data=data, message="Audit by id retrieved successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))
        
# class GetAuditDetails(APIView):
#     permission_classes=[IsAuthenticated]
#     def get(self,request,id):
#         try:
#             get_audit=get_object_or_404(Audit,pk=id)
#             data=audit_data_by_id(request,id)
#             return api_response(data=data, message="Audit by Id retrieved successfully")
#         except ValueError as e:
#             return api_response(status=400,error_message=str(e))
#         except Exception as e:
#             return api_response(status=500,system_message=str(e))
        
class GetAuditDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:
            # get_audit=get_object_or_404(Audit,pk=id)
            data=get_audit_details(request,id)
            return api_response(data=data, message="Audit Details retrieved successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))