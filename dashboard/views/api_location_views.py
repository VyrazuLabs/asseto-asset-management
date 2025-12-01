from rest_framework.views import APIView
from common.API_custom_response import api_response
from dashboard.models import Location

class LocationListForFormDropdown(APIView):
    def get(self,request):
        try:
            get_locations=Location.undeleted_objects.filter(status=True)
            if get_locations:
                data=[{'id':location.id,'name':str(location)} for location in get_locations]
            else:
                data=[]
            return api_response(data=data, message='list of Locations')
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))