from django.urls import path
from . import views
from .views import user_views
from .views import asset_bulk_upload_views

app_name = "upload"

urlpatterns = [
    path("vendors/", views.vendor_list, name="vendor_list"),
    path("vendors/export/csv", views.export_vendors_csv, name="export_vendors_csv"),
    path("vendors/import/csv", views.import_vendors_csv, name="import_vendors_csv"),
    path(
        "vendors/search/<str:page>",
        views.search_vendor_upload,
        name="search_vendor_upload",
    ),
    path(
        "venodrs-compare-data/",
        views.vendor_render_to_mapper_modal,
        name="vendor-compare_data",
    ),
    path("locations/", views.location_list, name="location_list"),
    path(
        "locations/export/csv", views.export_locations_csv, name="export_locations_csv"
    ),
    path(
        "locations/import/csv", views.import_locations_csv, name="import_locations_csv"
    ),
    path(
        "locations/search/<str:page>",
        views.search_location_upload,
        name="search_location_upload",
    ),
    path(
        "locations-compare-data/",
        views.location_render_to_mapper_modal,
        name="locations_compare_data",
    ),
    path(
        "create-obj-location/",
        views.create_matched_data_from_csv_locations,
        name="create-location-data",
    ),
    path("product-types/", views.product_type_list, name="product_type_list"),
    path(
        "product-types/export/csv",
        views.export_product_types_csv,
        name="export_product_types_csv",
    ),
    path(
        "product-types/import/csv",
        views.import_product_types_csv,
        name="import_product_types_csv",
    ),
    path(
        "product-types/search/<str:page>",
        views.search_product_type_upload,
        name="search_product_type_upload",
    ),
    path(
        "product-type-compare-data/",
        views.product_type_render_to_mapper_model,
        name="product_type_compare_data",
    ),
    path(
        "product-categories/", views.product_category_list, name="product_category_list"
    ),
    path(
        "product-categories/export/csv",
        views.export_product_categories_csv,
        name="export_product_categories_csv",
    ),
    path(
        "product-categories/import/csv",
        views.import_product_catagories_csv,
        name="import_product_catagories_csv",
    ),
    path(
        "product-categories/search/<str:page>",
        views.search_product_category_upload,
        name="search_product_category_upload",
    ),
    path(
        "product-categories-compare-data/",
        views.product_category_render_to_mapper_model,
        name="product_categories_compare_data",
    ),
    path("departments/", views.department_list, name="department_list"),
    path(
        "departments/export/csv",
        views.export_departments_csv,
        name="export_departments_csv",
    ),
    path(
        "departments/import/csv",
        views.import_departments_csv,
        name="import_departments_csv",
    ),
    path(
        "departments/search/<str:page>",
        views.search_department_upload,
        name="search_department_upload",
    ),
    path(
        "departments-compare-data/",
        views.department_render_to_mapper_modal,
        name="department_compare_data",
    ),
    path(
        "create-obj-department/",
        views.create_matched_data_from_csv_department,
        name="create_data",
    ),
    path("users/", user_views.user_list, name="user_list"),
    path("users/export/csv", user_views.export_users_csv, name="export_users_csv"),
    path("users/import/csv", user_views.import_user_csv, name="import_users_csv"),
    path(
        "users/search/<str:page>",
        user_views.search_user_upload,
        name="search_user_upload",
    ),
    path(
        "users-compare-data/",
        user_views.user_render_to_mapper_model,
        name="users_compare_data",
    ),
    path(
        "assets/bulk-import/",
        asset_bulk_upload_views.bulk_import_step1,
        name="bulk_import_step1",
    ),
    path(
        "assets/bulk-import/map/",
        asset_bulk_upload_views.bulk_import_step2,
        name="bulk_import_step2",
    ),

    path(
        "assets/bulk-import/finalize/",
        asset_bulk_upload_views.bulk_import_step4,
        name="bulk_import_step4",
    ),
    path(
        "assets/bulk-import/template/csv/",
        asset_bulk_upload_views.download_asset_template_csv,
        name="bulk_import_template_csv",
    ),
    path(
        "assets/bulk-import/template/zip/",
        asset_bulk_upload_views.download_asset_template_zip,
        name="bulk_import_template_zip",
    ),
    path(
        "assets/bulk-import/cancel/",
        asset_bulk_upload_views.bulk_import_cancel,
        name="bulk_import_cancel",
    ),
]
