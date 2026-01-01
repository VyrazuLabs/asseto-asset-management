from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from assets.models import AssetImage, AssignAsset
from authentication.models import User
from common.pagination import add_pagination
from users.serializers import UserSerializer,SearchUserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from common.API_custom_response import api_response,format_validation_errors
from users.utils import user_data, user_details
from django.db.models import Q
from drf_spectacular.utils import extend_schema,OpenApiParameter
from configurations.models import LocalizationConfiguration
from configurations.utils import dynamic_display_name
from configurations.constants import NAME_FORMATS,CURRENCY_CHOICES
from users.api_utils import get_profile_data,get_username,get_roles
from roles.models import Role


class UserList(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[
        OpenApiParameter(name="page",type=int,default=1,description="page number for pagination")])
    def get(self, request):
        try:
            user_list=User.undeleted_objects.all().exclude(pk=request.user.id).order_by("-created_at")
            data=user_data(request,user_list)
            page=int(request.GET.get('page',1))
            paginated_data=add_pagination(data,page=page)
            return api_response(data=paginated_data,message="user list fetched successfully")
        
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        
        except Exception as e:
            print(e)
            return api_response(status=500,system_message=str(e))
        

class AddUser(APIView):
    permission_classes=[IsAuthenticated]
    serializer_class = UserSerializer

    parser_classes=[MultiPartParser,FormParser]
    @extend_schema(request={"multipart/form-data": UserSerializer})
    def post(self,request):
        try:
            serializer=UserSerializer(data=request.data,context={'request':request})
            if not serializer.is_valid():
                raise ValueError(serializer.errors)
            
            serializer.save()
            return api_response(status=200,message="User data add sucessfully",error_location="Serializer",validation_errors=format_validation_errors(serializer.errors,User))       
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))

class UpdateUser(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(request={"multipart/form-data": UserSerializer})
    
    def patch(self,request,id):
        user=get_object_or_404(User,pk=id)
        try:
            serializer=UserSerializer(user,data=request.data, partial=True)
            if not serializer.is_valid():
                return api_response(status=400, error_message="Serializer",validation_errors=format_validation_errors(serializer.errors,User))
            serializer.save()
            return api_response(status=200,message="user updated sucessfully")
        except ValueError as e:
            return api_response(status=400,error_message=e)
        except Exception as e:
            return api_response(status=500, system_message=e) 

class UserDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:
            get_user=get_object_or_404(User,pk=id)
            assigned_assets = AssignAsset.objects.filter(user=get_user).all()
            data=user_details(request,get_user,assigned_assets)
            return api_response(data=data, message="Details fetched successfully")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))

        except Exception as e:
            return api_response(status=500,system_message=str(e))

class DeleteUSer(APIView):
    permission_classes=[IsAuthenticated]
    def delete(self,request,id):
        user=get_object_or_404(User,pk=id)
        try:
            user.soft_delete()
            return api_response(status=200,message="User has been move to trash")
        except ValueError as e:
            return api_response(status=400, system_message=str(e))
        except Exception as e:
            return api_response(status=500,error_message=str(e))
        
# class SearchUser(APIView):
#     permission_classes=[IsAuthenticated]
#     def get(self,request):
#         search_text=request.get("search_text")
#         try:
#             get_searched_user=User.objects.filter(Q(full_name__icontains=search_text)|Q(email__icontains=search_text)).order_by("-created_at")
#             if get_searched_user:
#                 data=user_data(get_searched_user)
#                 return api_response(data=data,message='User fond')
#             else:
#                 return api_response(status=200,message="User not found")
#         except ValueError as e:
#             api_response(status=400,error_message=str(e))
#         except Exception as e:
#             api_response(status=500,system_message=str(e))

class UserProfile(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        data=get_profile_data(request)
        try:
            return api_response(data=data, message="User profile fetched successfully")
        except ValueError as e:
            api_response(status=400,error_message=str(e))
        except Exception as e:
            api_response(status=500,system_message=str(e))

class GetUserName(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        data=get_username(request,id)
        try:
            return api_response(data=data, message="User name and profile picture fetched successfully")
        except ValueError as e:
            api_response(status=400,error_message=str(e))
        except Exception as e:
            api_response(status=500,system_message=str(e))

class GetRoles(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            data=get_roles(request)
            return api_response(data=data,message="Roles fetched successfully")
        except ValueError as e:
            api_response(status=400,error_message=str(e))
        except Exception as e:
            api_response(status=500,system_message=str(e))

class UserSearch(APIView):
    permission_classes=[IsAuthenticated]
    parser_classes=[FormParser,JSONParser]
    @extend_schema(request=SearchUserSerializer)
    def post(self,request):
        serializer=SearchUserSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                    status=400,error_type="Validation_error",
                    error_location="Serializer",
                    validation_errors=format_validation_errors(serializer.errors)
                )
        search_text=serializer.validated_data["search_text"]
        try:
            get_searched_user=User.undeleted_objects.filter(
                Q(full_name__icontains=search_text)|
                Q(email__icontains=search_text)|
                Q(role__related_name__icontains=search_text)|
                Q(department__name__icontains=search_text)|
                Q(is_active__icontains=search_text)
            ).order_by("-created_at")
            data=user_data(request,get_searched_user)
            return api_response(data=data,message="Searched user fetched successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))