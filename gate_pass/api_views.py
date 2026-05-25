import datetime
from zoneinfo import ZoneInfo

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.API_custom_response import api_response, format_validation_errors
from common.pagination import add_pagination
from gate_pass.models import GatePass
from gate_pass.serializers import SearchGatePassSerializer, GatePassCreateSerializer
from gate_pass.utils import get_vendor_count, get_gate_pass_list, search_gate_passes


class GatePassList(APIView):
    """List gate passes for the authenticated user's organization with stat card counts."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[
        OpenApiParameter(name='page', type=int, default=1, description="Page number")
    ])
    def get(self, request):
        organization = request.user.organization
        get_items = GatePass.objects.filter(organization=organization).select_related(
            'asset', 'destination_vendor', 'raised_by', 'authorised_by'
        )

        get_pending_authorization_count = get_items.filter(status=0).count()
        get_passes_created_today_count = get_items.filter(
            created_at__date=datetime.datetime.now(tz=ZoneInfo("Asia/Kolkata")).date()
        ).count()
        get_inward_pass_count = get_items.filter(movement_type=1).count()

        data = []
        for item in get_items:
            data.append({
                "id": item.id,
                "status": item.status,
                "asset_detail": {
                    "name": item.asset.name,
                    "tag": item.asset.tag,
                },
                "movement_type": item.movement_type,
                "destination_vendor": {
                    "name": item.destination_vendor.name,
                },
                "expected_return_date": item.expected_return_date,
                "purpose_of_movement": item.purpose_of_movement,
                "raised_by": {
                    "profile_image": item.raised_by.profile_pic.url if item.raised_by and item.raised_by.profile_pic else "",
                    "name": item.raised_by.full_name if item.raised_by else "",
                },
                "authorised_by": {
                    "profile_image": item.authorised_by.profile_pic.url if item.authorised_by and item.authorised_by.profile_pic else "",
                    "name": item.authorised_by.full_name if item.authorised_by else "",
                },
            })

        page = int(request.GET.get('page') or 1)
        paginated_data = add_pagination(data, page=page)
        return api_response(data={
            'inward_pass_count': get_inward_pass_count,
            'pending_authorization_count': get_pending_authorization_count,
            'passes_created_today_count': get_passes_created_today_count,
            "data": paginated_data["data"],
            "pagination": paginated_data["pagination"],
        }, message="List fetched successfully")


class GatePassSearch(APIView):
    """Search and filter gate passes for the authenticated user's organization."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        description='Search gate passes. Use "search_text" query param for full-text search.',
        parameters=[
            OpenApiParameter(
                name='search_text', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Text to search across Gate-Pass fields',
            ),
        ]
    )
    def get(self, request):
        serializer = SearchGatePassSerializer(data=request.GET)
        if not serializer.is_valid():
            return api_response(
                status=400, error_type="Validation_error",
                error_location="Serializer",
                validation_errors=format_validation_errors(serializer.errors),
            )

        queryset = search_gate_passes(request)

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
                    "id": item.raised_by.id if item.raised_by else None,
                    "name": item.raised_by.full_name if item.raised_by else "",
                    "email": item.raised_by.email if item.raised_by else "",
                },
            })

        return api_response(data=data, message="Search results fetched successfully")


class GatePassCreate(APIView):
    """Create a new gate pass for the authenticated user's organization."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request={"multipart/form-data": GatePassCreateSerializer})
    def post(self, request):
        serializer = GatePassCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data, message="GatePass created successfully")

        return api_response(
            data=serializer.errors,
            message="Validation failed",
            status=status.HTTP_400_BAD_REQUEST,
        )


class GatePassApprove(APIView):
    """Approve or reject a gate pass. Toggling: approved → rejected, otherwise → approved."""

    permission_classes = [IsAuthenticated]

    def post(self, request, gate_pass_id):
        """Toggle approval status of the gate pass identified by gate_pass_id."""
        organization = request.user.organization
        try:
            gate_pass = GatePass.objects.get(id=gate_pass_id, organization=organization)
        except GatePass.DoesNotExist:
            return api_response(message="GatePass not found", status=status.HTTP_404_NOT_FOUND)

        if gate_pass.status == 1:
            gate_pass.authorised_by = None
            gate_pass.status = 3
        else:
            gate_pass.authorised_by = request.user
            gate_pass.status = 1

        gate_pass.save()
        action = "Rejected" if gate_pass.status == 3 else "Approved"
        return api_response(message=f"GatePass {action} Successfully")
