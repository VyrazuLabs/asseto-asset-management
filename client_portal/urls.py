from django.urls import path
from . import views

app_name = 'client_portal'

urlpatterns = [
    # Authentication
    path('login',         views.client_portal_login,          name='login'),
    path('verify-otp',    views.client_portal_verify_otp,     name='verify_otp'),
    path('logout/',       views.client_portal_logout,         name='logout'),

    # Dashboard
    path('',              views.client_portal_dashboard,      name='dashboard'),

    # Assets
    path('assets',        views.client_portal_assets,         name='assets'),

    # Support Tickets
    path('support-tickets', views.client_portal_support_tickets, name='support_tickets'),
    path('support-tickets/add', views.client_portal_add_ticket, name='support_tickets_add'),
    path('support-tickets/asset-search', views.client_portal_asset_search, name='support_tickets_asset_search'),
    path('support-tickets/export', views.client_portal_export_support_tickets, name='support_tickets_export'),
    path('support-tickets/<uuid:pk>', views.client_portal_ticket_detail, name='support_tickets_detail'),
]
