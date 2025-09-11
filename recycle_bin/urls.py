from django.urls import path
from . import views

app_name = 'recycle_bin'

urlpatterns = [
    path('deleted-products', views.deleted_products, name='deleted_products'),
    path('deleted-products/restore/<uuid:id>', views.deleted_products_restore, name='deleted_products_restore'),
    path('deleted-products/delete/<uuid:id>', views.deleted_products_permanently, name='deleted_products_permanently'),
    path('deleted-products-search/<str:page>', views.deleted_products_search, name='deleted_products_search'),
    
    path('deleted-vendors', views.deleted_vendors, name='deleted_vendors'),
    path('deleted-vendors/restore/<uuid:id>', views.deleted_vendor_restore, name='deleted_vendor_restore'),
    path('deleted-vendors/delete/<uuid:id>', views.deleted_vendor_permanently, name='deleted_vendor_permanently'),
    path('deleted-vendors-search/<str:page>', views.deleted_vendors_search, name='deleted_vendors_search'),

    path('deleted-assets', views.deleted_assets, name='deleted_assets'),
    path('deleted-assets/restore/<uuid:id>', views.deleted_asset_restore, name='deleted_asset_restore'),
    path('deleted-assets/delete/<uuid:id>', views.deleted_asset_permanently, name='deleted_asset_permanently'),
    path('deleted-assets-search/<str:page>', views.deleted_assets_search, name='deleted_assets_search'),

    path('deleted-users', views.deleted_users, name='deleted_users'),
    path('deleted-users/restore/<uuid:id>', views.deleted_user_restore, name='deleted_user_restore'),
    path('deleted-users/delete/<uuid:id>', views.deleted_user_permanently, name='deleted_user_permanently'),
    path('deleted-users-search/<str:page>', views.deleted_users_search, name='deleted_users_search'),


    path('deleted-locations', views.deleted_locations, name='deleted_locations'),
    path('deleted-locations/restore/<uuid:id>', views.deleted_locations_restore, name='deleted_locations_restore'),
    path('deleted-locations/delete/<uuid:id>', views.deleted_locations_permanently, name='deleted_locations_permanently'),
    path('deleted-locations-search/<str:page>', views.deleted_locations_search, name='deleted_locations_search'),


    path('deleted-departments', views.deleted_depertments, name='deleted_departments'),
    path('deleted-departments/restore/<uuid:id>', views.deleted_departments_restore, name='deleted_departments_restore'),
    path('deleted-departments/delete/<uuid:id>', views.deleted_departments_permanently, name='deleted_departments_permanently'),
    path('deleted-departments-search/<str:page>', views.deleted_departments_search, name='deleted_departments_search'),


    path('deleted_product_categories', views.deleted_product_categories, name='deleted_product_categories'),
    path('deleted_product_categories/restore/<uuid:id>', views.deleted_product_categories_restore, name='deleted_product_categories_restore'),
    path('deleted_product_categories/delete/<uuid:id>', views.deleted_product_categories_permanently, name='deleted_product_categories_permanently'),
    path('search_deleted_product_categories/<str:page>', views.search_deleted_product_categories, name='search_deleted_product_categories'),

    path('deleted_product_types', views.deleted_product_types, name='deleted_product_types'),
    path('deleted_product_types/restore/<uuid:id>', views.deleted_product_types_restore, name='deleted_product_types_restore'),
    path('deleted_product_types/delete/<uuid:id>', views.deleted_product_types_permanently, name='deleted_product_types_permanently'),
    path('deleted_product_types_search/<str:page>', views.deleted_product_types_search, name='deleted_product_types_search'),

    path('deleted_asset_status', views.deleted_asset_status, name='deleted_asset_status'),
    path('deleted_asset_status/restore/<uuid:id>', views.deleted_asset_status_restore, name='deleted_asset_status_restore'),
    path('deleted_asset_status/delete/<uuid:id>', views.deleted_asset_status_permanently, name='deleted_asset_status_permanently'),
    path('deleted_asset_status_search/<str:page>', views.deleted_asset_status_search, name='deleted_asset_status_search'),
]