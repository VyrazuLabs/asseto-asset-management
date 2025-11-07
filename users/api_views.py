from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from assets.models import AssetImage, AssignAsset
from authentication.models import User
from common.pagination import add_pagination
from users.serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from common.API_custom_response import api_response
from users.utils import user_data, user_details
from django.db.models import Q

class UserList(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        try:
            user_list=User.objects.all().exclude(pk=request.user.id).order_by("-created_at")
            data=user_data(user_list)
            paginated_data=add_pagination(data)
            return api_response(data=paginated_data,message="user list fetched successfully")
        
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        
        except Exception as e:
            return api_response(status=500,system_message=str(e))
        

class AddUser(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        try:
            serializer=UserSerializer(data=request.data)
            serializer.is_valid(raise_exception=False)
            serializer.save()
            return api_response(status=200,message="User data add sucessfully")       
        except ValueError as e:
            return api_response(status=400,error_message=str(e))
        except Exception as e:
            print(serializer.errors)
            return api_response(status=500, system_message=str(e))        

class UpdateUser(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self,request,id):
        user=get_object_or_404(User,pk=id)
        try:
            serializer=UserSerializer(user,data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return api_response(status=200,message="user updated sucessfully")
        except ValueError as e:
            return api_response(status=400,error_message=e)
        except Exception as e:
            print(serializer.errors)
            return api_response(status=500, system_message=e) 

class UserDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        try:
            get_user=get_object_or_404(User,pk=id)
            assigned_assets = AssignAsset.objects.get(user=get_user)
            asset_images=AssetImage.objects.filter(asset=assigned_assets.asset.id).all()
            print(asset_images)
            data=user_details(get_user,assigned_assets,asset_images)

            return api_response(data=data, message="Details fetched successfully")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))

        except Exception as e:
            return api_response(status=500,system_message=str(e))

class DeleteUSer(APIView):
    def delete(self,request,id):
        user=get_object_or_404(User,pk=id)
        try:
            user.soft_delete()
            return api_response(status=200,message="User has been move to trash")
        except ValueError as e:
            return api_response(status=400, system_message=str(e))
        except Exception as e:
            return api_response(status=500,error_message=str(e))
        
class SearchUser(APIView):
    def get(self,request,search_text):
        try:
            get_searched_user=User.objects.filter(Q(full_name__icontains=search_text)|Q(email__icontains=search_text)).order_by("-created_at")
            data=user_data(get_searched_user)
            return api_response(data=data,message='User find successfully')
        except ValueError as e:
            api_response(status=400,error_message=str(e))
        except Exception as e:
            api_response(status=500,system_message=str(e))