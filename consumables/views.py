from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.decorators import user_passes_test
from .models import Consumable
from .forms import ConsumableForm
from .utils import consumable_list_util, search_utils, get_consumable_details, notify_low_stock


def manage_access(user):
    """Return True if the user holds any consumables permission."""
    perms = [
        "consumables.view_consumable",
        "consumables.add_consumable",
        "consumables.edit_consumable",
        "consumables.delete_consumable",
    ]
    return any(user.has_perm(p) for p in perms)


@login_required
@user_passes_test(manage_access)
def consumable_list(request):
    """Render the paginated consumables list page for the user's organization."""
    context = consumable_list_util(request)
    return render(request, "consumables/list.html", context)


@login_required
@permission_required("consumables.add_consumable")
def add_consumable(request):
    """Create a new consumable for the user's organization, notifying on low stock."""
    form = ConsumableForm(organization=request.user.organization)
    if request.method == "POST":
        form = ConsumableForm(request.POST, request.FILES, organization=request.user.organization)
        if form.is_valid():
            consumable = form.save(commit=False)
            consumable.organization = request.user.organization
            consumable.save()

            notify_low_stock(consumable, request.user, consumable.quantity)

            messages.success(request, "Consumable added successfully.")
            return redirect("consumables:list")
    context = {"form": form, "title": "Add Consumable"}
    return render(request, "consumables/add.html", context)


@login_required
@permission_required("consumables.view_consumable")
def detail_consumable(request, pk):
    """Render the consumable detail page, including history and checkouts."""
    context = get_consumable_details(request, pk)
    return render(request, "consumables/detail.html", context)


@login_required
@permission_required("consumables.edit_consumable")
def edit_consumable(request, pk):
    """Update a consumable belonging to the user's organization, notifying on low stock."""
    consumable = get_object_or_404(
        Consumable.undeleted_objects, pk=pk, organization=request.user.organization
    )
    form = ConsumableForm(instance=consumable, organization=request.user.organization)
    if request.method == "POST":
        form = ConsumableForm(
            request.POST, request.FILES, instance=consumable,
            organization=request.user.organization
        )
        if form.is_valid():
            consumable = form.save()

            if request.POST.get("remove_image"):
                if consumable.image:
                    consumable.image.delete(save=False)
                consumable.image = None
                consumable.save()

            qty = consumable.remaining_quantity if consumable.remaining_quantity is not None else consumable.quantity
            notify_low_stock(consumable, request.user, qty)

            messages.success(request, "Consumable updated successfully.")
            return redirect("consumables:detail", pk=consumable.pk)
    context = {"form": form, "consumable": consumable, "title": f"Edit - {consumable}"}
    return render(request, "consumables/edit.html", context)


@login_required
@permission_required("consumables.delete_consumable")
def delete_consumable(request, pk):
    """Soft-delete a consumable belonging to the user's organization."""
    if request.method == "POST":
        consumable = get_object_or_404(
            Consumable.undeleted_objects, pk=pk, organization=request.user.organization
        )
        consumable.soft_delete()
        history_id = consumable.history.first().history_id
        consumable.history.filter(pk=history_id).update(history_type="-")
        messages.success(request, "Consumable deleted successfully.")
    return redirect("consumables:list")


@login_required
def search(request, page):
    """Render the consumables table rows matching a search query (used by htmx)."""
    page_object, deleted_count = search_utils(request, page)
    return render(
        request,
        "consumables/consumables-data.html",
        {"page_object": page_object, "deleted_count": deleted_count},
    )


@login_required
@permission_required("consumables.edit_consumable")
def checkout_consumable(request, pk):
    """
    Check out a quantity of a consumable to a user, decrementing its
    remaining stock and notifying on low stock.

    Locks the consumable row for the duration of the read-check-write on
    remaining_quantity so concurrent checkouts cannot oversell stock.
    """
    if request.method == "POST":
        user_id = request.POST.get("user")
        try:
            checkout_qty = int(request.POST.get("quantity", 0))
        except (ValueError, TypeError):
            checkout_qty = 0

        notes = request.POST.get("notes", "").strip()

        if checkout_qty <= 0:
            messages.error(request, "Please enter a valid quantity to checkout.")
            return redirect("consumables:list")

        from django.contrib.auth import get_user_model
        from .models import ConsumableCheckout
        User = get_user_model()

        with transaction.atomic():
            consumable = get_object_or_404(
                Consumable.undeleted_objects.select_for_update(),
                pk=pk,
                organization=request.user.organization,
            )

            if consumable.remaining_quantity is not None and checkout_qty > consumable.remaining_quantity:
                messages.error(request, f"Cannot checkout more than remaining quantity ({consumable.remaining_quantity}).")
                return redirect("consumables:list")

            target_user = get_object_or_404(User, pk=user_id, organization=request.user.organization)

            ConsumableCheckout.objects.create(
                consumable=consumable,
                user=target_user,
                quantity=checkout_qty,
                notes=notes,
                created_by=request.user.get_full_name() or request.user.username or request.user.email or f"User #{request.user.pk}",
            )
            current_rem = consumable.remaining_quantity if consumable.remaining_quantity is not None else (consumable.quantity or 0)
            consumable.remaining_quantity = max(0, current_rem - checkout_qty)
            consumable.save()

        notify_low_stock(consumable, request.user, consumable.remaining_quantity)
        messages.success(request, f"Successfully checked out {checkout_qty} item(s) to {target_user}.")

    return redirect("consumables:list")
