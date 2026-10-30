import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import HttpResponse, JsonResponse

from clients.models import Client, ClientContact
from assets.models import Asset, AssetImage, AssignAsset
from assets.utils import first_image_map
from support.models import (
    SupportTicket,
    TicketAttachment,
    TicketActivity,
    TicketComment,
    TicketCommentAttachment,
    STATUS_CHOICES,
    PRIORITY_CHOICES,
    TICKET_TYPE_CHOICES,
)
from .forms import ClientSupportTicketForm
from support.utils import SupportTicketService
from django.core.exceptions import ValidationError
from assets.models import AssetStatus
from dashboard.models import ProductCategory, ProductType, Location
from vendors.models import Vendor
from .utils import (
    create_otp_for_contact,
    verify_otp_for_contact,
    otp_remaining_seconds,
)

# ─── Helper ──────────────────────────────────────────────────────────


def _get_contact_and_client(request):
    """Fetch the authenticated ClientContact and their Client from session."""
    contact_id = request.session.get("client_contact_id")
    if not contact_id:
        return None, None
    try:
        contact = ClientContact.objects.select_related("client").get(
            id=contact_id,
            is_portal_active=True,
            is_deleted=False,
            client__is_deleted=False,
        )
        return contact, contact.client
    except ClientContact.DoesNotExist:
        for key in ("client_contact_id", "client_id"):
            request.session.pop(key, None)
        return None, None


# ─── Authentication Views ────────────────────────────────────────────


def client_portal_login(request):
    """Step 1: Client enters email → OTP is sent."""
    # If already logged in with a still-valid session, go to dashboard
    if request.session.get("client_contact_id"):
        contact, _ = _get_contact_and_client(request)
        if contact:
            return redirect("client_portal:dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()

        if not email:
            messages.error(request, "Please enter your email address.")
            return redirect("client_portal:login")

        # Find the correct contact with portal access for this email.
        # Use the most recently created one to handle edge cases where
        # multiple contacts share the same email (e.g. after a re-save).
        contact = (
            ClientContact.objects.filter(
                email__iexact=email,
                is_portal_active=True,
                is_deleted=False,
                client__is_deleted=False,
            )
            .select_related("client")
            .order_by("-created_at")  # most recently created first
            .first()
        )

        if not contact:
            messages.error(
                request,
                "No portal access found for this email. Please contact your administrator.",
            )
            return redirect("client_portal:login")

        # Generate & send OTP
        try:
            create_otp_for_contact(contact)
            request.session["pending_contact_id"] = str(contact.id)
            request.session["pending_contact_email"] = contact.email  # use stored email
            messages.success(request, f"A verification code has been sent to {contact.email}")
            return redirect("client_portal:verify_otp")
        except Exception as e:
            messages.error(
                request, "Failed to send verification code. Please try again later."
            )
            return redirect("client_portal:login")

    # GET request: clear any stale pending OTP session keys so that
    # navigating back from the OTP page does not leave ghost state
    # that would cause a confusing "No portal access" message on refresh.
    for key in ("pending_contact_id", "pending_contact_email", "last_otp_resend"):
        request.session.pop(key, None)

    return render(request, "client_portal/login.html")


def client_portal_verify_otp(request):
    """Step 2: Client enters the OTP received via email."""
    pending_id = request.session.get("pending_contact_id")
    pending_email = request.session.get("pending_contact_email", "")

    if not pending_id:
        return redirect("client_portal:login")

    try:
        contact = ClientContact.objects.get(
            id=pending_id,
            is_portal_active=True,
            is_deleted=False,
            client__is_deleted=False,
        )
    except ClientContact.DoesNotExist:
        # Stale or invalid pending session — restart login flow
        for key in ("pending_contact_id", "pending_contact_email"):
            request.session.pop(key, None)
        messages.error(request, "Your session has expired. Please log in again.")
        return redirect("client_portal:login")
    otp_seconds = otp_remaining_seconds(contact)

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        if not entered_otp:
            messages.error(request, "Please enter the verification code.")
            return render(
                request,
                "client_portal/verify-otp.html",
                {"email": pending_email, "otp_seconds": otp_seconds},
            )

        success, message = verify_otp_for_contact(contact, entered_otp)

        if success:
            # Login successful — create authenticated session
            request.session["client_contact_id"] = str(contact.id)
            request.session["client_id"] = str(contact.client_id)

            # Clean up pending keys
            request.session.pop("pending_contact_id", None)
            request.session.pop("pending_contact_email", None)

            request.session["show_welcome_banner"] = True
            return redirect("client_portal:dashboard")
        else:
            messages.error(request, message)

    return render(
        request,
        "client_portal/verify-otp.html",
        {"email": pending_email, "otp_seconds": otp_seconds},
    )


def client_portal_logout(request):
    """Clear client portal session."""
    keys_to_remove = [
        "client_contact_id",
        "client_id",
        "pending_contact_id",
        "pending_contact_email",
    ]
    for key in keys_to_remove:
        request.session.pop(key, None)
    messages.success(request, "You have been logged out successfully.")
    return redirect("client_portal:login")


from datetime import datetime

def client_portal_resend_otp(request):
    """Resend OTP with cooldown protection."""
    pending_id = request.session.get("pending_contact_id")
    if not pending_id:
        return redirect("client_portal:login")

    # Rate limit: 1 resend per 60 seconds
    last_resend = request.session.get("last_otp_resend")
    if last_resend:
        elapsed = timezone.now() - datetime.fromisoformat(last_resend)
        if elapsed.total_seconds() < 60:
            remaining = int(60 - elapsed.total_seconds())
            messages.warning(request, f"Please wait {remaining}s before requesting another code.")
            return redirect("client_portal:verify_otp")

    try:
        contact = ClientContact.objects.get(
            id=pending_id,
            is_portal_active=True,
            is_deleted=False,
            client__is_deleted=False,
        )
    except ClientContact.DoesNotExist:
        for key in ("pending_contact_id", "pending_contact_email"):
            request.session.pop(key, None)
        messages.error(request, "Your session has expired. Please log in again.")
        return redirect("client_portal:login")
    try:
        create_otp_for_contact(contact)
        request.session["last_otp_resend"] = timezone.now().isoformat()
        messages.success(request, "A new verification code has been sent.")
    except Exception:
        messages.error(request, "Failed to send code. Please try again.")
    
    return redirect("client_portal:verify_otp")


# ─── Dashboard (Overview) ───────────────────────────────────────────


def client_portal_dashboard(request):
    """Client Portal Dashboard Overview."""
    contact, client = _get_contact_and_client(request)
    if not contact:
        return redirect("client_portal:login")

    show_welcome = request.session.pop("show_welcome_banner", False)

    client_assets = Asset.undeleted_objects.filter(client=client)
    asset_stats = client_assets.aggregate(total=Count("id"), value=Sum("price"))
    total_assets = asset_stats["total"]
    total_value = asset_stats["value"] or 0

    tickets_qs = _client_ticket_base_qs(client)
    open_tickets = tickets_qs.exclude(status__in=["3", "4"]).count()

    # Recent support activity (latest 5 tickets for the client)
    recent_tickets = list(
        tickets_qs.select_related("asset", "assigned_to").order_by("-created_at")[:5]
    )
    recent_asset_ids = [t.asset_id for t in recent_tickets if t.asset_id]
    recent_asset_images = first_image_map(recent_asset_ids)

    # Product distribution (matches the "Product Category" field in the add form)
    cat_colors = [
        "#435ebe",
        "#198754",
        "#ffc107",
        "#dc3545",
        "#0dcaf0",
        "#6f42c1",
        "#fd7e14",
        "#20c997",
    ]
    # Grouped in the database: one query returns every category count instead
    # of loading every asset row into Python. Coalesce keeps assets without a
    # product under "Uncategorized", as the previous loop did.
    cat_rows = (
        client_assets.annotate(
            cat_name=Coalesce("product__name", Value("Uncategorized"))
        )
        .values("cat_name")
        .annotate(cat_count=Count("id"))
        .order_by("-cat_count", "cat_name")
    )
    cat_labels = [row["cat_name"] for row in cat_rows]
    cat_values = [row["cat_count"] for row in cat_rows]
    cat_colors_used = [cat_colors[i % len(cat_colors)] for i in range(len(cat_labels))]

    context = {
        "cp_sidebar": "overview",
        "contact": contact,
        "client": client,
        "show_welcome_banner": show_welcome,
        "total_assets": total_assets,
        "total_value": total_value,
        "open_tickets": open_tickets,
        "recent_tickets": recent_tickets,
        "recent_asset_images": recent_asset_images,
        "cat_labels": cat_labels,
        "cat_values": cat_values,
        "cat_colors": cat_colors_used,
    }
    return render(request, "client_portal/dashboard.html", context)


# ─── Assets List ──────────────────────────────────────────────────

PAGE_SIZE = 25
ORPHANS = 3


def client_portal_assets(request):
    """Client Portal My Assets list."""
    contact, client = _get_contact_and_client(request)
    if not contact:
        return redirect("client_portal:login")

    assets_qs = (
        Asset.undeleted_objects.filter(client=client)
        .select_related("product__product_type", "vendor", "location", "asset_status")
        .order_by("-created_at")
    )

    # Filters
    search_text = (request.GET.get("search_text") or "").strip()
    type_id = request.GET.get("type")
    vendor_id = request.GET.get("vendor")
    location_id = request.GET.get("location")

    if search_text:
        assets_qs = assets_qs.filter(
            Q(tag__icontains=search_text)
            | Q(name__icontains=search_text)
            | Q(serial_no__icontains=search_text)
            | Q(product__name__icontains=search_text)
            | Q(vendor__name__icontains=search_text)
        )
    if type_id:
        assets_qs = assets_qs.filter(product__product_type_id=type_id)
    if vendor_id:
        assets_qs = assets_qs.filter(vendor_id=vendor_id)
    if location_id:
        assets_qs = assets_qs.filter(location_id=location_id)

    # Pagination
    paginator = Paginator(assets_qs, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    # First image per asset
    asset_ids = [a.id for a in page_object]
    asset_images = first_image_map(asset_ids)

    # Stats – one aggregate pass instead of four separate queries
    client_assets = Asset.undeleted_objects.filter(client=client)
    stats = client_assets.aggregate(
        total=Count("id"),
        available=Count("id", filter=Q(is_assigned=False)),
        assigned=Count("id", filter=Q(is_assigned=True)),
        value=Sum("price"),
    )
    total_assets = stats["total"]
    active_count = stats["available"]
    assigned_count = stats["assigned"]
    total_value = stats["value"] or 0

    # Filter dropdown data – only show options related to this client's assets
    client_asset_ids = Asset.undeleted_objects.filter(client=client).values("id")
    product_type_list = (
        ProductType.undeleted_objects.filter(product__asset__id__in=client_asset_ids)
        .distinct()
        .order_by("-created_at")
    )
    vendor_list = (
        Vendor.objects.filter(asset__id__in=client_asset_ids)
        .distinct()
        .order_by("-created_at")
    )
    location_list = (
        Location.undeleted_objects.filter(asset__id__in=client_asset_ids)
        .distinct()
        .order_by("-created_at")
    )

    context = {
        "cp_sidebar": "assets",
        "contact": contact,
        "client": client,
        "page_object": page_object,
        "asset_images": asset_images,
        "product_type_list": product_type_list,
        "vendor_list": vendor_list,
        "location_list": location_list,
        "total_assets": total_assets,
        "active_count": active_count,
        "assigned_count": assigned_count,
        "total_value": total_value,
    }
    return render(request, "client_portal/assets.html", context)


# ─── Support Tickets ──────────────────────────────────────────────


def _client_ticket_base_qs(client):
    """Base queryset of all non-deleted tickets visible to this client.

    Matches the listing's filter: tickets linked to the client directly OR
    to one of the client's assets (since the ticket's own `client` FK is
    nullable).
    """
    return SupportTicket.undeleted_objects.filter(
        Q(client=client) | Q(asset__client=client)
    ).distinct()


def _client_ticket_stats(client):
    """Stat card values for the client portal support tickets page."""
    qs = _client_ticket_base_qs(client)
    now = timezone.now()
    # Single aggregate over the (deduplicated) base queryset — replaces four
    # separate count queries, each of which re-ran the base filter.
    return qs.aggregate(
        total_active=Count("id", distinct=True, filter=~Q(status__in=["3", "4"])),
        pending_parts=Count(
            "id", distinct=True, filter=Q(status="0", ticket_type="hardware_repair")
        ),
        overdue_count=Count(
            "id",
            distinct=True,
            filter=Q(estimated_eta__lt=now) & ~Q(status__in=["3", "4"]),
        ),
        critical_count=Count(
            "id", distinct=True, filter=Q(priority="3") & ~Q(status__in=["3", "4"])
        ),
    )


def client_portal_support_tickets(request):
    """Client Portal Support Tickets list."""
    contact, client = _get_contact_and_client(request)
    if not contact:
        return redirect("client_portal:login")

    tickets_qs = _client_ticket_base_qs(client).order_by("-created_at")

    # Filters
    search = (request.GET.get("search") or "").strip()
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    ticket_type = request.GET.get("ticket_type")

    if search:
        tickets_qs = tickets_qs.filter(
            Q(ticket_id__icontains=search)
            | Q(subject__icontains=search)
            | Q(asset__name__icontains=search)
            | Q(description__icontains=search)
        )
    if status:
        tickets_qs = tickets_qs.filter(status=status)
    if priority:
        tickets_qs = tickets_qs.filter(priority=priority)
    if ticket_type:
        tickets_qs = tickets_qs.filter(ticket_type=ticket_type)

    # Pagination
    paginator = Paginator(tickets_qs, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    # First image per asset for tickets
    asset_ids = [t.asset_id for t in page_object if t.asset_id]
    asset_images = first_image_map(asset_ids)

    context = {
        "cp_sidebar": "support",
        "contact": contact,
        "client": client,
        "page_object": page_object,
        "asset_images": asset_images,
        "status_choices": STATUS_CHOICES,
        "priority_choices": PRIORITY_CHOICES,
        "ticket_type_choices": TICKET_TYPE_CHOICES,
        "all_tickets": tickets_qs,  # For kanban if needed
        **_client_ticket_stats(client),
    }
    return render(request, "client_portal/support_tickets.html", context)


def client_portal_add_ticket(request):
    """Client Portal Create Support Ticket."""
    contact, client = _get_contact_and_client(request)
    if not contact:
        return redirect('client_portal:login')

    form = ClientSupportTicketForm(client=client)

    if request.method == 'POST':
        form = ClientSupportTicketForm(request.POST, request.FILES, client=client)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.organization = client.organization
            ticket.client = client
            ticket.created_by = str(contact.id)
            ticket.save()

            # Handle file uploads
            for f in request.FILES.getlist('attachments'):
                TicketAttachment.objects.create(
                    ticket=ticket, file=f,
                    file_name=f.name, file_size=f.size,
                    # For client portal, we don't have a 'User' object for uploaded_by
                    # We might need to adjust TicketAttachment model if it's strict,
                    # but usually it's null=True.
                )

            # Create initial activity
            TicketActivity.objects.create(
                ticket=ticket, activity_type='created',
                description=f'Ticket initiated by {contact.name} (Client Contact).',
                # performed_by is FK to User, can be null
            )

            messages.success(request, 'Ticket created successfully.')
            return redirect('client_portal:support_tickets')

    context = {
        'cp_sidebar': 'support',
        'contact': contact,
        'client': client,
        'form': form,
        'title': 'New Support Request',
    }
    return render(request, 'client_portal/ticket_add.html', context)


def client_portal_asset_search(request):
    """AJAX asset search limited to the current client."""
    contact, client = _get_contact_and_client(request)
    if not contact:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    query = request.GET.get('q', '').strip()
    if not query:
        assets = Asset.undeleted_objects.filter(client=client).order_by('-created_at')[:10]
    else:
        assets = Asset.undeleted_objects.filter(
            Q(client=client),
            Q(name__icontains=query) | Q(tag__icontains=query) | Q(serial_no__icontains=query)
        )[:10]

    results = []
    for asset in assets:
        results.append({
            'id': str(asset.id),
            'name': asset.name,
            'tag': asset.tag,
        })

    return JsonResponse({'results': results})


def client_portal_export_support_tickets(request):
    """Export the client portal's filtered support tickets as CSV."""
    contact, client = _get_contact_and_client(request)
    if not contact:
        return redirect("client_portal:login")

    tickets_qs = _client_ticket_base_qs(client).select_related(
        "asset", "assigned_to"
    ).order_by("-created_at")

    search = (request.GET.get("search") or "").strip()
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    ticket_type = request.GET.get("ticket_type")

    if search:
        tickets_qs = tickets_qs.filter(
            Q(ticket_id__icontains=search)
            | Q(subject__icontains=search)
            | Q(asset__name__icontains=search)
            | Q(description__icontains=search)
        )
    if status:
        tickets_qs = tickets_qs.filter(status=status)
    if priority:
        tickets_qs = tickets_qs.filter(priority=priority)
    if ticket_type:
        tickets_qs = tickets_qs.filter(ticket_type=ticket_type)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="support_tickets.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Ticket ID",
            "Subject",
            "Asset",
            "Priority",
            "Status",
            "Ticket Type",
            "Assigned To",
            "Created At",
        ]
    )

    for ticket in tickets_qs:
        writer.writerow(
            [
                ticket.ticket_id,
                ticket.subject,
                ticket.asset.name if ticket.asset else "",
                ticket.get_priority_display(),
                ticket.get_status_display(),
                ticket.get_ticket_type_display(),
                (
                    ticket.assigned_to.get_full_name()
                    if ticket.assigned_to
                    else "Unassigned"
                ),
                ticket.created_at,
            ]
        )

    return response


def client_portal_ticket_detail(request, pk):
    """Client Portal Ticket Detail view."""
    contact, client = _get_contact_and_client(request)
    if not contact:
        return redirect('client_portal:login')

    ticket = get_object_or_404(
        SupportTicket.undeleted_objects.select_related('asset', 'assigned_to').filter(
            Q(client=client) | Q(asset__client=client)
        ),
        pk=pk
    )

    if request.method == "POST":
        try:
            comment, created = SupportTicketService.add_client_comment(request, ticket, contact)
            if created:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    from django.template.loader import render_to_string
                    html = render_to_string("support/includes/comment_item.html", {"comment": comment}, request=request)
                    return JsonResponse({"success": True, "html": html, "comment_id": str(comment.id)})
                messages.success(request, "Comment posted successfully.")
                return redirect("client_portal:support_tickets_detail", pk=pk)
        except ValidationError as e:
            err_msg = e.message if hasattr(e, 'message') else ", ".join(e.messages)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": err_msg})
            messages.error(request, err_msg)
            return redirect("client_portal:support_tickets_detail", pk=pk)

    comments = ticket.comments.select_related("author", "contact", "client").prefetch_related("attachments")

    from django.core.paginator import Paginator
    activities_qs = ticket.activities.filter(is_internal=False).order_by('-created_at')
    activities_paginator = Paginator(activities_qs, 10, orphans=1)
    activities_page = activities_paginator.get_page(request.GET.get('activities_page', 1))

    context = {
        'cp_sidebar': 'support',
        'contact': contact,
        'client': client,
        'ticket': ticket,
        'attachments': ticket.attachments.order_by('-created_at'),
        'comments': comments,
        'activities': activities_page,
    }
    return render(request, 'client_portal/ticket_detail.html', context)
