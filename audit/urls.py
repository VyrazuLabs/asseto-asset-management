from django.urls import path
from django.views.generic import TemplateView
from . import views
app_name = 'audit'

urlpatterns = [ 
    path('add-audit/',views.add_audit, name='add_audit'),
    path('audit-list/',views.audit_list, name='audit_list'),
    path('get-audits-by-id/<str:id>/',views.get_audits_by_id, name='get_audits_by_id'),
    path('pending-audits/',views.pending_audits, name='pending_audits'),
    # path('upcoming-audits/',views.upcoming_audits, name='upcoming_audits'),
    path('completed-audits/',views.completed_audits, name='completed_audits'),
    path('get-assigned-user/<str:tag>/',views.get_assigned_user, name='get_assigned_users'),
    path('details/<str:id>/',views.audit_details, name='details'),
]