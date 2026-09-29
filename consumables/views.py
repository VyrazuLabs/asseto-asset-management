from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.decorators import user_passes_test
from .models import Consumable, ConsumableDocument, ConsumableUnit
from .forms import ConsumableForm
from .utils import (
    bulk_assign_serials,
    checkout_serialized_units,
    consumable_list_util,
    get_consumable_details,
    notify_low_stock,
    retire_unit,
    search_utils,
    set_unit_serial,
)


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
            consumable.apply_serialized_quantity()

            for f in request.FILES.getlist("documents"):
                ConsumableDocument.objects.create(
                    consumable=consumable,
                    file=f,
                    file_name=f.name,
                    file_size=f.size,
                    uploaded_by=request.user,
                )

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

            delete_doc_ids = request.POST.getlist("delete_documents")
            if delete_doc_ids:
                for doc in consumable.documents.filter(id__in=delete_doc_ids):
                    doc.file.delete(save=False)
                    doc.delete()

            for f in request.FILES.getlist("documents"):
                ConsumableDocument.objects.create(
                    consumable=consumable,
                    file=f,
                    file_name=f.name,
                    file_size=f.size,
                    uploaded_by=request.user,
                )

            if consumable.is_serialized:
                consumable.apply_serialized_quantity()
            else:
                from django.db.models import Sum
                total_checked_out = consumable.checkouts.aggregate(
                    total=Sum("quantity")
                )["total"] or 0

                new_qty = consumable.quantity or 0
                consumable.remaining_quantity = max(0, new_qty - total_checked_out)
                consumable.save(update_fields=["remaining_quantity"])

            qty = consumable.remaining_quantity
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
        is_serialized = get_object_or_404(
            Consumable.undeleted_objects, pk=pk, organization=request.user.organization
        ).is_serialized
        if is_serialized:
            return _checkout_serialized(request, pk)

        user_id = request.POST.get("user")
        try:
            checkout_qty = int(request.POST.get("quantity", 0))
        except (ValueError, TypeError):
            checkout_qty = 0

        notes = request.POST.get("notes", "").strip()

        if checkout_qty <= 0:
            messages.error(request, "Please enter a valid quantity to checkout.")
            return _after_checkout(request, pk)

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
                return _after_checkout(request, pk)

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

    return _after_checkout(request, pk)


def _checkout_serialized(request, pk):
    """Check out the units picked in the modal; the consumable is row-locked for the whole pick."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    with transaction.atomic():
        consumable = get_object_or_404(
            Consumable.undeleted_objects.select_for_update(),
            pk=pk,
            organization=request.user.organization,
        )
        target_user = get_object_or_404(
            User, pk=request.POST.get("user"), organization=request.user.organization
        )
        try:
            checkout = checkout_serialized_units(
                consumable,
                request.POST.getlist("units"),
                target_user,
                request.POST.get("notes", "").strip(),
                request.user.get_full_name() or request.user.username or request.user.email or f"User #{request.user.pk}",
            )
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
            return _after_checkout(request, pk)

    notify_low_stock(consumable, request.user, consumable.remaining_quantity)
    messages.success(request, f"Successfully checked out {checkout.quantity} unit(s) to {target_user}.")
    return _after_checkout(request, pk)


@login_required
@permission_required("consumables.edit_consumable")
def available_units(request, pk):
    """Return the in-stock units of a serialized consumable as JSON for the checkout modal."""
    consumable = get_object_or_404(
        Consumable.undeleted_objects, pk=pk, organization=request.user.organization
    )
    units = consumable.units.filter(status=ConsumableUnit.STATUS_IN_STOCK).select_related("consumable")
    return JsonResponse(
        {"units": [{"id": str(u.pk), "sub_id": u.sub_id, "serial_no": u.serial_no or ""} for u in units]}
    )


@login_required
@permission_required("consumables.edit_consumable")
def update_unit(request, unit_pk):
    """Update one unit: set its serial, or mark it lost/disposed."""
    unit = get_object_or_404(
        ConsumableUnit.objects.select_related("consumable"),
        pk=unit_pk,
        consumable__organization=request.user.organization,
        consumable__is_deleted=False,
    )
    if request.method == "POST":
        try:
            if "retire" in request.POST:
                retire_unit(unit, request.POST["retire"])
                notify_low_stock(unit.consumable, request.user, unit.consumable.remaining_quantity)
                messages.success(request, f"{unit.sub_id} updated.")
            else:
                set_unit_serial(unit, request.POST.get("serial_no"))
                messages.success(request, f"{unit.sub_id} serial saved.")
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
    return redirect("consumables:detail", pk=unit.consumable_id)


@login_required
@permission_required("consumables.edit_consumable")
def bulk_serials(request, pk):
    """Tag untagged units in sequence order from pasted serials (one per line)."""
    consumable = get_object_or_404(
        Consumable.undeleted_objects, pk=pk, organization=request.user.organization, is_serialized=True
    )
    if request.method == "POST":
        try:
            tagged = bulk_assign_serials(consumable, request.POST.get("serials", ""))
            messages.success(request, f"Tagged {tagged} unit(s).")
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
    return redirect("consumables:detail", pk=consumable.pk)


def _after_checkout(request, pk):
    """Send the user back to the page the checkout modal was opened from."""
    if request.POST.get("return_to") == "detail":
        return redirect("consumables:detail", pk=pk)
    return redirect("consumables:list")
