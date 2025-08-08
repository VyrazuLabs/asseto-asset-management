from django.urls import path
from authentication import views
from django.contrib.auth import views as auth_views

app_name = 'authentication'

urlpatterns = [
    path('', views.index, name = 'index'),
    path('login', views.user_login, name = 'login'),
    path('register', views.user_register, name = 'register'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('profile', views.profile, name='profile'),
    # path('logout', auth_views.LogoutView.as_view(next_page='authentication:login'), name='logout'),
    path('logout/',views.logout_view, name='logout'),
    path('profile-basic-information/update', views.profile_basic_info_update, name='profile_basic_info_update'),
    path('organization-information/update', views.organization_info_update, name='organization_info_update'),
]
