from django.urls import path
from django.views.generic import TemplateView
# from .views import OrganizationLogo
from . import views
app_name = 'configurations'

urlpatterns=[
    # path('upload-logo/' ,TemplateView.as_view(template_name='configurations/logo.html'),name='upload_logo'),
    path('upload-logo/',views.logo_upload,name='upload_logo'),
    path('delete-logo/<int:id>',views.delete_logo,name='delete_logo'),
    path('update-tag-configuration/<str:id>/', views.create_or_update_tag_configuration, name='update_tag_configuration'),
    path('update-tag-configuration/', views.create_or_update_tag_configuration, name='update_tag_configuration_without_id'),
    # path('update-tag-configuration/<str:id>/', views.update_tag_configuration, name='update_tag_configuration'),
    path('list-tag-configuration/', views.list_tag_configurations, name='list_tag'),
    path('toggle-default-settings/<str:id>/', views.toggle_default_settings, name='toggle_default_settings'),
]