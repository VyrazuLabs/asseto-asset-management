from django.urls import path
from authentication import views
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView,TokenBlacklistView
from . import index_api_views
app_name = 'authentication'

urlpatterns = [
    # Template urls
    path('introduce/', views.introduce, name = 'introduce'),
    path('data-base-configure/',views.db_configure, name="db_configure"),
    path('smtp-email-configure/',views.smtp_email_configure,name='email_configure'),

    path('', views.index, name = 'index'),
    path('login', views.user_login, name = 'login'),
    path('register', views.user_register, name = 'register'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('profile', views.profile, name='profile'),
    path('logout/',views.logout_view, name='logout'),
    path('profile-basic-information/update', views.profile_basic_info_update, name='profile_basic_info_update'),
    path('organization-information/update', views.organization_info_update, name='organization_info_update'),
]

authentication_url_patterns=[
    #api urls
    path('api/authentication/login/', TokenObtainPairView.as_view(),name='login'),
    path('api/authentication/token/refresh/',TokenRefreshView.as_view(),name='token_refresh'),
    # path('api/authentication/token/refresh/',views.get_refresh_token,name='token_refresh'),
    path('api/authentication/logout/',TokenBlacklistView.as_view(),name='logout'),

    #dashboard api urls
    path('api/dashboard/asset-details',index_api_views.AssetData.as_view(),name='asset_datas'),
    path('api/dashboard/user-details',index_api_views.UsersData.as_view(),name='user_datas'),
    path('api/dashboard/product-details',index_api_views.ProductData.as_view(),name='product_datas'),
    path('api/dashboard/vendor-details',index_api_views.VendorData.as_view(),name='vendor_datas'),
    path('api/dashboard/location-details',index_api_views.LocationData.as_view(),name='location_datas'),
]