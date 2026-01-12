from django.urls import path
from .barcode import Scan_barcode
from . import views
from . import asset_status_views
from . import api_views
from .api_views import GetNotifications
app_name = 'assets'

urlpatterns = [
    #template_urls

    path('list', views.listed, name='list'),
    path('details/<uuid:id>', views.details, name='details'),
    path('delete/<uuid:id>', views.delete, name='delete'),
    path('update-assets-details/<str:id>/',views.update_in_detail,name='update_in_detail'),
    path('add', views.add, name='add'),
    path('search/<str:page>', views.search, name='search'),
    #assigned assets
    path('assigned-list', views.assigned_list, name='assigned_list'),
    path('assign-asset', views.assign_assets, name='assign_asset'),
    path('delete-assign/<uuid:id>', views.delete_assign, name='delete_assign'),
    path('delete-assign-asset-list/<uuid:id>', views.delete_assign_asset_list, name='delete_assign_asset_list'),
    path('assign-asset-in-asset-list/<uuid:id>', views.assign_asset_in_asset_list, name='assign_asset_in_asset_list'),
    path('assign_asset_search/<str:page>', views.assign_asset_search, name='assign_asset_search'),
    path('reassign-asset/<uuid:id>', views.reassign_asset, name='reassign_asset'),
    # urls for pie chart
    path('piechart_status_data/', views.pie_chart_assigned_status, name='piechart_status_data'),
    path('assets_by_status', views.pie_chart_status, name='pie_chart_status'),

    #asset status urls
    path('change-status/<uuid:id>/',views.change_status,name='change_status'),
    path('add_status',asset_status_views.add_asset_status,name='add_asset_status'),
    path('asset_status_list',asset_status_views.asset_status_list,name='asset_status_list'),
    path('asset_status_details/<uuid:id>',asset_status_views.asset_status_details,name='asset_status_details'),
    path('edit_asset_status/<uuid:id>',asset_status_views.edit_asset_status,name='edit_asset_status'),
    path('asset_status_search/<str:page>',asset_status_views.asset_status_search,name='asset_status_search'),
    path('delete_asset_status/<uuid:id>',asset_status_views.delete_asset_status,name='delete_asset_status'),

    # url for generate barcodes
    path('scan-barcode/<str:tag_id>',Scan_barcode.as_view(), name='barcode'),
    path('slack-authorize/', views.slack_authorize, name='slack_authorize'),
    path('slack/oauth/callback/', views.slack_oauth_callback, name='slack_oauth_callback'),
]

api_url_patterns = [
    #api urls
    path('api/asset/list/',api_views.AssetList.as_view(),name="asset_list"),
    path('api/asset/add/',api_views.AddAsset.as_view(),name='add_asset'),
    path('api/asset/details/<uuid:id>/',api_views.AssetDetails.as_view(),name="asset_details"),
    path('api/asset/update/<uuid:id>',api_views.UpdateAsset.as_view(),name='update_asset'),
    path('api/asset/delete/<uuid:id>',api_views.DeleteAsset.as_view(),name="delete_asset"),
    path('api/asset/search/',api_views.SearchAsset.as_view(),name='search_asset'),
    path('api/asset/scan-barcode/<str:tag_id>',api_views.Scan_api_barcode.as_view(), name='scan_barcode'),
    path('api/asset/details/update-asset-status/<uuid:id>',api_views.UpdateAssetStatus.as_view(),name="update_asset_status"),
    path('api/asset/details/assign-asset/<uuid:id>',api_views.AssignAsset.as_view(),name="assign_asset"),
    path('api/asset/details/unassign-asset/<uuid:id>',api_views.UnAssignAsset.as_view(),name="unassign_asset"),
    path('api/asset/details/user-list-for-assign-asset',api_views.UserListForAssignAsset.as_view(),name="user_list_for_assign_asset"),
    path('api/asset/get-notifications',api_views.GetNotifications.as_view(),name="get_notifications")
]
