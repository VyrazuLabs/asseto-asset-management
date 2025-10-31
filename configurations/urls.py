from django.urls import path
from django.views.generic import TemplateView
# from .views import OrganizationLogo
from . import views
app_name = 'configurations'

urlpatterns=[
    path('upload-logo/',views.logo_upload,name='upload_logo'),
    path('delete-logo/<int:id>',views.delete_logo,name='delete_logo'),
    path('delete-favicon/<int:id>',views.delete_favicon,name='delete_favicon'),
    path('delete-login-page-logo/<int:id>',views.delete_login_page_logo,name='delete_login_page_logo'),
    path('update-tag-configuration/<str:id>/', views.create_or_update_tag_configuration, name='update_tag_configuration'),
    path('update-tag-configuration/', views.create_or_update_tag_configuration, name='update_tag_configuration_without_id'),
    # path('update-tag-configuration/<str:id>/', views.update_tag_configuration, name='update_tag_configuration'),
    path('list-tag-configuration/', views.list_tag_configurations, name='list_tag'),
    path('toggle-default-settings/<str:id>/', views.toggle_default_settings, name='toggle_default_settings'),
    path('list-localization/', views.list_localizations, name='list_localization'),
    path('create-localization-configuration/', views.create_localization_configuration, name='create_localization_configuration'),
    path('integration/', views.integration, name='integration'),

]