import json
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from assets.api_utils import asset_data, convert_to_list, get_asset
from assets.barcode import generate_barcode
from assets.models import Asset, AssetImage, AssetStatus
from assets.serializers import AssetSerializer
from common.API_custom_response import api_response
from common.pagination import add_pagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser,FormParser
from drf_spectacular.utils import extend_schema,OpenApiParameter
from django.db.models import Q

class AssetList(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[
        OpenApiParameter(name="page",type=int,default=1,description="page number for pagination")])
    def get(self,request):
        try:
            asset_queryset=Asset.undeleted_objects.filter(organization=request.user.organization).order_by("created_at")
            data=convert_to_list(request,asset_queryset)
            page=int(request.GET.get('page'))
            paginated_data=add_pagination(data,page=page)
            return api_response(data=paginated_data, message="List get Successfully")
        except ValueError as e:
            api_response(status=400,error_message=str(e))
        except Exception as e:
            api_response(status=500,system_message=str(e))

class AddAsset(APIView):
    permission_classes=[IsAuthenticated]
    parser_class=[MultiPartParser,FormParser]

    @extend_schema(request={"multipart/form-data":AssetSerializer})
    def post(self,request):
        try:
            add_asset=AssetSerializer(data=request.data,context={'request':request})
            if not add_asset.is_valid():
                raise ValueError(add_asset.errors)
            add_asset.save()
            return api_response(status=200,message='Asset data saved successfully')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))

class AssetDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:
            asset=get_object_or_404(Asset,pk=id)
            asset_images=AssetImage.objects.filter(asset=asset.id).all()
            asset_barcode = generate_barcode(asset.tag)
            asset_statuses=AssetStatus.objects.all()
            data=asset_data(request,asset,asset_images,asset_barcode,asset_statuses)
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
        get_asset=get_object_or_404(Asset,pk=id)        
        try:
            asset_data=AssetSerializer(get_asset,data=request.data,partial=True)
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
    def get(self,request,**kwargs):
        try:
            tag_id=self.kwargs.get('tag_id')
            respones_data = get_asset(tag_id)
            return api_response(data=respones_data,message="Tag id found")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))
    
