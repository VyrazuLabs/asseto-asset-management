from django.urls import path
from django.views.generic import TemplateView
from . import views
from . import api_views
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

audit_api_url_patterns = [
    #api urls
    path('api/audit/list/completed/',api_views.CompletedAuditList.as_view(),name="complete_audit_list"),
    path('api/audit/list/pending/',api_views.PendingAuditList.as_view(),name='pending_audit_list'),
    path('api/audit/add',api_views.AddAudit.as_view(),name="add_audit"),
    path('api/audit/<str:id>',api_views.GetAuditById.as_view(),name='get_audit_by_id'),
    path('api/audit/details/<str:id>',api_views.GetAuditDetails.as_view(),name='audit_details'),
    # path('api/asset/delete/<uuid:id>',api_views.DeleteAsset.as_view(),name="delete_asset"),
    # path('api/asset/search/',api_views.SearchAsset.as_view(),name='search_asset'),
    # path('api/asset/scan-barcode/<str:tag_id>',api_views.Scan_api_barcode.as_view(), name='scan_barcode'),
]