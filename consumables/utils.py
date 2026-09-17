from django.core.paginator import Paginator
from django.db.models import Q, Sum
from .models import Consumable
from django.shortcuts import get_object_or_404

PAGE_SIZE = 10
ORPHANS = 1


def notify_low_stock(consumable, actor, remaining):
    """
    Send a low-stock notification for a consumable, if it has dropped to or
    below its configured minimum quantity.

    Args:
        consumable: Consumable instance to check and notify about.
        actor: User the notification is sent as/to (the acting user).
        remaining: Current quantity to compare against consumable.min_qty.

    Returns:
        None.
    """
    if consumable.min_qty is None or remaining is None or remaining > consumable.min_qty:
        return

    from notifications.service import NotificationService

    consumable_name = consumable.consumable_name or "Consumable"
    notif_message = (
        f"{consumable_name} is below or almost below the minimum quantity "
        f"required (Min: {consumable.min_qty}, Current: {remaining})."
    )
    try:
        NotificationService.send(
            user=actor,
            title="Low Stock Alert",
            message=notif_message,
            icon="bi-exclamation-triangle",
            link=f"/consumables/detail/{consumable.pk}",
            object_id=str(consumable.pk),
            instance_id="consumable",
        )
    except Exception:
        pass


def consumable_list_util(request):
    """
    Build the context for the consumables list page: paginated, org-scoped
    consumables plus summary stats (totals, low-stock count) and filter data.

    Args:
        request: The current HttpRequest (used for org scoping and the
            "page" query param).

    Returns:
        dict: Template context for consumables/list.html.
    """
    qs = Consumable.undeleted_objects.filter(
        organization=request.user.organization
    ).select_related("product", "vendor", "location").order_by("-created_at")

    total_count = qs.count()
    low_stock_count = sum(1 for c in qs if c.is_low_stock())
    
    agg = qs.aggregate(
        total_quantity=Sum("quantity"),
        total_purchase_cost=Sum("purchase_cost"),
    )
    total_quantity = agg["total_quantity"] or 0
    total_purchase_cost = agg["total_purchase_cost"] or 0

    paginator = Paginator(qs, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.filter(organization=request.user.organization, is_active=True)

    deleted_count = Consumable.deleted_objects.filter(
        organization=request.user.organization
    ).count()

    context = {
        "page_object": page_object,
        "total_count": total_count,
        "low_stock_count": low_stock_count,
        "total_quantity": total_quantity,
        "total_purchase_cost": total_purchase_cost,
        "deleted_count": deleted_count,
        "users": users,
        "title": "Consumables",
        "sidebar": "consumables",
    }
    return context


def search_utils(request, page):
    """
    Search org-scoped consumables by name, product, vendor, location, item
    no. or order number, and paginate the results.

    Args:
        request: The current HttpRequest (used for org scoping and the
            "search_text" query param).
        page: Page number to return from the paginator.

    Returns:
        tuple[Page, int]: (paginated consumables, count of soft-deleted
        consumables for the organization).
    """
    search_text = (request.GET.get("search_text") or "").strip()
    filters = Q(organization=request.user.organization)

    if search_text:
        filters &= (
            Q(consumable_name__icontains=search_text)
            | Q(product__name__icontains=search_text)
            | Q(vendor__name__icontains=search_text)
            | Q(location__office_name__icontains=search_text)
            | Q(item_no__icontains=search_text)
            | Q(order_number__icontains=search_text)
        )

    qs = Consumable.undeleted_objects.filter(filters).select_related(
        "product", "vendor", "location"
    ).order_by("-created_at")

    paginator = Paginator(qs, PAGE_SIZE, orphans=ORPHANS)
    page_object = paginator.get_page(page)
    deleted_count = Consumable.deleted_objects.filter(
        organization=request.user.organization
    ).count()
    return page_object, deleted_count


def get_consumable_details(request, pk):
    """
    Build the context for the consumable detail page: the consumable itself,
    its paginated audit history, and its paginated checkout history.

    Args:
        request: The current HttpRequest (used for org scoping and the
            "page"/"checkout_page" query params).
        pk: Primary key of the Consumable to look up.

    Returns:
        dict: Template context for consumables/detail.html.

    Raises:
        Http404: If no undeleted consumable with this pk exists for the
            requesting user's organization.
    """
    consumable = get_object_or_404(
        Consumable.undeleted_objects,
        pk=pk,
        organization=request.user.organization,
    )
    history_list = consumable.history.all()
    paginator = Paginator(history_list, 10, orphans=1)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    from .models import ConsumableCheckout
    checkout_list = consumable.checkouts.select_related("user").order_by("-created_at")
    purchase_cost = consumable.purchase_cost or 0
    for co in checkout_list:
        co.total_amount = co.quantity * purchase_cost
    checkout_paginator = Paginator(checkout_list, 10, orphans=1)
    checkout_page_number = request.GET.get("checkout_page")
    checkout_page_object = checkout_paginator.get_page(checkout_page_number)

    context = {
        "consumable": consumable,
        "page_object": page_object,
        "checkout_page_object": checkout_page_object,
        "documents": consumable.documents.all(),
        "title": f"Consumable - {consumable}",
        "sidebar": "consumables",
    }
    return context
