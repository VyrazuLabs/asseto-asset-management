from rest_framework.views import APIView
from common.API_custom_response import api_response
from dashboard.models import Department

class DepartmentListForFormDropdown(APIView):
    def get(self,request):
        try:
            get_departments=Department.undeleted_objects.filter(status=True)
            if get_departments:
                data=[{'id':department.id,'name':department.name} for department in get_departments]
            else:
                data=[]
            return api_response(data=data, message='list of Departments')
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))