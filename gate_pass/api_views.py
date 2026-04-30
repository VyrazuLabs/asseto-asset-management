# GatePass Details API Views
# {
#     id: UUID,
#     asset_detail: {
#         id: UUID,
#         name: String,
#         tag: String,
#         asset_status: {
#             name: String,
#             colour: String
#         }
#     },
#     movement_type: enum,
#     destination_vendor: {
#         id: UUID,
#         name: String,
#         address: String,
#         email: String,
#         phone: String
#     },
#     expected_return_date: Date,
#     purpose_of_movement: String,
#     raised_by: {
#         id: UUID,
#         name: String,
#         email: String,
#         phone: String
#     },
#     authorised_by: {
        # id: UUID,  #User uuid
#         name: String,
#         email: String,
#         phone: String
#     },
#     status: enum
# }

from zoneinfo import ZoneInfo
import datetime
from drf_spectacular.types import OpenApiTypes
from rest_framework.views import APIView
from rest_framework.response import Response
from assets.api_utils import convert_to_list
from gate_pass.models import GatePass
from gate_pass.serializers import SearchGatePassSerializer,GatePassCreateSerializer
from gate_pass.utils import get_vendor_count,get_gate_pass_list
from drf_spectacular.utils import extend_schema, OpenApiParameter
from common.API_custom_response import api_response
from rest_framework.views import APIView
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from common.API_custom_response import api_response, format_validation_errors
from rest_framework import status
from common.pagination import add_pagination
from rest_framework.permissions import IsAuthenticated

class GatePassList(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(parameters=[OpenApiParameter(name='page', type=int, default=1, description="Page number for pagination")])
    def get(self, request):
        get_items = GatePass.objects.all()
        data=[]
        get_pending_authorization_count=get_items.filter(authorised_by=None).count()
        get_passes_created_today_count=get_items.filter(created_at__date=datetime.datetime.now(tz=ZoneInfo("Asia/Kolkata")).date()).count()
        get_inward_pass_count=get_items.filter(movement_type=0).count()

        for item in get_items:
            # print(item.keys())
            dict={
                "id": item.id,
                "status": item.status,
                "asset_detail": {
                    # "id": item.asset.id,
                    "name": item.asset.name,
                    "tag": item.asset.tag,
                    # "asset_status": {
                    #     "name": item.asset.asset_status.name,

                    # }
                },
                "movement_type": item.movement_type,
                "destination_vendor": {
                    # "id": item.destination_vendor.id,
                    "name": item.destination_vendor.name,
                    # "address": item.destination_vendor.address.address_line_one if item.destination_vendor.address else "",
                    # "email": item.destination_vendor.email,
                },
                "expected_return_date": item.expected_return_date,
                "purpose_of_movement": item.purpose_of_movement,
                "raised_by": {
                    # "id": item.raised_by.id,
                    "profile_image": item.raised_by.profile_pic.url if item.raised_by.profile_pic else "",
                    "name": item.raised_by.full_name,
                    # "email": item.raised_by.email,
                },
                "authorised_by":{
                    # "id":item.authorised_by.id,
                    "profile_image":item.authorised_by.profile_pic.url if item.authorised_by is not None else "",
                    "name":item.authorised_by.full_name if item.authorised_by is not None else ""
                }

            }
            data.append(dict)
        # data.append(data_card_dict)
        page=int(request.GET.get('page') or 1)
        paginated_data=add_pagination(data,page=page)
        return api_response(data={
            'inward_pass_count': get_inward_pass_count,
            'pending_authorization_count': get_pending_authorization_count,
            'passes_created_today_count': get_passes_created_today_count,
            "data": paginated_data["data"],
            "pagination": paginated_data["pagination"]
        }, message="List get Successfully")


class GatePassSearch(APIView):

    @extend_schema(description='from frontend the search field name must be "search_text"',
        parameters=[
            OpenApiParameter(name='search_text',type=OpenApiTypes.STR,location=OpenApiParameter.QUERY,required=False,
                description='Text to search across Gate-Pass fields',
        ),]
    )
    def get(self, request):
        serializer=SearchGatePassSerializer(data=request.GET)
        if not serializer.is_valid():
            return api_response(
                    status=400,error_type="Validation_error",
                    error_location="Serializer",
                    validation_errors=format_validation_errors(serializer.errors)
                )
        # search_text=serializer.validated_data["search_text"]
        search = serializer.validated_data.get("search_text")
        # search = request.GET.get('search_text')
        movement_type = request.GET.get('movement-type')
        raised_by = request.GET.get('raised-by')
        destination_vendor = request.GET.get('destination-vendor')
        expected_return_date = request.GET.get('expected-return-date')
        asset = request.GET.get('asset')

        queryset = GatePass.objects.all()

        # 🔍 Search (OR conditions)
        if search:
            queryset = queryset.filter(
                Q(asset__name__icontains=search) |
                Q(asset__tag__icontains=search) |
                Q(destination_vendor__name__icontains=search) |
                Q(asset__serial_no__icontains=search) |
                Q(raised_by__full_name__icontains=search) |
                Q(authorised_by__full_name__icontains=search)
            )

        # 🎯 Filters (AND conditions)
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)

        if raised_by:
            queryset = queryset.filter(raised_by__id=raised_by)

        if destination_vendor:
            queryset = queryset.filter(destination_vendor__id=destination_vendor)

        if expected_return_date:
            queryset = queryset.filter(expected_return_date=expected_return_date)

        if asset:
            queryset = queryset.filter(asset__id=asset)

        # 📦 Response formatting
        data = []
        for item in queryset:
            data.append({
                "id": item.id,
                "asset_detail": {
                    "id": item.asset.id,
                    "name": item.asset.name,
                    "tag": item.asset.tag,
                },
                "movement_type": item.movement_type,
                "destination_vendor": {
                    "id": item.destination_vendor.id,
                    "name": item.destination_vendor.name,
                    "address": item.destination_vendor.address.address_line_one if item.destination_vendor.address else "",
                },
                "expected_return_date": item.expected_return_date,
                "purpose_of_movement": item.purpose_of_movement,
                "raised_by": {
                    "id": item.raised_by.id,
                    "name": item.raised_by.full_name,
                    "email": item.raised_by.email,
                }
            })

        return api_response(data=data, message="Search results fetched successfully")
    
class GatePassCreate(APIView):

    @extend_schema(request={"multipart/form-data":GatePassCreateSerializer})
    def post(self, request):
        serializer = GatePassCreateSerializer(data=request.data, context={"request": request})
        
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data, message="GatePass created successfully")

        return api_response(
            data=serializer.errors,
            message="Validation failed",
            status=status.HTTP_400_BAD_REQUEST
        )    
    
class GatePassApprove(APIView):
    # To Apporve/Unapprove a gate pass
    @extend_schema(description='from frontend name must be "id"',
        parameters=[
            OpenApiParameter(name='id',type=OpenApiTypes.STR,location=OpenApiParameter.QUERY,required=False,
                description='Text to filter by gatepass-id to approve/unapprove the gatepass',
        ),]
    )
    def post(self, request, gate_pass_id):
        try:
            gate_pass = GatePass.objects.get(id=gate_pass_id)
        except GatePass.DoesNotExist:
            return api_response(message="GatePass not found", status=status.HTTP_404_NOT_FOUND)

        # if gate_pass.authorised_by is not None:
        #     return api_response(message="GatePass already approved", status=status.HTTP_400_BAD_REQUEST)
        if gate_pass.status==1:
            gate_pass.authorised_by = None
            gate_pass.status = 3  # '3' means unapproved or rejected
            gate_pass.save()
            return api_response(message="GatePass Rejected Successfully")
        gate_pass.authorised_by = request.user
        gate_pass.status = 1          # '1' means approved
        gate_pass.save()

        return api_response(message="GatePass Approved Successfully")