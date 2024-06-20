from django.urls import path
from . import views

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
