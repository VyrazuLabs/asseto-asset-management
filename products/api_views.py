from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from common.API_custom_response import api_response
from common.pagination import add_pagination
from products.serializers import ProductSerializer
from products.utils import convert_to_list, delete_product_images, product_details, product_list_for_form
from .models import Product
from drf_spectacular.utils import extend_schema,OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
import json
from common.API_custom_response import format_validation_errors,get_detailed_errors_info,log_error_to_terminal

class ProductList(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[
        OpenApiParameter(name="page",type=int,default=1,description="page number for pagination")])
    def get(self,request):
        try:
            product_queryset=Product.undeleted_objects.filter(organization=request.user.organization).order_by("-created_at")
            product_list=convert_to_list(request,product_queryset)
            page=int(request.GET.get('page',1))
            paginated_data=add_pagination(product_list,page=page)
            return api_response(data=paginated_data,message='Product list fetch successfully')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))


class AddProduct(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(request={"multipart/form-data":ProductSerializer})
    def post(self,request):
        try:
            serializer=ProductSerializer(data=request.data,context={'request':request})
            if not serializer.is_valid():
                raise ValueError(serializer.errors)
            serializer.save()
            return api_response(status=200,message='product add successfully')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)

            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])



class ProductDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:    
            print("ID-------->",id)
            get_product=get_object_or_404(Product,pk=id)
            data=product_details(request,get_product)
            return api_response(data=data,message='Product details fetch successfully')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))
        

class UpdateProduct(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(request={"multipart/form-data":ProductSerializer})
    def patch(self,request,id):
        try:
            get_product=get_object_or_404(Product,pk=id)
            deleted_image_ids=request.data.get('delete_image_ids',[])
            deleted_image_ids= json.loads(deleted_image_ids) if isinstance(deleted_image_ids,str) else deleted_image_ids
            if deleted_image_ids:
                delete_product_images(deleted_image_ids)
            serializer=ProductSerializer(get_product,data=request.data,partial=True)
            if not serializer.is_valid():
                print(serializer.errors)
                return api_response(
                    status=400,error_type="Validation_error",
                    error_location="Serializer",
                    validation_errors=format_validation_errors(serializer.errors,Product)
                )
            serializer.save()
            return api_response(status=200,message='product Updated successfully')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500,system_message=str(e))

class DeleteProduct(APIView):
    def delete(self,request,id):
        try:
            get_product=get_object_or_404(Product,pk=id)
            get_product.soft_delete()
            return api_response(status=200, message='Product sent to tarsh')
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))
        
class SearchProduct(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(description='from frontend the search field name must be "search_text"',
        parameters=[
            OpenApiParameter(name='search_text',type=OpenApiTypes.STR,location=OpenApiParameter.QUERY,required=False,
                description='Text to search across Product fields',
        ),],
    )
    def get(self,request):
        search_text=request.GET.get('search_text')
        status=request.GET.get('status')
        vendor=request.GET.get('vendor')
        product_type=request.GET.get('product_type')
        product_sub_category=request.GET.get('product_sub_category')
        user=request.GET.get('user')
        location=request.GET.get('location')
        department=request.GET.get('department')
        try:
            searched_data=Product.undeleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(manufacturer__icontains=search_text) | Q(product_sub_category__name__icontains=search_text) | Q(product_type__name__icontains=search_text)
            ))
            if status:
                searched_data=searched_data.filter(status=status)
            if vendor:
                searched_data=searched_data.filter(vendor__id=vendor)
            if product_type:
                searched_data=searched_data.filter(product_type__id=product_type)
            if product_sub_category:
                searched_data=searched_data.filter(product_sub_category__id=product_sub_category)
            if user:
                searched_data=searched_data.filter(asset__assigned_asset__user__id=user)
            if location:
                searched_data=searched_data.filter(asset__location__id=location)
            if department:
                searched_data=searched_data.filter(asset__assigned_asset__user__department__id=department)
            # searched_data=searched_data.distinct().order_by('-created_at')
            if searched_data:
                searched_product_data=convert_to_list(request,searched_data)
                return api_response(data=searched_product_data,message='Product found successfully')
            else:
                return api_response(status=404, message='product did not found')
        except ValueError as e:
            return api_response(status=400,message=str(e))
        except Exception as e:
            return api_response(status=500,message=str(e))

class ProductListForFormDropdown(APIView):
    def get(self,request):
        try:
            get_prodcuts=Product.undeleted_objects.filter(status=True)
            data=product_list_for_form(get_prodcuts)
            return api_response(data=data, message='list of products')
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))