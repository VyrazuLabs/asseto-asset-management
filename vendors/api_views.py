from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from vendors.serializers import VendorSerializer
from vendors.utils import convert_to_list, searched_data, vendor_details
from common.API_custom_response import api_response
from common.pagination import add_pagination
from vendors.models import Vendor
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema,OpenApiParameter
from rest_framework.parsers import MultiPartParser,FormParser
from drf_spectacular.types import OpenApiTypes
class VendorList(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[
        OpenApiParameter(name='page', type=int, default=1, description="Page number for pagination")])
    
    def get(self,request):
        try:
            vendor_queryset=Vendor.undeleted_objects.filter(organization=request.user.organization).order_by("-created_at")
            data=convert_to_list(vendor_queryset,request)
            page=int(request.GET.get('page',1))
            paginated_data=add_pagination(data,page=page)
            return api_response(data=paginated_data,message='Vendor list get successfully')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))
        

class AddVendor(APIView):
    permission_classes=[IsAuthenticated]
    parser_class=[MultiPartParser,FormParser]
    @extend_schema(request={'multipart/form-data':VendorSerializer})
    def post(self,request):
        try:
            serializer=VendorSerializer(data=request.data,context={'request':request})
            if not serializer.is_valid():
                raise Exception(serializer.errors)
            serializer.save()
            return api_response(status=200,message='Vendor added successfully')
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            print(e)
            return api_response(status=500,system_message=str(e))

class VendorDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:
            get_vendor=get_object_or_404(Vendor,pk=id)
            data=vendor_details(get_vendor,request)
            return api_response(data=data, message='User details fetch successfully')
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))

class UpdateVendor(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(request={'multipart/form-data':VendorSerializer})
    def patch(self,request,id):
        try:
            get_vendor=get_object_or_404(Vendor,pk=id)
            serializer=VendorSerializer(get_vendor,data=request.data,partial=True)
            if not serializer.is_valid():
                raise Exception(serializer.errors)
            serializer.save()
            return api_response(status=200, message="Vendor updated successfully")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))


class DeleteVendor(APIView):
    permission_classes=[IsAuthenticated]
    def delete(request,self,id):
        try:
            get_vendor=get_object_or_404(Vendor, pk=id)
            get_vendor.soft_delete()
            return api_response(status=200, message='Vendor sent to trash')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))

class SearchVendor(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(description='from frontend the search field name must be "search_text"',
        parameters=[OpenApiParameter(name='page', type=int, default=1, description="Page number for pagination"),
                    OpenApiParameter(name='search_text',type=OpenApiTypes.STR,location=OpenApiParameter.QUERY,required=False,
                        description='Text to search across vendor fields',
                    ),],
    )
    def get(self,request):
        search_text=request.GET.get('search_text')
        try:
            vendors_list = searched_data(request,search_text)
            if vendors_list:
                data=convert_to_list(vendors_list,request)
                page=int(request.GET.get('page',1))
                paginated_searched_data=add_pagination(data,page=page)
                return api_response(data=paginated_searched_data,message="Vendor found successfully")
            else:
                return api_response(status=404,message="Vendor not found")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))

