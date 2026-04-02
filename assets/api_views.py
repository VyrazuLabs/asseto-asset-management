import json
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from assets.api_utils import asset_data, convert_to_list, delete_images, get_asset,get_base_segment
from assets.models import Asset, AssetImage, AssetStatus
from assets.serializers import AssetSerializer,NotificationSerializer, AssignAssetSerializer, SearchAssetSerializer
from authentication.models import User
from common.API_custom_response import api_response, format_validation_errors, get_detailed_errors_info, log_error_to_terminal
from common.pagination import add_pagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from drf_spectacular.utils import extend_schema,OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
from django.http import HttpResponse
import requests
from dashboard.models import CustomField
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from notifications.models import UserNotification
from assets.api_utils import BaseSegmentFunc
from django.db.models import F
from .api_utils import get_notification_data, mark_notification_as_seen,asset_details,assign_asset_user_list

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_push_notification(request):
#     data=get_push_notification_data(request.user)
#     print("inside push notification api view=======================================================")
#     return Response(data) 

class GetNotifications(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[OpenApiParameter(name='page', type=int, default=1, description="Page number for pagination")])
    def get(self,request):
        try:
            in_app_notifications_status = True if request.user.inapp_notification else False
            # notifications = UserNotification.objects.filter(
            #     user=request.user,
            #     notification__entity_type=0
            # ).order_by('-notification__created_at')
            # data = [
            #     # {"recent_notification":get_recent_notification},
            #     {"id": n.id, "title": n.notification.notification_title,"body": n.notification.notification_text,"is_seen": n.is_seen,"link": n.notification.link,"object_type": get_base_segment(n.notification.link) if n.notification.link else None,"created_at": n.notification.created_at,"object_id": n.notification.object_id}
            #     for n in notifications
            # ]
            data=get_notification_data(request)
            page = int(request.GET.get('page', 1))
            paginated_data=add_pagination(data,page=page)
            response_data = {
                "in_app_notifications_status": in_app_notifications_status,
                "notifications": paginated_data
            }
            return api_response(data=response_data, message="List get Successfully")
            # Mark as sent
            # notifications.update(is_sent=True)
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])

class MarkNotificationAsSeen(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='notification_id',
                type=int,
                required=True,
                description="ID of the UserNotification to mark as seen"
            )
        ]
    )
    def patch(self, request):
        try:
            notification_id = request.GET.get("notification_id")

            if not notification_id:
                return api_response(
                    status=400,
                    error_message="notification_id is required"
                )

            mark_notification_as_seen(notification_id, request)

            return api_response(
                message="Notification marked as seen successfully"
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

class AssetList(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[
        OpenApiParameter(name="page",type=int,default=1,description="page number for pagination")])
    def get(self,request):
        try:
            asset_queryset=Asset.undeleted_objects.filter(organization=request.user.organization).order_by("-created_at")
            data=convert_to_list(request,asset_queryset)
            page=int(request.GET.get('page'))
            paginated_data=add_pagination(data,page=page)
            return api_response(data=paginated_data, message="List get Successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])

class AddAsset(APIView):
    permission_classes=[IsAuthenticated]
    parser_classes=[JSONParser,MultiPartParser,FormParser]

    @extend_schema(request={"multipart/form-data":AssetSerializer})
    def post(self,request):
        add_asset=None
        try:
            add_asset=AssetSerializer(data=request.data,context={'request':request})
            if not add_asset.is_valid():
                return api_response(
                    status=400,error_type="Validation_error",
                    error_location="Serializer",
                    validation_errors=format_validation_errors(add_asset.errors,Asset)
                )
            add_asset.save()
            return api_response(status=200,message='Asset data saved successfully')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)

            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])

class AssetDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:
            data=asset_details(id,request)
            return api_response(data=data, message="Details retrived successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)

            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])
class UpdateAsset(APIView):
    parser_class=[JSONParser,MultiPartParser,FormParser]
    permission_classes=[IsAuthenticated]

    @extend_schema(request={"multipart/form-data":AssetSerializer})
    def patch(self,request,id):
        deleted_image_ids=request.data.get('delete_image_ids',[])
        deleted_image_ids= json.loads(deleted_image_ids) if isinstance(deleted_image_ids,str) else deleted_image_ids
        if deleted_image_ids:
            delete_images(deleted_image_ids)
        get_asset=get_object_or_404(Asset,pk=id)        
        try:
            asset_data=AssetSerializer(get_asset,data=request.data,context={'request':request},partial=True)
            if not asset_data.is_valid():
                return api_response(
                    status=400,error_type="Validation_error",
                    error_location="Serializer",
                    validation_errors=format_validation_errors(asset_data.errors,Asset)
                )
            asset_data.save()
            return api_response(status=200, message="Asset updated successfully")
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)

            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])

class DeleteAsset(APIView):
    permission_classes=[IsAuthenticated]
    def delete(self,request,id):
        get_asset=get_object_or_404(Asset,pk=id)
        try:
            get_asset.soft_delete()
            return api_response(status=200,message="Asset deleted successfully")

        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)

            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])
        
class SearchAsset(APIView):
    permission_classes=[IsAuthenticated]
    parser_classes=[FormParser,JSONParser]

    @extend_schema(request=SearchAssetSerializer)
    def post(self,request):
        serializer=SearchAssetSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                    status=400,error_type="Validation_error",
                    error_location="Serializer",
                    validation_errors=format_validation_errors(serializer.errors)
                )
        # search_text=serializer.validated_data["search_text"]
        search_text = serializer.validated_data.get("search_text")
        if not search_text or not search_text.strip():
            return api_response(data=[], message="No Asset found")
        try:
            get_asset_queryset=Asset.objects.filter(Q(tag__icontains=search_text) |
            Q(name__icontains=search_text) |
            Q(serial_no__icontains=search_text) |
            Q(purchase_type__icontains=search_text) |
            Q(product__name__icontains=search_text) |
            Q(vendor__name__icontains=search_text) |
            Q(vendor__gstin_number__icontains=search_text) |
            Q(location__office_name__icontains=search_text) |
            Q(product__product_type__name__icontains=search_text)).order_by("-created_at")
            if get_asset_queryset:
                data=convert_to_list(request,get_asset_queryset)
                return api_response(data=data,message="Asset found")
            else:
                return api_response(status=200,message="Asset not found")
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
 
            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])

class Scan_api_barcode(APIView):
    @extend_schema(description="for the tag id, the variable name from frontend must be 'tag_id' ")
    def get(self,request,tag_id):
        try:
            # tag_id=self.kwargs.get('tag_id')
            response_data = get_asset(tag_id)
            return api_response(data=response_data,message="Tag id found")
        
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
 
            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])
        
class UpdateAssetStatus(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[OpenApiParameter(name='status_id',type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY,required=True,
        description='From frontend for the status id, name should come as "status_id"')])
    def post(self,request,id):
        status_id=request.GET.get('status_id')
        try:
            asset=get_object_or_404(Asset,pk=id)
            asset.asset_status=AssetStatus.objects.get(id=status_id)
            asset.save()
            return api_response(status=200,message='Asset Status updated successfully')
        
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)

            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])
        
class AssignAsset(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(request={'multipart/form-data':AssignAssetSerializer})
    def post(self,request,id):
        try:
            get_asset=get_object_or_404(Asset,pk=id)
            if get_asset.is_assigned==True:
                return api_response(status=400,message="this asset is already assigned")
            serializer=AssignAssetSerializer(data=request.data)
            if not serializer.is_valid():
                raise ValueError(serializer.errors)
            serializer.save(asset=get_asset)
            return api_response(status=200,message="asset assigned successfully")

        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)

            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])

class UnAssignAsset(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        get_asset=get_object_or_404(Asset,pk=id)
        get_asset.is_assigned=False
        get_asset.save()
        return api_response(status=200,message="asset unassigned successfully")

class UserListForAssignAsset(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            data=assign_asset_user_list(request)
            return api_response(data=data, message="users for assign asset get successfully")
        
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)

            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])
        
class GetWarrantyExpiredAssetFlag(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            user=request.user
            data={
                "use_warranty_expired_assets": True if user.use_expired_assets else False
            }
            return api_response(data=data, message="Flag get successfully")
        
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)

            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])




    
