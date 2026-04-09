import json
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from .api_utils import  get_completed_audits,get_pending_audits,audit_data_by_id,get_audit_details,get_completed_audit
from assets.barcode import generate_barcode
from .models import Audit, AssetImage
from assets.models import AssignAsset,Asset
from assets.serializers import AssetSerializer
from common.API_custom_response import api_response
from common.pagination import add_pagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser,FormParser
from drf_spectacular.utils import extend_schema,OpenApiParameter
from django.db.models import Q
from .serializers import AuditSerializer
from .utils import get_tag_list
from datetime import datetime, timedelta

class GetAssignedUser(APIView):
    permission_classes=[IsAuthenticated]
    """ Get the assigned user data"""
    def get(self, request, tag):
        try:
            assigned_asset=AssignAsset.objects.filter(asset__tag=tag).first()
            if not assigned_asset:
                raise ValueError("No assigned user found for this asset tag")
            data={
                "assigned_user_id":assigned_asset.user.id,
                "assigned_user_name":assigned_asset.user.full_name,
                "assigned_user_email":assigned_asset.user.email,
            }
            return api_response(data=data, message="Assigned User retrieved successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))

class GetAssetTagList(APIView):
    permission_classes=[IsAuthenticated]
    """Get the list of tags"""
    def get(self, request):
        try:
            tag = request.GET.get('tag')
            data = get_tag_list(tag) if tag is not None else get_tag_list("")
            return api_response(data=data, message="List get Successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))

class CompletedAuditList(APIView):
    permission_classes=[IsAuthenticated]
    """Get the list of Completed Audits"""
    @extend_schema(parameters=[
        OpenApiParameter(name="page",type=int,default=1,description="page number for pagination")])
    def get(self,request):
        try:
            data=get_completed_audit(request)
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
    """Get the list of Pending Audits"""
    @extend_schema(parameters=[OpenApiParameter(name="page",type=int,default=1,description="page number for pagination")])
    def get(self,request):
        try:
            # audit_queryset=Audit.objects.filter(organization=request.user.organization).order_by("created_at")
            data=get_pending_audits(request)
            page=int(request.GET.get('page',"1"))
            paginated_data=add_pagination(data,page=page)
            return api_response(data=paginated_data, message="List get Successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))

class AddAudit(APIView):
    permission_classes=[IsAuthenticated]
    parser_class=[MultiPartParser,FormParser]
    """Add the Audit Data"""
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
    """Get the audit based on respective Id"""
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
    """Get the Audit Details"""
    def get(self,request,id):
        try:
            # get_audit=get_object_or_404(Audit,pk=id)
            data=get_audit_details(request,id)
            return api_response(data=data, message="Audit Details retrieved successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))
