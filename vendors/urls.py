from django.urls import path
from . import views,api_views
app_name = 'vendors'

urlpatterns = [
    path('list', views.vendor_list, name='list'),
    path('search/<str:page>', views.search, name='search'),
    path('details/<uuid:id>', views.details, name='details'),
    path('add', views.add_vendor, name='add'),
    path('delete/<uuid:id>', views.delete_vendor, name='delete_vendor'),
    path('update/<uuid:id>', views.update_vendor, name='update_vendor'),
    path('status/<uuid:id>', views.status, name='status'),
    path('csv', views.export_vendors_csv, name='export_vendors_csv'),
    path('pdf', views.export_vendors_pdf, name='export_vendors_pdf'),
]

vendor_api_urlpatterns = [
    path('api/vendor/list',api_views.VendorList.as_view(),name='vendor_list'),
    path('api/vendor/add',api_views.AddVendor.as_view(),name='add_vendor'),
    path('api/vendor/details/<uuid:id>',api_views.VendorDetails.as_view(),name='vendor_details'),
    path('api/vendor/update/<uuid:id>',api_views.UpdateVendor.as_view(),name='update_vendor'),
    path('api/vendor/delete/<uuid:id>',api_views.DeleteVendor.as_view(),name='vendor_details'),
    path('api/vendor/search/',api_views.SearchVendor.as_view(),name='search_vendor'),

]