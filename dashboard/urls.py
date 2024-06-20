from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
     
    # location urls
    path('locations/list', views.locations, name='locations'),
    path('locations/add', views.add_location, name='add_location'),
    path('locations/details/<uuid:id>', views.location_details, name='location_details'),
    path('locations/update/<uuid:id>', views.update_location, name='update_location'),
    path('locations/delete/<uuid:id>', views.delete_location, name='delete_location'),
    path('locations/status/<uuid:id>', views.location_status, name='location_status'),
    path('locations/search/<str:page>', views.search_location, name='search_location'),

    # department urls
    path('departments/list', views.departments, name='departments'),
    path('departments/detail/<uuid:id>', views.department_details, name='department_details'),
    path('departments/updates/<uuid:id>', views.update_department, name='update_department'),
    path('departments/add', views.add_department, name='add_department'),
    path('departments/delete/<uuid:id>', views.delete_department, name='delete_department'),
    path('departments/status/<uuid:id>', views.department_status, name='department_status'),
    path('departments/search/<str:page>', views.search_department, name='search_department'),

    # product type urls
    path('product-types/list', views.product_type_list, name='product_type_list'),
    path('product-types/add', views.add_product_type, name='add_product_type'),
    path('product-types/details/<uuid:id>', views.product_type_details, name='product_type_details'),
    path('product-types/update/<uuid:id>', views.update_product_type, name='update_product_type'),
    path('product-types/delete/<uuid:id>', views.delete_product_type, name='delete_product_type'),
    path('product-types/status/<uuid:id>', views.product_type_status, name='product_type_status'),
    path('product-types/search/<str:page>', views.search_product_type, name='search_product_type'),

    # product category urls
    path('product-categories/list', views.product_category_list, name='product_category_list'),
    path('product-categories/add', views.add_product_category,name='add_product_category'),
    path('product-categories/details/<uuid:id>', views.product_category_details, name='product_category_details'),
    path('product-categories/delete/<uuid:id>', views.delete_product_category, name='delete_product_category'),
    path('product-categories/update/<uuid:id>', views.update_product_category, name='update_product_category'),
    path('product-categories/status/<uuid:id>', views.product_category_status, name='product_category_status'),
    path('product-categories/search/<str:page>', views.search_product_category, name='search_product_category'),
]