from django.urls import path
from . import views
from . import api_views

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

# Mobile / JSON API URLs
support_api_url_patterns = [
    path("api/support/tickets/", api_views.TicketListAPIView.as_view(), name="api_ticket_list"),
    path("api/support/tickets/add/", api_views.TicketCreateAPIView.as_view(), name="api_ticket_add"),
    path("api/support/tickets/<uuid:id>/", api_views.TicketDetailAPIView.as_view(), name="api_ticket_detail"),
    path("api/support/tickets/<uuid:id>/update/", api_views.TicketUpdateAPIView.as_view(), name="api_ticket_update"),
    path(
        "api/support/tickets/<uuid:id>/update-status/",
        api_views.TicketStatusUpdateAPIView.as_view(),
        name="api_ticket_update_status",
    ),
    path("api/support/tickets/<uuid:id>/comments/", api_views.TicketCommentAPIView.as_view(), name="api_ticket_comments"),
    path(
        "api/support/attachments/<uuid:id>/delete/",
        api_views.TicketAttachmentDeleteAPIView.as_view(),
        name="api_ticket_attachment_delete",
    ),
    path("api/support/asset-search/", api_views.AssetSearchAPIView.as_view(), name="api_asset_search"),
    path("api/support/technician-search/", api_views.TechnicianSearchAPIView.as_view(), name="api_technician_search"),
]
