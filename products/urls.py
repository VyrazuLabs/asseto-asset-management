from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('list', views.list, name='list'),
    path('add', views.add_product, name='add'),
    path('details/<uuid:id>', views.details_product, name='details_product'),
    path('delete/<uuid:id>', views.delete_product, name='delete_product'),
    path('update/<uuid:id>', views.update_product, name='update_product'),
    path('status/<uuid:id>', views.status, name='status'),
    path('search/<str:page>', views.search, name='search'),
    path('csv', views.export_products_csv, name='export_products_csv'),
    path('pdf', views.export_products_pdf, name='export_products_pdf'),
    path('assigned-product-info/<uuid:id>', views.get_assigned_product_info, name='assigned_product_info'),
]