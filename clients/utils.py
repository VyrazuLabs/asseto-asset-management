# utils.py
"""Utility functions and service layer for the ``clients`` app.

Exports include CSV/PDF export helpers and the ``ClientService`` class which
encapsulates business logic for client management. This consolidates service
logic into a single module as dictated by the project rules.
"""

import csv
import logging
from datetime import date
from io import BytesIO

from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from xhtml2pdf import pisa

from assets.models import Asset
from .models import Client, ClientContact, STATUS_CHOICES

logger = logging.getLogger(__name__)


def export_clients_csv_utils(request):
    """Generate a CSV file with client data.

    The variable ``client_queryset`` holds the filtered and annotated set of
    ``Client`` objects that will be iterated over.
    """
    try:
        today = date.today()
        client_queryset = (
            Client.undeleted_objects.filter(organization=request.user.organization)
            .annotate(
                asset_count=Count('assets', filter=Q(assets__is_deleted=False)),
                open_tickets_count=Count(
                    'assets__tickets',
                    filter=Q(assets__tickets__is_deleted=False) & ~Q(assets__tickets__status__in=['3', '4']),
                    distinct=True,
                ),
            )
            .order_by('-created_at')
        )

        search_term = request.GET.get("search", "").strip()
        status_filter = request.GET.get("status")
        if search_term:
            client_queryset = client_queryset.filter(
                Q(name__icontains=search_term) | Q(client_id__icontains=search_term)
            )
        if status_filter and status_filter != "All Statuses":
            client_queryset = client_queryset.filter(status=status_filter)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="export-clients-{today}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(
            [
                "Client ID",
                "Name",
                "Industry",
                "Contact Person",
                "Email",
                "Phone",
                "Total Assets",
                "Open Tickets",
                "Status",
            ]
        )

        for client in client_queryset:
            first_contact = client.contacts.first()
            writer.writerow([
                client.client_id,
                client.name,
                client.industry_name,
                first_contact.name if first_contact else '',
                first_contact.email if first_contact else '',
                first_contact.phone if first_contact else '',
                client.asset_count,
                client.open_tickets_count,
                client.get_status_display()
            ])
        return response
    except Exception:
        logger.exception("Error exporting clients CSV")
        return HttpResponse(status=500)


def export_clients_pdf_utils(request):
    """Generate a PDF document with client data.

    ``client_queryset`` mirrors the CSV export logic but is used to render a
    template for PDF generation.
    """
    try:
        today = date.today()
        client_queryset = (
            Client.undeleted_objects.filter(organization=request.user.organization)
            .annotate(
                asset_count=Count('assets', filter=Q(assets__is_deleted=False)),
                open_tickets_count=Count(
                    'assets__tickets',
                    filter=Q(assets__tickets__is_deleted=False) & ~Q(assets__tickets__status__in=['3', '4']),
                    distinct=True,
                ),
            )
            .order_by('-created_at')
        )

        search_term = request.GET.get("search", "").strip()
        status_filter = request.GET.get("status")
        if search_term:
            client_queryset = client_queryset.filter(
                Q(name__icontains=search_term) | Q(client_id__icontains=search_term)
            )
        if status_filter and status_filter != "All Statuses":
            client_queryset = client_queryset.filter(status=status_filter)

        context = {"clients": client_queryset}
        template = get_template("clients/clients-pdf.html")
        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="export-clients-{today}.pdf"'
            )
            return response
        return HttpResponse(status=500)
    except Exception:
        logger.exception("Error exporting clients PDF")
        return HttpResponse(status=500)


class ClientService:
    """Encapsulates client‑related operations.

    Service methods receive the ``request`` object only when they need
    request‑specific data such as the current user or query parameters.
    """

    @staticmethod
    def base_queryset(user):
        """Return the base queryset for the current user's organization."""
        return (
            Client.undeleted_objects.filter(organization=user.organization)
            .annotate(
                asset_count=Count('assets', filter=Q(assets__is_deleted=False)),
                open_tickets_count=Count(
                    'assets__tickets',
                    filter=Q(assets__tickets__is_deleted=False) & ~Q(assets__tickets__status__in=['3', '4']),
                    distinct=True,
                ),
            )
            .order_by('-created_at')
        )

    @staticmethod
    def stats(user):
        """Aggregate various client statistics."""
        client_queryset = ClientService.base_queryset(user)
        total_active_rentals = (
            client_queryset.aggregate(total=Sum("asset_count"))["total"] or 0
        )
        open_tickets_total = (
            client_queryset.aggregate(total=Sum("open_tickets_count"))["total"] or 0
        )
        return {
            "total_client_count": client_queryset.count(),
            "active_client_count": client_queryset.filter(status="1").count(),
            "review_client_count": client_queryset.filter(status="2").count(),
            "dormant_client_count": client_queryset.filter(status="3").count(),
            "inactive_client_count": client_queryset.filter(status="0").count(),
            "active_rentals_count": total_active_rentals,
            "open_tickets_count": open_tickets_total,
            "deleted_client_count": Client.deleted_objects.filter(
                organization=user.organization
            ).count(),
        }

    @staticmethod
    def list(request):
        """Return context data for the client list view."""
        client_queryset = ClientService.base_queryset(request.user)
        search_term = request.GET.get("search", "").strip()
        status_filter = request.GET.get("status", "")
        if search_term:
            client_queryset = client_queryset.filter(
                Q(name__icontains=search_term) | Q(client_id__icontains=search_term)
            )
        if status_filter and status_filter != "All Statuses":
            client_queryset = client_queryset.filter(status=status_filter)
        paginator = Paginator(client_queryset, 10, orphans=1)
        page_object = paginator.get_page(request.GET.get("page", 1))
        return {
            "sidebar": "clients",
            "title": "Client Directory",
            "page_object": page_object,
            "status_choices": [s for s in STATUS_CHOICES if s[0] in ("1", "0")],
            "search_query": search_term,
            "selected_status": status_filter,
            **ClientService.stats(request.user),
        }

    @staticmethod
    def create(request):
        """Create a new client and its contacts."""
        form = request.form
        client = form.save(commit=False)
        client.organization = request.user.organization
        client.created_by = request.user.id
        client.save()
        # contacts
        contact_names = request.POST.getlist("contact_name[]")
        contact_emails = request.POST.getlist("contact_email[]")
        contact_phones = request.POST.getlist("contact_phone[]")
        contact_roles = request.POST.getlist("contact_role[]")
        contact_notes = request.POST.getlist("contact_notes[]")
        for index, raw_name in enumerate(contact_names):
            contact_name = raw_name.strip()
            if not contact_name:
                continue
            ClientContact.objects.create(
                client=client,
                name=contact_name,
                email=(
                    contact_emails[index].strip() if index < len(contact_emails) else ""
                ),
                phone=(
                    contact_phones[index].strip() if index < len(contact_phones) else ""
                ),
                role_id=(
                    contact_roles[index]
                    if index < len(contact_roles) and contact_roles[index]
                    else None
                ),
                notes=(
                    contact_notes[index].strip() if index < len(contact_notes) else ""
                ),
            )
        return client

    @staticmethod
    def update(request, client_id: int):
        """Update an existing client and replace its contacts."""
        client = get_object_or_404(
            Client.undeleted_objects,
            pk=client_id,
            organization=request.user.organization,
        )
        form = request.form
        client = form.save(commit=False)
        client.updated_by = request.user.id
        client.save()
        # replace contacts
        client.contacts.all().delete()
        contact_names = request.POST.getlist("contact_name[]")
        contact_emails = request.POST.getlist("contact_email[]")
        contact_phones = request.POST.getlist("contact_phone[]")
        contact_roles = request.POST.getlist("contact_role[]")
        contact_notes = request.POST.getlist("contact_notes[]")
        for index, raw_name in enumerate(contact_names):
            contact_name = raw_name.strip()
            if not contact_name:
                continue
            ClientContact.objects.create(
                client=client,
                name=contact_name,
                email=(
                    contact_emails[index].strip() if index < len(contact_emails) else ""
                ),
                phone=(
                    contact_phones[index].strip() if index < len(contact_phones) else ""
                ),
                role_id=(
                    contact_roles[index]
                    if index < len(contact_roles) and contact_roles[index]
                    else None
                ),
                notes=(
                    contact_notes[index].strip() if index < len(contact_notes) else ""
                ),
            )
        return client

    @staticmethod
    def delete(request, client_id: int):
        """Soft‑delete a client."""
        client = get_object_or_404(
            Client.undeleted_objects,
            pk=client_id,
            organization=request.user.organization,
        )
        client.soft_delete()

    @staticmethod
    def toggle_status(request, client_id: int):
        """Toggle active/inactive status for a client."""
        client = get_object_or_404(
            Client.undeleted_objects,
            pk=client_id,
            organization=request.user.organization,
        )
        client.status = "0" if client.status == "1" else "1"
        client.save()

    @staticmethod
    def search(request, page: int):
        """Search clients for the AJAX table view."""
        client_queryset = ClientService.base_queryset(request.user)
        search_text = request.GET.get("search_text", "").strip()
        if search_text:
            client_queryset = client_queryset.filter(
                Q(name__icontains=search_text)
                | Q(client_id__icontains=search_text)
                | Q(contacts__name__icontains=search_text)
                | Q(contacts__email__icontains=search_text)
                | Q(rental_type__icontains=search_text)
            ).distinct()
        status_filter = request.GET.get("status", "")
        if status_filter and status_filter != "All Statuses":
            client_queryset = client_queryset.filter(status=status_filter)
        paginator = Paginator(client_queryset, 10, orphans=1)
        page_object = paginator.get_page(page)
        return {"sidebar": "clients", "page_object": page_object}

    @staticmethod
    def export_csv(request):
        return export_clients_csv_utils(request)

    @staticmethod
    def export_pdf(request):
        return export_clients_pdf_utils(request)

    @staticmethod
    def get_detail_context(request, client_id: int):
        """Prepare context for the client detail view.

        This consolidates the heavy query logic formerly in the view, keeping the
        view thin and adhering to the Single‑Responsibility principle.
        """
        client = get_object_or_404(
            ClientService.base_queryset(request.user), pk=client_id
        )
        # Asset pagination and related data
        assets_qs = (
            client.assets.filter(is_deleted=False)
            .select_related(
                "product__product_type", "product__product_sub_category", "location"
            )
            .prefetch_related("images")
            .order_by("-created_at")
        )
        asset_search = request.GET.get("asset_search", "").strip()
        if asset_search:
            assets_qs = assets_qs.filter(
                Q(tag__icontains=asset_search) | Q(name__icontains=asset_search)
            )
        assets_page = Paginator(assets_qs, 10, orphans=1).get_page(
            request.GET.get("asset_page")
        )
        asset_ids = [a.id for a in assets_page]
        # Collect related data
        from assets.models import AssetImage, AssignAsset
        from audit.models import Audit
        from collections import defaultdict

        asset_images = {
            img.asset_id: img
            for img in AssetImage.objects.filter(
                asset__organization=request.user.organization, asset_id__in=asset_ids
            ).order_by("-uploaded_at")
        }
        asset_user_map = {}
        for assign in (
            AssignAsset.objects.select_related("user")
            .filter(asset_id__in=asset_ids)
            .order_by("-assigned_date")
        ):
            asset_user_map[assign.asset_id] = (
                {"full_name": assign.user.full_name, "image": assign.user.profile_pic}
                if assign.user
                else None
            )
        asset_conditions_map = defaultdict(list)
        for audit in Audit.objects.filter(asset_id__in=asset_ids):
            asset_conditions_map[audit.asset_id].append(audit.condition)
        total_val = assets_qs.aggregate(total=Sum("price"))["total"] or 0
        total_asset_value = total_val / 1_000_000
        # History aggregation
        client_history = client.history.all()[:10]
        asset_history = Asset.history.filter(client=client)[:10]
        activities = []
        for client_history_entry in client_history:
            history_type_display = client_history_entry.get_history_type_display()
            action = {"Created": "Registration", "Changed": "Updated"}.get(
                history_type_display, history_type_display
            )
            notes = (
                "Initial registration of the client record."
                if history_type_display == "Created"
                else (
                    "Client profile information was updated."
                    if history_type_display == "Changed"
                    else f"Client record {history_type_display.lower()}."
                )
            )
            activities.append(
                {
                    "date": client_history_entry.history_date,
                    "user": client_history_entry.history_user,
                    "type": "Client",
                    "action": action,
                    "notes": notes,
                    "history_type": client_history_entry.history_type,
                }
            )
        for asset_history_entry in asset_history:
            history_type_display = asset_history_entry.get_history_type_display()
            action = (
                "Updated" if history_type_display == "Changed" else history_type_display
            )
            activities.append(
                {
                    "date": asset_history_entry.history_date,
                    "user": asset_history_entry.history_user,
                    "type": "Asset",
                    "action": action,
                    "notes": f"Asset {asset_history_entry.tag} was {history_type_display.lower()}.",
                    "history_type": asset_history_entry.history_type,
                }
            )
        activities.sort(key=lambda x: x["date"], reverse=True)
        return {
            "sidebar": "clients",
            "title": f"{client.name} | Asseto",
            "client": client,
            "assets_page_object": assets_page,
            "asset_images": asset_images,
            "asset_user_map": asset_user_map,
            "asset_conditions_map": asset_conditions_map,
            "asset_search": asset_search,
            "total_asset_value": total_asset_value,
            "activities": activities[:15],
        }
