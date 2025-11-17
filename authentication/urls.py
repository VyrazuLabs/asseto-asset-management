from django.urls import path
from authentication import views
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView,TokenBlacklistView
app_name = 'authentication'

urlpatterns = [
    # Template urls
    path('introduce/', views.introduce, name = 'introduce'),
    path('data-base-configure/',views.db_configure, name="db_configure"),
    path('', views.index, name = 'index'),
    path('login', views.user_login, name = 'login'),
    path('register', views.user_register, name = 'register'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('profile', views.profile, name='profile'),
    path('logout/',views.logout_view, name='logout'),
    path('profile-basic-information/update', views.profile_basic_info_update, name='profile_basic_info_update'),
    path('organization-information/update', views.organization_info_update, name='organization_info_update'),



    #api urls
    path('api/login/', TokenObtainPairView.as_view(),name='api_login'),
    path('api/token/refresh/',TokenRefreshView.as_view(),name='api_token_refresh'),
    path('api/logout/',TokenBlacklistView.as_view(),name='api_logout')
]
