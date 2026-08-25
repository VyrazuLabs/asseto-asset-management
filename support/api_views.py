from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from common.API_custom_response import api_response, get_detailed_errors_info, log_error_to_terminal
from common.pagination import add_pagination

from .models import SupportTicket, TicketAttachment
from .serializers import (
    SupportTicketSerializer,
    SupportTicketWriteSerializer,
    TicketCommentSerializer,
    TicketCommentCreateSerializer,
    TicketStatusUpdateSerializer,
)
from .utils import SupportTicketService

TAGS = ["support-tickets"]


class TicketListAPIView(APIView):
    """List support tickets for the current org, paginated and filterable
    by ``status``, ``priority``, ``ticket_type``, and free-text ``search``
    (see ``SupportTicketService.apply_filters``)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=TAGS,
        operation_id="support_tickets_list",
        summary="List support tickets",
        description=(
            "Paginated, org-scoped list of support tickets. Supports filtering "
            "by status, priority, ticket_type, and a free-text search across "
            "ticket id, subject, asset name, and assignee name."
        ),
        parameters=[
            OpenApiParameter(name="page", type=int, default=1, description="Page number"),
            OpenApiParameter(
                name="status", type=str, required=False,
                description="Filter by status: 0=Open, 1=In Progress, 2=In Testing, 3=Resolved, 4=Closed",
            ),
            OpenApiParameter(
                name="priority", type=str, required=False,
                description="Filter by priority: 0=Low, 1=Medium, 2=High, 3=Emergency",
            ),
            OpenApiParameter(
                name="ticket_type", type=str, required=False,
                description="hardware_repair | software_issue | network | preventive_maintenance | inspection | critical_failure | other",
            ),
            OpenApiParameter(name="search", type=str, required=False, description="Free-text search"),
        ],
        responses={200: OpenApiResponse(response=SupportTicketSerializer(many=True), description="Paginated list of tickets")},
    )
    def get(self, request):
        try:
            qs = SupportTicketService.base_queryset(request.user)
            qs = SupportTicketService.apply_filters(qs, request.GET)
            data = SupportTicketSerializer(qs, many=True).data
            page = int(request.GET.get("page", 1))
            paginated_data = add_pagination(list(data), page=page)
            return api_response(data=paginated_data, message="List get Successfully")
        except ValueError as e:
            return api_response(status=400, error_message=str(e))
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))


class TicketDetailAPIView(APIView):
    """Ticket detail, including attachments, comments and custom fields."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=TAGS,
        operation_id="support_tickets_detail",
        summary="Get support ticket detail",
        description="Full ticket detail: attachments, comments, and cf_definitions/cf_values for the support_ticket custom-fields module.",
        parameters=[OpenApiParameter(name="id", type=str, location=OpenApiParameter.PATH, description="Ticket UUID")],
        responses={200: OpenApiResponse(response=SupportTicketSerializer, description="Ticket detail")},
    )
    def get(self, request, id):
        try:
            ticket = get_object_or_404(
                SupportTicketService.base_queryset(request.user), pk=id
            )
            data = SupportTicketSerializer(ticket).data
            comments = ticket.comments.select_related("author").prefetch_related("attachments")
            data["comments"] = TicketCommentSerializer(comments, many=True).data
            return api_response(data=data, message="Ticket retrieved successfully")
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))


class TicketCreateAPIView(APIView):
    """Create a support ticket, with optional attachments and custom fields."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        tags=TAGS,
        summary="Create a support ticket",
        description=(
            "Creates a ticket for the current org. Accepts JSON or "
            "multipart/form-data (multipart required if uploading "
            "attachments). ``custom_fields`` is an optional "
            "``{field_key: value}`` dict for the support_ticket module."
        ),
        request={"multipart/form-data": SupportTicketWriteSerializer, "application/json": SupportTicketWriteSerializer},
        responses={201: OpenApiResponse(response=SupportTicketSerializer, description="Ticket created")},
    )
    def post(self, request):
        try:
            serializer = SupportTicketWriteSerializer(
                data=request.data, context={"request": request}
            )
            if not serializer.is_valid():
                return api_response(status=400, validation_errors=serializer.errors)
            ticket = serializer.save()
            data = SupportTicketSerializer(ticket).data
            return api_response(status=201, data=data, message="Ticket created successfully")
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))


class TicketUpdateAPIView(APIView):
    """Update a support ticket (partial update)."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        tags=TAGS,
        summary="Update a support ticket",
        description=(
            "Partial update of a ticket's fields. Use "
            "``happy_code_confirm`` when moving ``status`` to Closed (4) "
            "on a ticket that has a client — see the status-update "
            "endpoint for the same rule."
        ),
        parameters=[OpenApiParameter(name="id", type=str, location=OpenApiParameter.PATH, description="Ticket UUID")],
        request={"multipart/form-data": SupportTicketWriteSerializer, "application/json": SupportTicketWriteSerializer},
        responses={200: OpenApiResponse(response=SupportTicketSerializer, description="Ticket updated")},
    )
    def patch(self, request, id):
        try:
            ticket = get_object_or_404(
                SupportTicket.undeleted_objects, pk=id, organization=request.user.organization
            )
            serializer = SupportTicketWriteSerializer(
                ticket, data=request.data, partial=True, context={"request": request}
            )
            if not serializer.is_valid():
                return api_response(status=400, validation_errors=serializer.errors)
            ticket = serializer.save()
            data = SupportTicketSerializer(ticket).data
            return api_response(data=data, message="Ticket updated successfully")
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))


class TicketStatusUpdateAPIView(APIView):
    """Dedicated status-transition endpoint — the most common mobile action
    (Open -> In Progress -> In Testing -> Resolved -> Closed).

    Reads ``request.data`` (not ``request.POST``, which stays empty for
    JSON bodies) and reuses the same ``SupportTicketService`` helpers the
    web Kanban view calls, so happy-code validation and activity logging
    behave identically on both surfaces.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=TAGS,
        summary="Update ticket status",
        description=(
            "Transitions a ticket's status. Closing (status=4) a ticket "
            "that has a client (directly or via its asset) requires "
            "``happy_code`` matching the ticket's generated happy code."
        ),
        parameters=[OpenApiParameter(name="id", type=str, location=OpenApiParameter.PATH, description="Ticket UUID")],
        request=TicketStatusUpdateSerializer,
        responses={200: OpenApiResponse(description="{'success': true}")},
    )
    def patch(self, request, id):
        try:
            from .models import STATUS_CHOICES, TicketActivity

            ticket = get_object_or_404(
                SupportTicket.undeleted_objects, pk=id, organization=request.user.organization
            )
            new_status = request.data.get("status")
            if new_status not in dict(STATUS_CHOICES):
                raise ValidationError("Invalid status.")

            old_status = ticket.status
            SupportTicketService.validate_close_transition(
                ticket, new_status, request.data.get("happy_code")
            )

            ticket.status = new_status
            ticket.updated_by = str(request.user.id)
            ticket.save(update_fields=["status", "updated_by"])

            SupportTicketService.log_status_change(ticket, old_status, request.user)

            return api_response(data={"success": True}, message="Ticket status updated successfully")
        except ValidationError as e:
            extra = e.params if hasattr(e, "params") and e.params else {}
            msg = e.message if hasattr(e, "message") else ", ".join(e.messages)
            return api_response(status=400, error_message=msg, data=extra or None)
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))


class TicketCommentAPIView(APIView):
    """List or add comments on a ticket."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        tags=TAGS,
        summary="List ticket comments",
        parameters=[OpenApiParameter(name="id", type=str, location=OpenApiParameter.PATH, description="Ticket UUID")],
        responses={200: OpenApiResponse(response=TicketCommentSerializer(many=True), description="Comments, oldest first")},
    )
    def get(self, request, id):
        try:
            ticket = get_object_or_404(
                SupportTicketService.base_queryset(request.user), pk=id
            )
            comments = ticket.comments.select_related("author").prefetch_related("attachments")
            data = TicketCommentSerializer(comments, many=True).data
            return api_response(data=data, message="Comments retrieved successfully")
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))

    @extend_schema(
        tags=TAGS,
        summary="Add a ticket comment",
        description="Adds a comment, with optional file attachments, and logs a comment activity.",
        parameters=[OpenApiParameter(name="id", type=str, location=OpenApiParameter.PATH, description="Ticket UUID")],
        request={"multipart/form-data": TicketCommentCreateSerializer, "application/json": TicketCommentCreateSerializer},
        responses={201: OpenApiResponse(response=TicketCommentSerializer, description="Comment created")},
    )
    def post(self, request, id):
        try:
            ticket = get_object_or_404(
                SupportTicketService.base_queryset(request.user), pk=id
            )
            serializer = TicketCommentCreateSerializer(
                data=request.data, context={"request": request, "ticket": ticket}
            )
            if not serializer.is_valid():
                return api_response(status=400, validation_errors=serializer.errors)
            comment = serializer.save()
            data = TicketCommentSerializer(comment).data
            return api_response(status=201, data=data, message="Comment added successfully")
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))


class TicketAttachmentDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=TAGS,
        summary="Delete a ticket attachment",
        parameters=[OpenApiParameter(name="id", type=str, location=OpenApiParameter.PATH, description="Attachment UUID")],
        responses={200: OpenApiResponse(description="Attachment deleted successfully")},
    )
    def delete(self, request, id):
        try:
            attachment = get_object_or_404(
                TicketAttachment, id=id, ticket__organization=request.user.organization
            )
            attachment.delete()
            return api_response(message="Attachment deleted successfully")
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))


class AssetSearchAPIView(APIView):
    """Typeahead search for the asset picker."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=TAGS,
        summary="Search assets for the ticket asset picker",
        parameters=[OpenApiParameter(name="q", type=str, required=False, description="Search text (name, tag, or serial no.)")],
        responses={200: OpenApiResponse(description="[{id, name, tag}]")},
    )
    def get(self, request):
        try:
            query = request.GET.get("q", "").strip()
            results = SupportTicketService.search_assets(request.user, query)
            return api_response(data=results, message="List get Successfully")
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))


class TechnicianSearchAPIView(APIView):
    """Typeahead search for the technician/assignee picker."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=TAGS,
        summary="Search technicians for the ticket assignee picker",
        parameters=[OpenApiParameter(name="q", type=str, required=False, description="Search text (name or email)")],
        responses={200: OpenApiResponse(description="[{id, full_name, email}]")},
    )
    def get(self, request):
        try:
            query = request.GET.get("q", "").strip()
            results = SupportTicketService.search_technicians(request.user, query)
            return api_response(data=results, message="List get Successfully")
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))
