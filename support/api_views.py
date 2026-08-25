from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiParameter

from common.API_custom_response import api_response, get_detailed_errors_info, log_error_to_terminal
from common.pagination import add_pagination

from .models import SupportTicket, TicketAttachment
from .serializers import (
    SupportTicketSerializer,
    SupportTicketWriteSerializer,
    TicketCommentSerializer,
    TicketCommentCreateSerializer,
)
from .utils import SupportTicketService


class TicketListAPIView(APIView):
    """List support tickets for the current org, paginated and filterable
    by ``status``, ``priority``, ``ticket_type``, and free-text ``search``
    (see ``SupportTicketService.apply_filters``)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="page", type=int, default=1, description="Page number"),
            OpenApiParameter(name="status", type=str, required=False),
            OpenApiParameter(name="priority", type=str, required=False),
            OpenApiParameter(name="ticket_type", type=str, required=False),
            OpenApiParameter(name="search", type=str, required=False),
        ]
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

    @extend_schema(request={"multipart/form-data": SupportTicketWriteSerializer})
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

    @extend_schema(request={"multipart/form-data": SupportTicketWriteSerializer})
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

    def get(self, request):
        try:
            query = request.GET.get("q", "").strip()
            results = SupportTicketService.search_technicians(request.user, query)
            return api_response(data=results, message="List get Successfully")
        except Exception as e:
            error_info = get_detailed_errors_info(e)
            log_error_to_terminal(error_info)
            return api_response(status=500, error_message=str(e))
