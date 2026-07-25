from django.urls import path
from . import views

app_name = "support"

urlpatterns = [
    # New Ticket URLs
    path("tickets", views.ticket_list, name="ticket_list"),
    path("tickets/add", views.add_ticket, name="ticket_add"),
    path("tickets/details/<uuid:id>", views.ticket_detail, name="ticket_detail"),
    path("tickets/update/<uuid:id>", views.update_ticket, name="ticket_update"),
    path("tickets/delete/<uuid:id>", views.delete_ticket, name="ticket_delete"),
    path("tickets/search/<str:page>", views.search_tickets, name="ticket_search"),
    path("tickets/export", views.export_tickets, name="ticket_export"),
    path(
        "tickets/attachment/delete/<uuid:id>",
        views.delete_ticket_attachment,
        name="ticket_attachment_delete",
    ),
    path("asset-search/", views.asset_search, name="asset_search"),
    path("technician-search/", views.technician_search, name="technician_search"),
    path("tickets/<uuid:id>/update-status/", views.update_ticket_status, name="ticket_update_status"),
]
