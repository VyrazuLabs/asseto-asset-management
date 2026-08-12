# views.py
"""Thin view functions for the ``clients`` app.
All business logic is delegated to ``ClientService`` to satisfy SOLID
and DRY principles. Only request handling, messaging and rendering are
performed here.
"""

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .utils import ClientService

# Configure logger for this module
logger = logging.getLogger(__name__)

PAGE_SIZE = 10
ORPHANS = 1


@login_required
def client_list(request):
    """Display paginated list of clients with optional search/filter."""
    try:
        context = ClientService.list(request)
    except Exception as e:
        logger.exception("Error in client_list view")
        messages.error(
            request, "An unexpected error occurred while loading the client list."
        )
        return redirect("clients:list")
    return render(request, "clients/list.html", context)


@login_required
def add_client(request):
    """Create a new client and its contacts."""
    if request.method == "POST":
        form = ClientForm(request.POST, organization=request.user.organization)
        if form.is_valid():
            request.form = form
            try:
                client = ClientService.create(request)
                from custom_fields.utils import save_values_for_entity
                save_values_for_entity(request, client.id, "client")
                messages.success(request, "Client registered successfully.")
                return redirect("clients:list")
            except ValueError as e:
                logger.warning(f"Validation error creating client: {e}")
                messages.error(request, str(e))
            except Exception as e:
                logger.exception("Error creating client")
                messages.error(request, f"Failed to create client: {type(e).__name__}: {e}")
    else:
        form = ClientForm(organization=request.user.organization)
    from roles.models import Role

    roles = Role.objects.filter(organization=request.user.organization).order_by("name")
    from custom_fields.utils import get_definitions_for_module
    cf_definitions = get_definitions_for_module(request.user.organization, "client")

    context = {
        "sidebar": "clients",
        "title": "Register Client",
        "form": form,
        "roles": roles,
        "cf_definitions": cf_definitions,
    }
    return render(request, "clients/add.html", context)


@login_required
def update_client(request, id):
    """Update an existing client and its contacts."""
    client = get_object_or_404(ClientService.base_queryset(request.user), pk=id)
    if request.method == "POST":
        form = ClientForm(
            request.POST, instance=client, organization=request.user.organization
        )
        if form.is_valid():
            request.form = form
            try:
                ClientService.update(request, client_id=id)
                from custom_fields.utils import save_values_for_entity
                save_values_for_entity(request, id, "client")
                messages.success(request, "Client updated successfully.")
                return redirect("clients:list")
            except ValueError as e:
                logger.warning(f"Validation error updating client: {e}")
                messages.error(request, str(e))
            except Exception as e:
                logger.exception("Error updating client")
                messages.error(request, f"Failed to update client: {type(e).__name__}: {e}")
    else:
        form = ClientForm(instance=client, organization=request.user.organization)
    from roles.models import Role

    roles = Role.objects.filter(organization=request.user.organization).order_by(
        "related_name"
    )
    from custom_fields.utils import get_definitions_for_module, get_values_for_entity
    cf_definitions = get_definitions_for_module(request.user.organization, "client")
    cf_values = get_values_for_entity(client.id, cf_definitions)

    context = {
        "sidebar": "clients",
        "title": f"Edit {client.name}",
        "form": form,
        "client": client,
        "roles": roles,
        "cf_definitions": cf_definitions,
        "cf_values": cf_values,
    }
    return render(request, "clients/edit.html", context)


@login_required
def client_detail(request, id):
    try:
        context = ClientService.get_detail_context(request, id)
    except Exception as e:
        logger.exception("Error fetching client detail")
        messages.error(request, "Unable to load client details.")
        return redirect("clients:list")
    return render(request, "clients/detail.html", context)


@login_required
def delete_client(request, id):
    """Soft delete a client and redirect to the list view."""
    if request.method == "POST":
        try:
            ClientService.delete(request, client_id=id)
            messages.success(request, "Client deleted successfully.")
        except Exception as e:
            logger.exception("Error deleting client")
            messages.error(request, "Failed to delete client.")
    return redirect("clients:list")


@login_required
def toggle_status(request, id):
    """Toggle client active/inactive status via POST."""
    if request.method == "POST" and request.user.is_superuser:
        try:
            ClientService.toggle_status(request, client_id=id)
        except Exception as e:
            logger.exception("Error toggling client status")
            messages.error(request, "Failed to toggle client status.")
            return HttpResponse(status=500)
    return HttpResponse(status=204)


@login_required
def search_clients(request, page):
    """AJAX endpoint returning a paginated client table."""
    try:
        context = ClientService.search(request, page)
    except Exception as e:
        logger.exception("Error searching clients")
        return HttpResponse(status=500)
    return render(request, "clients/clients-data.html", context)


@login_required
def export_clients_csv(request):
    try:
        return ClientService.export_csv(request)
    except Exception as e:
        logger.exception("Error exporting CSV")
        messages.error(request, "Failed to export CSV.")
        return redirect("clients:list")


@login_required
def export_clients_pdf(request):
    try:
        return ClientService.export_pdf(request)
    except Exception as e:
        logger.exception("Error exporting PDF")
        messages.error(request, "Failed to export PDF.")
        return redirect("clients:list")


@login_required
def add_client_location(request, id):
    """Add a new location for a client."""
    from dashboard.models import Location
    from dashboard.forms import LocationForm, AddressForm
    from .models import Client

    client = get_object_or_404(
        Client.undeleted_objects, pk=id, organization=request.user.organization
    )
    address_form = AddressForm(request.POST or None)
    location_form = LocationForm(request.POST or None)

    if request.method == "POST":
        if address_form.is_valid() and location_form.is_valid():
            address = address_form.save()
            location = location_form.save(commit=False)
            location.address = address
            location.organization = request.user.organization
            location.client = client
            location.save()
            messages.success(request, "Location added successfully")
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "clientLocationAdded"
            return response

    context = {
        "address_form": address_form,
        "location_form": location_form,
        "client": client,
    }
    return render(
        request, "dashboard/locations/add-location-modal.html", context=context
    )


@login_required
def update_client_location(request, id):
    """Update an existing client location."""
    from dashboard.models import Location, Address
    from dashboard.forms import LocationForm, AddressForm

    location = get_object_or_404(
        Location.undeleted_objects, pk=id, organization=request.user.organization
    )
    address = get_object_or_404(Address, pk=location.address.id)

    location_form = LocationForm(request.POST or None, instance=location)
    address_form = AddressForm(request.POST or None, instance=address)

    if request.method == "POST":
        if location_form.is_valid() and address_form.is_valid():
            location_form.save()
            address_form.save()
            messages.success(request, "Location updated successfully")
            if request.htmx:
                return HttpResponse(status=200, headers={"HX-Refresh": "true"})
            if location.client:
                return redirect("clients:details", id=location.client.id)
            return redirect("clients:list")

    context = {
        "sidebar": "clients",
        "location_form": location_form,
        "address_form": address_form,
        "location": location,
        "title": f"Update-{location.office_name}",
    }

    if request.headers.get("HX-Request", "false").lower() == "true":
        return render(
            request, "dashboard/locations/edit-location-modal.html", context=context
        )

    return redirect("clients:list")


@login_required
def delete_client_location(request, id):
    """Delete a client location (soft delete)."""
    from dashboard.models import Location
    from assets.models import AssignAsset

    if request.method == "POST":
        location = get_object_or_404(
            Location.undeleted_objects, pk=id, organization=request.user.organization
        )
        client_id = location.client.id if location.client else None

        # Check if the deleted location is assigned to any asset
        assigned_assets = AssignAsset.objects.filter(asset__location=location).first()
        if assigned_assets is not None:
            messages.error(
                request,
                "Location cannot be deleted as it is assigned to an asset. Please unassign the asset before deleting the location.",
            )
            if client_id:
                return redirect("clients:details", id=client_id)
            return redirect("clients:list")

        location.status = False
        location.soft_delete()
        history_id = location.history.first().history_id
        location.history.filter(pk=history_id).update(history_type="-")
        messages.success(request, "Location deleted successfully")
        if client_id:
            return redirect("clients:details", id=client_id)
    return redirect("clients:list")
