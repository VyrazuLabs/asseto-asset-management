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
from rest_framework.response import Response
from users.api_utils import forgot_password
from common.API_custom_response import format_validation_errors,get_detailed_errors_info,log_error_to_terminal
from datetime import datetime
from django.utils import timezone
from django.shortcuts import render
# @api_view(["POST"])
class ResetPassword(APIView):
    permission_classes = []

    def post(self, request):
        # token = request.data.get("token")
        token=request.query_params.get("token")
        print("token",token)
        new_password = request.data.get("password")
        print("New Password:", new_password)
        if not new_password:
            return Response(
                {"success": False, "message": "Password is required."},
                status=400
            )

        user = User.objects.filter(
            password_reset_token=token,
            # password_reset_expires__gte=timezone.now()
        ).first()

        if not user:
            return Response(
                {"success": False, "message": "Invalid or expired token."},
                status=400
            )

        user.set_password(new_password)
        user.password_reset_token = None
        # user.password_reset_expires = None
        user.save()
        # return render(request, "users/password-reset-entry.html")
        return Response(
            {"success": True, "message": "Password reset successfully."},
            status=200
        )
    
    def get(self, request):
        token=request.query_params.get("token")
        return render(request, "users/password-reset-entry.html", {"token": token})

class ForgotPassword(APIView):
    # permission_classes=[AllowAny]
    @extend_schema(parameters=[
        OpenApiParameter(name="email",type=str,description="Enter Email")])
    def post(self,request):
        email=request.query_params.get("email",None)
        print(request.query_params.get("email"))

        try:
            if email is None:
                return Response({"success": False, "message": "Email cannot be blank."})
            else:
                response = forgot_password(request=request,email=email)
                return Response(response)
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500, system_message=str(e))

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
            serializer=UserSerializer(user,data=request.data, partial=True,context={'request':request})
            if not serializer.is_valid():
                return api_response(status=400, error_message="Serializer",validation_errors=format_validation_errors(serializer.errors,User))
            serializer.save()
            return api_response(status=200,message="user updated sucessfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            error_info=get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500,error_type="server_error",error_location=error_info['location'],
                system_message=error_info["message"], trace_back=error_info['traceback'])

class UserDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:
            type(id)
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
        search_text=serializer.validated_data["search_text"] if serializer.validated_data.get("search_text") else ""
        role=serializer.validated_data.get("role",None)
        status=serializer.validated_data.get("status",None)
        try:
            get_searched_user=User.undeleted_objects.filter(
                Q(full_name__icontains=search_text)|
                Q(email__icontains=search_text)|
                Q(role__related_name__icontains=search_text)|
                Q(department__name__icontains=search_text)|
                Q(is_active__icontains=search_text)
            ).order_by("-created_at")

            if role:
                get_searched_user = get_searched_user.filter(role__related_name__icontains=role)
            if status:
                is_active = True if status.lower() == 'active' else False
                get_searched_user = get_searched_user.filter(is_active=is_active)

            print("Rendered query: ", str(get_searched_user.query))
            data=user_data(request,get_searched_user)
            return api_response(data=data,message="Searched user fetched successfully")
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            return api_response(status=500,system_message=str(e))