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
                messages.success(request, "Client registered successfully.")
                return redirect("clients:list")
            except Exception as e:
                logger.exception("Error creating client")
                messages.error(request, "Failed to create client. Please try again.")
    else:
        form = ClientForm(organization=request.user.organization)
    from roles.models import Role

    roles = Role.objects.filter(organization=request.user.organization).order_by("name")
    context = {
        "sidebar": "clients",
        "title": "Register Client",
        "form": form,
        "roles": roles,
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
                messages.success(request, "Client updated successfully.")
                return redirect("clients:list")
            except Exception as e:
                logger.exception("Error updating client")
                messages.error(request, "Failed to update client. Please try again.")
    else:
        form = ClientForm(instance=client, organization=request.user.organization)
    from roles.models import Role

    roles = Role.objects.filter(organization=request.user.organization).order_by(
        "related_name"
    )
    context = {
        "sidebar": "clients",
        "title": f"Edit {client.name}",
        "form": form,
        "client": client,
        "roles": roles,
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
