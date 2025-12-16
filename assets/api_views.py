from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from assets.api_utils import asset_data, convert_to_list, delete_images, get_asset
from assets.barcode import generate_barcode_px
from assets.models import Asset, AssetImage, AssetStatus
from assets.serializers import AssetSerializer, AssignAssetSerializer
from authentication.models import User
from common.API_custom_response import api_response, format_validation_errors, get_detailed_errors_info, log_error_to_terminal
from common.pagination import add_pagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from drf_spectacular.utils import extend_schema,OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
from dashboard.models import CustomField

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
            return api_response(status=500,system_message=str(e))

class AddAsset(APIView):
    permission_classes=[IsAuthenticated]
    parser_classes=[JSONParser,MultiPartParser,FormParser]

    @extend_schema(request={"multipart/form-data":AssetSerializer})
    def post(self,request):
        print(request.data)
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
        
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal()

            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])

class AssetDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:
            asset=get_object_or_404(Asset,pk=id)
            asset_images=AssetImage.objects.filter(asset=asset.id).all()
            custom_fields=CustomField.objects.filter(object_id=asset.id)
            asset_barcode = generate_barcode_px(asset.tag)
            asset_statuses=AssetStatus.objects.all()
            data=asset_data(request,asset,asset_images,asset_statuses,custom_fields)
            return api_response(data=data, message="Details retrived successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))
class UpdateAsset(APIView):
    parser_class=[MultiPartParser,FormParser]
    permission_classes=[IsAuthenticated]

    @extend_schema(request={"multipart/form-data":AssetSerializer})
    def patch(self,request,id):
        print(request.data)
        deleted_image_ids=request.data.get('delete_image_ids',[])
        if deleted_image_ids:
            delete_images(deleted_image_ids)
        get_asset=get_object_or_404(Asset,pk=id)        
        try:
            asset_data=AssetSerializer(get_asset,data=request.data,context={'request':request},partial=True)
            if not asset_data.is_valid():
                raise ValueError(asset_data.errors)
            asset_data.save()
            return api_response(status=200, message="Asset updated successfully")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))

class DeleteAsset(APIView):
    permission_classes=[IsAuthenticated]
    def delete(self,request,id):
        get_asset=get_object_or_404(Asset,pk=id)
        try:
            get_asset.soft_delete()
            return api_response(status=200,message="Asset deleted successfully")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))
        
class SearchAsset(APIView):
    permission_classes=[IsAuthenticated]
    parser_class=[FormParser]
    @extend_schema(description="From frontend the name of the form data name must be defined as search_text ")
    def get(self,request):
        search_text=request.data.get("search_text")
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
                data=convert_to_list( get_asset_queryset)
                return api_response(data=data,message="Asset found")
            else:
                return api_response(status=200,message="Asset not found")
            
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))

class Scan_api_barcode(APIView):
    @extend_schema(description="for the tag id, the variable name from frontend must be 'tag_id' ")
    def get(self,request):
        try:
            tag_id=self.kwargs.get('tag_id')
            respones_data = get_asset(tag_id)
            return api_response(data=respones_data,message="Tag id found")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))
        
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
            return api_response(status=200,message='Asset status updated successfully')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))
        
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
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,message=str(e))
        
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
            get_users=User.undeleted_objects.filter(status=True, organization=request.user.organization).exclude(pk=request.user.id)
            data=[{'id':user.id,'name':user.full_name} for user in get_users]
            return api_response(data=data, message="users for assign asset get successfully")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))
        





    
