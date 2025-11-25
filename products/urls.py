from django.urls import path
from . import views,api_views

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

product_api_urlpattrens=[

    path('api/product/list',api_views.ProductList.as_view(),name='product_list'),
    path('api/product/add',api_views.AddProduct.as_view(),name='add_prdoct'),
    path('api/product/details/<uuid:id>',api_views.ProductDetails.as_view(),name='prdoct_details'),
    path('api/product/update/<uuid:id>',api_views.UpdateProduct.as_view(),name='update_prdoct'),
    path('api/product/delete/<uuid:id>',api_views.DeleteProduct.as_view(),name='delete_prdoct'),
    path('api/product/search',api_views.SearchProduct.as_view(),name='search_prdoct')
]