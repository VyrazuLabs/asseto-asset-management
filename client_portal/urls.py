from django.urls import path
from . import views

app_name = "client_portal"

urlpatterns = [
    # Authentication
    path("login", views.client_portal_login, name="login"),
    path("verify-otp", views.client_portal_verify_otp, name="verify_otp"),
    path("logout/", views.client_portal_logout, name="logout"),
    # Dashboard
    path("", views.client_portal_dashboard, name="dashboard"),
    # Assets
    path("assets", views.client_portal_assets, name="assets"),
    # Support Tickets
    path(
        "support-tickets", views.client_portal_support_tickets, name="support_tickets"
    ),
    path(
        "support-tickets/export",
        views.client_portal_export_support_tickets,
        name="support_tickets_export",
    ),
]
