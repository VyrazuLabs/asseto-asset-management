from django.urls import path
from .views import *


app_name = 'upload'

urlpatterns = [
    path('vendors', vendor_list, name='vendor_list'),
    path('vendors/export/csv', export_vendors_csv, name='export_vendors_csv'),
    path('vendors/import/csv', import_vendors_csv, name = 'import_vendors_csv'),
    
    path('locations', location_list, name='location_list'),
    path('locations/export/csv', export_locations_csv, name='export_locations_csv'),
    path('locations/import/csv', import_locations_csv, name = 'import_locations_csv'),

    path('product-types', product_type_list, name='product_type_list'),
    path('product-types/export/csv', export_product_types_csv, name='export_product_types_csv'),
    path('product-types/import/csv', import_product_types_csv, name ='import_product_types_csv' ),

    path('product-categories', product_category_list, name='product_category_list'),
    path('product-categories/export/csv', export_product_categories_csv, name='export_product_categories_csv'),
    path('product-categories/import/csv', import_product_catagories_csv, name='import_product_catagories_csv'),
    
    path('departments', department_list, name = 'department_list' ),
    path('departments/export/csv', export_departments_csv , name='export_departments_csv'),
    path('departments/import/csv', import_departments_csv , name='import_departments_csv'),
    path('compare-data', render_to_mapper_modal, name='compare_data'),
    path('create-obj-department',create_matched_data_from_csv_department, name='create_data'),
    path('create-obj-location',create_matched_data_from_csv_locations,name='create-location-data'),
]
