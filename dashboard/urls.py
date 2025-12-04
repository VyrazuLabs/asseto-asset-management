from django.urls import path
from . import views
from .views import global_search_views,api_location_views,api_product_type_views,api_product_category_views, api_department_views,license_type
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

    # path('product/')
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

    #License Type
    path('license-type/list/',license_type.license_type_list,name='license_type_list'),
    path('license-type/add/',license_type.license_type_add,name='add_license_type'),
    path('license-types/details/<int:id>', license_type.license_type_details, name='license_type_details'),
    path('license-type/add/<int:id>',license_type.update_license_type,name='update_license_type'),
    path('license-type/status/<int:id>',license_type.license_type_status,name='license_type_status'),
    path('license-type/delete/<int:id>',license_type.delete_license_type,name='delete_license_type'),
    path('license-type/search/', license_type.search_license_type, name='search_license_type'),

    path('get-subcategories/',views.get_subcategories, name='get_subcategories'),
     
    path('global-search/', global_search_views.global_search, name='global_search'),
]


dashboard_api_urlpatterns=[
    #Location api urls
    path('api/admin/location/location-dropdown-list',api_location_views.LocationListForFormDropdown.as_view(),name='location_dropdown_list'),

    #Location api urls
    path('api/admin/product-type/product-type-dropdown-list',api_product_type_views.ProductTypeListForFormDropdown.as_view(),name='product_type-dropdown_list'),

    #Product Category urls
    path('api/admin/product-category/product-category-dropdown-list',api_product_category_views.ProductCategoryListForFormDropdown.as_view(),name='product_category-dropdown_list'),

    #for fetching the subcategory
    path('api/admin/product-category/product-sub-category-dropdown-list',api_product_category_views.ProductSubCategoryListForFormDropdown.as_view(),name='product_sub_category-dropdown_list'),

    # Department api urls
    path('api/admin/department/department-dropdown-list',api_department_views.DepartmentListForFormDropdown.as_view(),name='department_dropdown_list')

]