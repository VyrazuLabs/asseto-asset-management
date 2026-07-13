# utils.py
"""Utility functions and service layer for the ``support`` app.

Exports the ``SupportTicketService`` class which encapsulates business logic
for support ticket management. This consolidates service logic into a single
module as dictated by the project rules (DJANGO_DEVELOPMENT_RULES).
"""

import csv
import logging
from itertools import chain

from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.timezone import now

from assets.models import Asset
from authentication.models import User

from .models import (
    SupportTicket,
    TicketAttachment,
    TicketActivity,
    TicketComment,
    TicketCommentAttachment,
    STATUS_CHOICES,
    PRIORITY_CHOICES,
    TICKET_TYPE_CHOICES,
)

logger = logging.getLogger(__name__)


class SupportTicketService:
    """Encapsulates support-ticket-related operations.

    Service methods receive the ``request`` object only when they need
    request-specific data such as the current user or query parameters.
    Follows the same Service pattern used in ``clients/utils.py``.
    """

    # ------------------------------------------------------------------
    # Base queryset & stats
    # ------------------------------------------------------------------

    @staticmethod
    def base_queryset(user):
        """Return the base queryset for the current user's organization."""
        return (
            SupportTicket.undeleted_objects.filter(organization=user.organization)
            .select_related("asset", "assigned_to")
            .order_by("-created_at")
        )

    @staticmethod
    def stats(user):
        """Compute stat-card values for the ticket list dashboard."""
        qs = SupportTicketService.base_queryset(user)
        return {
            "total_active": qs.exclude(status="4").count(),
            "pending_parts": qs.filter(
                status="0", ticket_type="hardware_repair"
            ).count(),
            "overdue_count": qs.filter(status="0", estimated_eta__lt=now()).count(),
            "critical_count": qs.filter(
                priority__in=["3", "2"], status="0"
            ).count(),
        }

    # ------------------------------------------------------------------
    # Filtering (DRY – shared by list, search, and export)
    # ------------------------------------------------------------------

    @staticmethod
    def apply_filters(qs, params):
        """Apply search, status, priority, and ticket_type filters to *qs*.

        ``params`` is typically ``request.GET``.
        """
        search = params.get("search", "").strip()
        status = params.get("status")
        priority = params.get("priority")
        ticket_type = params.get("ticket_type")

        if search:
            qs = qs.filter(
                Q(ticket_id__icontains=search)
                | Q(subject__icontains=search)
                | Q(asset__name__icontains=search)
                | Q(assigned_to__full_name__icontains=search)
            )
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        if ticket_type:
            qs = qs.filter(ticket_type=ticket_type)

        return qs.order_by("-created_at")

    # ------------------------------------------------------------------
    # Asset images helper
    # ------------------------------------------------------------------

    @staticmethod
    def collect_asset_images(page_object):
        """Build a dict mapping asset IDs to their first image."""
        asset_images = {}
        for ticket in page_object:
            if ticket.asset:
                asset_images[ticket.asset.id] = ticket.asset.images.first()
        return asset_images

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    @staticmethod
    def list(request):
        """Return context data for the ticket list view."""
        qs = SupportTicketService.base_queryset(request.user)
        qs = SupportTicketService.apply_filters(qs, request.GET)

        paginator = Paginator(qs, 10, orphans=1)
        page_object = paginator.get_page(request.GET.get("page", 1))

        return {
            "sidebar": "support",
            "title": "Maintenance Tickets | Asseto",
            "page_object": page_object,
            "all_tickets": qs,  # For Kanban view
            "status_choices": STATUS_CHOICES,
            "priority_choices": PRIORITY_CHOICES,
            "ticket_type_choices": TICKET_TYPE_CHOICES,
            "asset_images": SupportTicketService.collect_asset_images(page_object),
            **SupportTicketService.stats(request.user),
        }

    # ------------------------------------------------------------------
    # Search (HTMX partial)
    # ------------------------------------------------------------------

    @staticmethod
    def search(request, page):
        """Search tickets for the AJAX / HTMX table view."""
        qs = SupportTicketService.base_queryset(request.user)
        qs = SupportTicketService.apply_filters(qs, request.GET)

        paginator = Paginator(qs, 10, orphans=1)
        page_object = paginator.get_page(page)

        return {
            "page_object": page_object,
            "asset_images": SupportTicketService.collect_asset_images(page_object),
        }

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    def create(request, form):
        """Create a new ticket with attachments and initial activity."""
        try:
            ticket = form.save(commit=False)
            ticket.organization = request.user.organization
            ticket.created_by = str(request.user.id)
            ticket.save()

            # Handle file uploads
            SupportTicketService._save_attachments(
                ticket, request.FILES.getlist("attachments"), request.user
            )

            # Create initial activity
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type="created",
                description=(
                    f"Ticket initiated by {request.user.get_full_name()}."
                ),
                performed_by=request.user,
            )
            return ticket
        except Exception:
            logger.exception("Error creating support ticket")
            raise

    # ------------------------------------------------------------------
    # Detail
    # ------------------------------------------------------------------

    @staticmethod
    def get_detail_context(request, ticket_id):
        """Prepare context for the ticket detail view.

        This consolidates the heavy query logic formerly in the view,
        keeping the view thin (Single-Responsibility principle).
        """
        ticket = get_object_or_404(
            SupportTicket.undeleted_objects.select_related(
                "asset", "assigned_to", "department", "location",
            ),
            pk=ticket_id,
            organization=request.user.organization,
        )

        history_qs = ticket.history.all()
        comments = ticket.comments.select_related("author").prefetch_related(
            "attachments"
        )
        activities_qs = (
            ticket.activities.filter(is_internal=False)
            .exclude(activity_type="created")
        )

        combined = sorted(
            chain(activities_qs, history_qs),
            key=lambda x: x.created_at if hasattr(x, "activity_type") else x.history_date,
            reverse=True,
        )
        paginator = Paginator(combined, 10, orphans=1)
        page_object = paginator.get_page(request.GET.get("page", 1))

        return {
            "sidebar": "support",
            "title": f"{ticket.subject} | Asseto",
            "ticket": ticket,
            "attachments": ticket.attachments.order_by("-created_at"),
            "comments": comments,
            "page_object": page_object,
        }

    # ------------------------------------------------------------------
    # Add comment (from detail page)
    # ------------------------------------------------------------------

    ALLOWED_EXTENSIONS = {
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg',
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'rtf',
        'zip', 'rar', 'tar', 'gz', '7z',
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    @staticmethod
    def validate_attachments(files):
        """Validate files for size and safe extensions."""
        for f in files:
            if f.size > SupportTicketService.MAX_FILE_SIZE:
                raise ValidationError(f"File '{f.name}' exceeds the 10MB size limit.")
            
            ext = f.name.split('.')[-1].lower() if '.' in f.name else ''
            if ext not in SupportTicketService.ALLOWED_EXTENSIONS:
                raise ValidationError(f"File type '.{ext}' is not allowed.")

    # ------------------------------------------------------------------
    # Add comment (from detail page)
    # ------------------------------------------------------------------

    @staticmethod
    def add_comment(request, ticket):
        """Create a comment with optional attachments and log activity.

        Returns ``(comment, True)`` on success, ``(None, False)`` if blank.
        """
        comment_content = request.POST.get("comment_content", "").strip()
        if not comment_content:
            return None, False

        files = request.FILES.getlist("comment_attachments")
        SupportTicketService.validate_attachments(files)

        is_staff = request.user.is_staff or request.user.is_superuser

        with transaction.atomic():
            comment = TicketComment.objects.create(
                ticket=ticket,
                content=comment_content,
                author=request.user,
                is_staff_comment=is_staff,
            )

            for f in files:
                TicketCommentAttachment.objects.create(
                    comment=comment,
                    file=f,
                    file_name=f.name,
                    file_size=f.size,
                )

            TicketActivity.objects.create(
                ticket=ticket,
                activity_type="comment",
                description=comment_content,
                is_internal=False,
                performed_by=request.user,
            )

        return comment, True

    @staticmethod
    def add_client_comment(request, ticket, contact):
        """Create a comment from the Client Portal with optional attachments and log activity.

        Returns ``(comment, True)`` on success, ``(None, False)`` if blank.
        """
        comment_content = request.POST.get("comment_content", "").strip()
        if not comment_content:
            return None, False

        files = request.FILES.getlist("comment_attachments")
        SupportTicketService.validate_attachments(files)

        with transaction.atomic():
            comment = TicketComment.objects.create(
                ticket=ticket,
                content=comment_content,
                author=None,
                contact=contact,
                client=contact.client,
                is_staff_comment=False,
            )

            for f in files:
                TicketCommentAttachment.objects.create(
                    comment=comment,
                    file=f,
                    file_name=f.name,
                    file_size=f.size,
                )

            TicketActivity.objects.create(
                ticket=ticket,
                activity_type="comment",
                description=comment_content,
                is_internal=False,
                performed_by=None,
                contact=contact,
            )

        return comment, True

    @staticmethod
    def render_comment_html(comment, request):
        """Render a single comment for AJAX response."""
        return render_to_string(
            "support/includes/comment_item.html",
            {"comment": comment},
            request=request,
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    def update(request, ticket_id, form):
        """Update a ticket, log status/assignment changes, and handle notes.

        Returns the updated ``SupportTicket`` instance.
        """
        ticket = get_object_or_404(
            SupportTicket.undeleted_objects,
            pk=ticket_id,
            organization=request.user.organization,
        )
        old_status = ticket.status
        old_assigned = ticket.assigned_to

        # Validate happy code when closing a ticket (status = 4)
        new_status = request.POST.get("status", old_status)
        if new_status == "4" and old_status != "4":
            if not ticket.happy_code:
                raise ValidationError(
                    "This ticket does not have a happy code. "
                    "Please ask the client to provide one."
                )
            submitted_code = request.POST.get("happy_code", "").strip().upper()
            if not submitted_code:
                raise ValidationError(
                    "Happy code is required to close this ticket. "
                    "Please enter the code provided by the client."
                )
            expected_code = ticket.happy_code.upper()
            if submitted_code != expected_code and submitted_code != f"HC-{expected_code}":
                raise ValidationError(
                    "Invalid happy code. Please check with the client for the correct code."
                )

        ticket = form.save(commit=False)
        ticket.updated_by = str(request.user.id)
        ticket.save()

        # Log status change
        if old_status != ticket.status:
            status_map = dict(STATUS_CHOICES)
            old_label = status_map.get(old_status, old_status)
            new_label = status_map.get(str(ticket.status), ticket.status)
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type="status_changed",
                description=(
                    f"Status changed from {old_label} to {new_label}."
                ),
                performed_by=request.user,
            )

        # Log reassignment
        if old_assigned != ticket.assigned_to:
            desc = (
                f"Ticket assigned to {ticket.assigned_to.get_full_name()}."
                if ticket.assigned_to
                else "Ticket unassigned."
            )
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type="reassigned",
                description=desc,
                performed_by=request.user,
            )

        # Handle note / comment
        note_content = request.POST.get("note_content", "").strip()
        if note_content:
            is_internal = request.POST.get("is_internal") == "on"
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type="internal_note" if is_internal else "comment",
                description=note_content,
                is_internal=is_internal,
                performed_by=request.user,
            )

        # Handle new file uploads
        SupportTicketService._save_attachments(
            ticket, request.FILES.getlist("attachments"), request.user
        )

        return ticket

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    def delete(request, ticket_id):
        """Soft-delete a ticket."""
        ticket = get_object_or_404(
            SupportTicket.undeleted_objects,
            pk=ticket_id,
            organization=request.user.organization,
        )
        ticket.soft_delete()

    # ------------------------------------------------------------------
    # Delete attachment
    # ------------------------------------------------------------------

    @staticmethod
    def delete_attachment(request, attachment_id):
        """Delete a ticket attachment and return the parent ticket's ID."""
        attachment = get_object_or_404(
            TicketAttachment,
            id=attachment_id,
            ticket__organization=request.user.organization,
        )
        ticket_id = attachment.ticket.id
        attachment.delete()
        return ticket_id

    # ------------------------------------------------------------------
    # Export CSV
    # ------------------------------------------------------------------

    @staticmethod
    def export_csv(request):
        """Generate a CSV file with filtered ticket data."""
        try:
            qs = SupportTicketService.base_queryset(request.user)
            qs = SupportTicketService.apply_filters(qs, request.GET)

            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="tickets.csv"'

            writer = csv.writer(response)
            writer.writerow([
                "Ticket ID",
                "Subject",
                "Asset",
                "Priority",
                "Status",
                "Assigned To",
                "Created At",
            ])

            for ticket in qs:
                writer.writerow([
                    ticket.ticket_id,
                    ticket.subject,
                    ticket.asset.name if ticket.asset else "",
                    ticket.priority,
                    ticket.status,
                    (
                        ticket.assigned_to.get_full_name()
                        if ticket.assigned_to
                        else "Unassigned"
                    ),
                    ticket.created_at,
                ])

            return response
        except Exception:
            logger.exception("Error exporting tickets CSV")
            return HttpResponse(status=500)

    # ------------------------------------------------------------------
    # Asset search (JSON API)
    # ------------------------------------------------------------------

    @staticmethod
    def search_assets(user, query):
        """Search assets for the autocomplete dropdown.

        Returns a list of dicts suitable for ``JsonResponse``.
        """
        if not query:
            assets = Asset.undeleted_objects.filter(
                organization=user.organization,
            ).order_by("-created_at")[:10]
        else:
            assets = Asset.undeleted_objects.filter(
                Q(organization=user.organization),
                Q(name__icontains=query)
                | Q(tag__icontains=query)
                | Q(serial_no__icontains=query),
            )[:10]

        return [
            {"id": str(asset.id), "name": asset.name, "tag": asset.tag}
            for asset in assets
        ]

    # ------------------------------------------------------------------
    # Technician search (JSON API)
    # ------------------------------------------------------------------

    @staticmethod
    def search_technicians(user, query):
        """Search technicians for the autocomplete dropdown.

        Returns a list of dicts suitable for ``JsonResponse``.
        """
        if not query:
            users = User.objects.filter(
                organization=user.organization,
            ).order_by("full_name")[:10]
        else:
            users = User.objects.filter(
                Q(organization=user.organization),
                Q(full_name__icontains=query) | Q(email__icontains=query),
            )[:10]

        return [
            {
                "id": str(u.id),
                "full_name": u.get_full_name(),
                "email": u.email,
            }
            for u in users
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _save_attachments(ticket, files, user):
        """Persist a list of uploaded files as ``TicketAttachment`` records."""
        for f in files:
            TicketAttachment.objects.create(
                ticket=ticket,
                file=f,
                file_name=f.name,
                file_size=f.size,
                uploaded_by=user,
            )
