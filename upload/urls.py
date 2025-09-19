from django.urls import path
from . import views


app_name = 'upload'

urlpatterns = [
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/export/csv', views.export_vendors_csv, name='export_vendors_csv'),
    path('vendors/import/csv', views.import_vendors_csv, name = 'import_vendors_csv'),
    path('venodrs-compare-data/', views.vendor_render_to_mapper_modal, name='vendor-compare_data'),
    
    path('locations/', views.location_list, name='location_list'),
    path('locations/export/csv', views.export_locations_csv, name='export_locations_csv'),
    path('locations/import/csv', views.import_locations_csv, name = 'import_locations_csv'),
    path('locations-compare-data/', views.location_render_to_mapper_modal, name='locations_compare_data'),
    path('create-obj-location/',views.create_matched_data_from_csv_locations,name='create-location-data'),

    path('product-types/', views.product_type_list, name='product_type_list'),
    path('product-types/export/csv', views.export_product_types_csv, name='export_product_types_csv'),
    path('product-types/import/csv', views.import_product_types_csv, name ='import_product_types_csv' ),
    path('product-type-compare-data/', views.product_type_render_to_mapper_model, name='product_type_compare_data'),

    path('product-categories/', views.product_category_list, name='product_category_list'),
    path('product-categories/export/csv', views.export_product_categories_csv, name='export_product_categories_csv'),
    path('product-categories/import/csv', views.import_product_catagories_csv, name='import_product_catagories_csv'),
    path('product-categories-compare-data/', views.product_category_render_to_mapper_model, name='product_categories_compare_data'),
    
    path('departments/', views.department_list, name = 'department_list' ),
    path('departments/export/csv', views.export_departments_csv , name='export_departments_csv'),
    path('departments/import/csv', views.import_departments_csv , name='import_departments_csv'),
    path('departments-compare-data/', views.department_render_to_mapper_modal, name='department_compare_data'),
    path('create-obj-department/',views.create_matched_data_from_csv_department, name='create_data'),
    
]
