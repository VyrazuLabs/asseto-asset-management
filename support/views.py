from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import SupportTicketForm
from .models import SupportTicket
from .utils import SupportTicketService


@login_required
def ticket_list(request):
    context = SupportTicketService.list(request)
    return render(request, "support/ticket_list.html", context)


@login_required
def add_ticket(request):
    # ── Severity → Priority mapping ──────────────────────────────────────────
    SEVERITY_PRIORITY_MAP = {"critical": "3", "warning": "2", "info": "1"}

    # ── Build initial data from alarm URL params (GET request) ───────────────
    initial_data = {}
    alarm_id = request.GET.get("alarm_id") or request.POST.get("alarm_id")
    prefill_asset = None  # asset object to auto-fill the search input in template

    if request.method == "GET":
        asset_id = request.GET.get("asset_id")
        subject = request.GET.get("subject")
        severity = request.GET.get("severity", "").lower()

        if subject:
            initial_data["subject"] = subject
        if severity in SEVERITY_PRIORITY_MAP:
            initial_data["priority"] = SEVERITY_PRIORITY_MAP[severity]

        form = SupportTicketForm(initial=initial_data, organization=request.user.organization)

        # If asset_id passed, pre-populate the asset field queryset AND pass
        # the asset object to the template so JS can fill the visible text box.
        if asset_id:
            try:
                from assets.models import Asset
                asset = Asset.undeleted_objects.get(
                    pk=asset_id, organization=request.user.organization
                )
                # Make the asset available in the hidden <select> queryset
                form.fields["asset"].queryset = (
                    form.fields["asset"].queryset | Asset.undeleted_objects.filter(pk=asset_id)
                )
                form.initial["asset"] = asset.pk
                prefill_asset = asset          # passed to template for JS
            except Exception:
                pass

    elif request.method == "POST":
        form = SupportTicketForm(
            request.POST, request.FILES, organization=request.user.organization
        )
        if form.is_valid():
            ticket = SupportTicketService.create(request, form)

            # Link the alarm to this ticket and auto-acknowledge it
            if alarm_id:
                try:
                    from iot.models.sensor_models import SensorAlarm
                    from django.utils import timezone
                    alarm = SensorAlarm.objects.get(pk=alarm_id)
                    alarm.ticket = ticket
                    # Auto-acknowledge if still active
                    if alarm.status == "active":
                        alarm.status = "acknowledged"
                        alarm.acknowledged_by = request.user
                        alarm.acknowledged_at = timezone.now()
                    alarm.save()
                except Exception:
                    pass

            messages.success(request, "Ticket created successfully.")
            return redirect("support:ticket_list")

    context = {
        "sidebar": "support",
        "title": "New Support Request",
        "form": form,
        "alarm_id": alarm_id,
        "prefill_asset": prefill_asset,

    }
    return render(request, "support/ticket_add.html", context)



@login_required
def ticket_detail(request, id):
    context = SupportTicketService.get_detail_context(request, id)
    ticket = context["ticket"]

    if request.method == "POST":
        try:
            comment, created = SupportTicketService.add_comment(request, ticket)
            if created:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    html = SupportTicketService.render_comment_html(comment, request)
                    return JsonResponse(
                        {"success": True, "html": html, "comment_id": str(comment.id)}
                    )
                messages.success(request, "Comment posted successfully.")
                return redirect("support:ticket_detail", id=id)
        except ValidationError as e:
            err_msg = e.message if hasattr(e, 'message') else ", ".join(e.messages)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": err_msg})
            messages.error(request, err_msg)
            return redirect("support:ticket_detail", id=id)

    return render(request, "support/ticket_detail.html", context)


@login_required
def update_ticket(request, id):
    ticket = get_object_or_404(
        SupportTicket.undeleted_objects, pk=id, organization=request.user.organization
    )
    form = SupportTicketForm(instance=ticket, organization=request.user.organization)

    if request.method == "POST":
        form = SupportTicketForm(
            request.POST, instance=ticket, organization=request.user.organization
        )
        if form.is_valid():
            try:
                SupportTicketService.update(request, id, form)
                messages.success(request, "Ticket updated successfully.")
                return redirect("support:ticket_list")
            except ValidationError as e:
                messages.error(request, e.message if hasattr(e, 'message') else ", ".join(e.messages))

    context = {
        "sidebar": "support",
        "title": f"Edit {ticket.subject}",
        "form": form,
        "ticket": ticket,
        "activities": ticket.activities.order_by("-created_at")[:20],
    }
    return render(request, "support/ticket_edit.html", context)


@login_required
def delete_ticket(request, id):
    if request.method == "POST":
        SupportTicketService.delete(request, id)
        messages.success(request, "Ticket deleted successfully.")
    return redirect("support:ticket_list")


@login_required
def search_tickets(request, page):
    context = SupportTicketService.search(request, page)
    return render(request, "support/tickets-data.html", context)


@login_required
def export_tickets(request):
    return SupportTicketService.export_csv(request)


@login_required
def delete_ticket_attachment(request, id):
    ticket_id = SupportTicketService.delete_attachment(request, id)
    messages.success(request, "Attachment deleted successfully.")
    return redirect("support:ticket_update", id=ticket_id)


@login_required
def asset_search(request):
    query = request.GET.get("q", "").strip()
    results = SupportTicketService.search_assets(request.user, query)
    return JsonResponse({"results": results})


@login_required
def technician_search(request):
    query = request.GET.get("q", "").strip()
    results = SupportTicketService.search_technicians(request.user, query)
    return JsonResponse({"results": results})


@login_required
@require_POST
def update_ticket_status(request, id):
    """Update ticket status from Kanban drag-and-drop."""
    try:
        result = SupportTicketService.update_status(request, id)
        return JsonResponse(result)
    except ValidationError as e:
        extra = {}
        if hasattr(e, "params") and e.params:
            extra = e.params
        return JsonResponse(
            {"success": False, "error": e.message if hasattr(e, "message") else ", ".join(e.messages), **extra},
            status=400,
        )
