from rest_framework.views import APIView
from common.API_custom_response import api_response
from dashboard.models import ProductType

class ProductTypeListForFormDropdown(APIView):
    def get(self,request):
        try:
            get_product_types=ProductType.undeleted_objects.filter(status=True)
            if get_product_types:
                data=[{'id':product_type.id,'name':product_type.name} for product_type in get_product_types]
            else:
                data=[]
            return api_response(data=data, message='list of Product Types')
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))