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
]