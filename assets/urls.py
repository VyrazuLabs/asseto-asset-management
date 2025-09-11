from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('list', views.listed, name='list'),
    path('details/<uuid:id>', views.details, name='details'),
    path('update/<uuid:id>', views.update, name='update'),
    path('delete/<uuid:id>', views.delete, name='delete'),
    path('status/<uuid:id>', views.status, name='status'),
    path('add', views.add, name='add'),
    path('search/<str:page>', views.search, name='search'),
    path('assigned-list', views.assigned_list, name='assigned_list'),
    path('unassigned-list', views.unassigned_list, name='unassigned_list'),
    path('assign-asset', views.assign_asset, name='assign_asset'),
    path('reassign-asset/<uuid:id>', views.reassign_asset, name='reassign_asset'),
    path('delete-assign/<uuid:id>', views.delete_assign, name='delete_assign'),
    path('delete-assign-asset-list/<uuid:id>', views.delete_assign_asset_list, name='delete_assign_asset_list'),
    path('assign_asset_search/<str:page>', views.assign_asset_search, name='assign_asset_search'),
    path('change-status/<str:id>/',views.change_status,name='change_status'),
    path('status-repair-to-release/<str:id>/',views.release_asset,name='release'),
    path('status-ready-to-assign/<str:id>/',views.assign_assets,name='assigned'),
    path('update-assets-details/<str:id>/',views.update_in_detail,name='update_in_detail'),
    path('piechart_status_data/', views.pie_chart_assigned_status, name='piechart_status_data'),
    path('assets_by_status', views.pie_chart_status, name='pie_chart_status'),
    path('add_status',views.add_asset_status,name='add_asset_status'),
    path('asset_status_list',views.asset_status_list,name='asset_status_list'),
    path('asset_status_details/<uuid:id>',views.asset_status_details,name='asset_status_details'),
    path('edit_asset_status/<uuid:id>',views.edit_asset_status,name='edit_asset_status'),
    path('asset_status_search/<str:page>',views.asset_status_search,name='asset_status_search'),
    path('delete_asset_status/<uuid:id>',views.delete_asset_status,name='delete_asset_status'),
    path('assign-asset-in-asset-list/<uuid:id>', views.assign_asset_in_asset_list, name='assign_asset_in_asset_list'),
]
