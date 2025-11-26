from rest_framework.views import APIView
from common.API_custom_response import api_response
from dashboard.models import ProductCategory
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema,OpenApiParameter
from drf_spectacular.types import OpenApiTypes

class ProductCategoryListForFormDropdown(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        try:
            get_product_categories=ProductCategory.undeleted_objects.filter(status=True,parent__name='Root')
            if get_product_categories:
                data=[{'id':product_category.id,'name':product_category.name} for product_category in get_product_categories]
            else:
                data=[]
            return api_response(data=data, message='list of Product Category')
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))
        
class ProductSubCategoryListForFormDropdown(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[
        OpenApiParameter(name='category_id',type=OpenApiTypes.UUID,location=OpenApiParameter.QUERY,required=False)
    ])
    def get(self,request):
        id=request.GET.get('category_id')
        try:
            product_sub_categories=ProductCategory.undeleted_objects.filter(parent__id=id,status=True)
            if product_sub_categories:
                data=[{'id':product_sub_category.id,'name':product_sub_category.name} for product_sub_category in product_sub_categories]
            else:
                data=[]
            return api_response(data=data, message='list of Product sub Category')
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))