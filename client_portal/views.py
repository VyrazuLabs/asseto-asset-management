import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import HttpResponse, JsonResponse

from clients.models import Client, ClientContact
from assets.models import Asset, AssetImage, AssignAsset
from support.models import (
    SupportTicket,
    TicketAttachment,
    TicketActivity,
    STATUS_CHOICES,
    PRIORITY_CHOICES,
    TICKET_TYPE_CHOICES,
)
from .forms import ClientSupportTicketForm
from assets.models import AssetStatus
from dashboard.models import ProductCategory, ProductType, Location
from vendors.models import Vendor
from .utils import create_otp_for_contact, verify_otp_for_contact

# ─── Helper ──────────────────────────────────────────────────────────


def _get_contact_and_client(request):
    """Fetch the authenticated ClientContact and their Client from session."""
    contact_id = request.session.get("client_contact_id")
    if not contact_id:
        return None, None
    try:
        contact = ClientContact.objects.select_related("client").get(id=contact_id)
        return contact, contact.client
    except ClientContact.DoesNotExist:
        return None, None


# ─── Authentication Views ────────────────────────────────────────────


def client_portal_login(request):
    """Step 1: Client enters email → OTP is sent."""
    # If already logged in, go to dashboard
    if request.session.get("client_contact_id"):
        return redirect("client_portal:dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()

        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, "client_portal/login.html")

        # Find contact with portal access
        contact = (
            ClientContact.objects.filter(
                email__iexact=email,
                is_portal_active=True,
                is_deleted=False,
            )
            .select_related("client")
            .first()
        )

        if not contact:
            # Security note: In some cases, we might not want to reveal if an email exists,
            # but for a portal like this, a clear error helps legitimate users.
            messages.error(
                request,
                "No portal access found for this email. Please contact your administrator.",
            )
            return render(request, "client_portal/login.html", {"email": email})

        # Generate & send OTP
        try:
            create_otp_for_contact(contact)
        except Exception as e:
            # Log the error path here in a real app
            messages.error(
                request, "Failed to send verification code. Please try again later."
            )
            return render(request, "client_portal/login.html", {"email": email})

        # Store pending contact in session
        request.session["pending_contact_id"] = str(contact.id)
        request.session["pending_contact_email"] = email
        messages.success(request, f"A verification code has been sent to {email}")
        return redirect("client_portal:verify_otp")

    return render(request, "client_portal/login.html")


def client_portal_verify_otp(request):
    """Step 2: Client enters the OTP received via email."""
    pending_id = request.session.get("pending_contact_id")
    pending_email = request.session.get("pending_contact_email", "")

    if not pending_id:
        return redirect("client_portal:login")

    contact = get_object_or_404(ClientContact, id=pending_id)

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        if not entered_otp:
            messages.error(request, "Please enter the verification code.")
            return render(
                request, "client_portal/verify-otp.html", {"email": pending_email}
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

    return render(request, "client_portal/verify-otp.html", {"email": pending_email})


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


# ─── Dashboard (Overview) ───────────────────────────────────────────


def client_portal_dashboard(request):
    """Client Portal Dashboard Overview."""
    contact, client = _get_contact_and_client(request)
    if not contact:
        return redirect("client_portal:login")

    show_welcome = request.session.pop("show_welcome_banner", False)

    client_assets = Asset.undeleted_objects.filter(client=client)
    total_assets = client_assets.count()
    total_value = client_assets.aggregate(total=Sum("price"))["total"] or 0

    tickets_qs = _client_ticket_base_qs(client)
    open_tickets = tickets_qs.exclude(status__in=["3", "4"]).count()

    # Recent support activity (latest 5 tickets for the client)
    recent_tickets = list(
        tickets_qs.select_related("asset", "assigned_to").order_by("-created_at")[:5]
    )
    recent_asset_ids = [t.asset_id for t in recent_tickets if t.asset_id]
    recent_asset_images = {}
    if recent_asset_ids:
        for img in AssetImage.objects.filter(asset_id__in=recent_asset_ids).order_by(
            "-uploaded_at"
        ):
            if img.asset_id not in recent_asset_images:
                recent_asset_images[img.asset_id] = img

    # Product distribution (matches the "Product Category" field in the add form)
    cat_data = {}
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
    for asset in client_assets.select_related("product").iterator():
        cat_name = asset.product.name if asset.product else "Uncategorized"
        if cat_name not in cat_data:
            cat_data[cat_name] = 0
        cat_data[cat_name] += 1

    cat_labels = list(cat_data.keys())
    cat_values = list(cat_data.values())
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

    assets_qs = Asset.undeleted_objects.filter(client=client).order_by("-created_at")

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
    images_qs = AssetImage.objects.filter(asset_id__in=asset_ids).order_by(
        "-uploaded_at"
    )
    asset_images = {}
    for img in images_qs:
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img

    # Stats
    client_assets = Asset.undeleted_objects.filter(client=client)
    total_assets = client_assets.count()
    active_count = client_assets.filter(is_assigned=False).count()
    assigned_count = client_assets.filter(is_assigned=True).count()
    total_value = client_assets.aggregate(total=Sum("price"))["total"] or 0

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
    return {
        "total_active": qs.exclude(status__in=["3", "4"]).count(),
        "pending_parts": qs.filter(status="0", ticket_type="hardware_repair").count(),
        "overdue_count": qs.filter(estimated_eta__lt=timezone.now())
        .exclude(status__in=["3", "4"])
        .count(),
        "critical_count": qs.filter(priority="3")
        .exclude(status__in=["3", "4"])
        .count(),
    }


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
    images_qs = AssetImage.objects.filter(asset_id__in=asset_ids).order_by(
        "-uploaded_at"
    )
    asset_images = {}
    for img in images_qs:
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img

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
            ticket.created_by_contact = contact
            ticket.created_by = f"Client Contact: {contact.name}"
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

    tickets_qs = _client_ticket_base_qs(client).order_by("-created_at")

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

    context = {
        'cp_sidebar': 'support',
        'contact': contact,
        'client': client,
        'ticket': ticket,
        'attachments': ticket.attachments.order_by('-created_at'),
        'activities': ticket.activities.filter(is_internal=False).order_by('-created_at'),
    }
    return render(request, 'client_portal/ticket_detail.html', context)
