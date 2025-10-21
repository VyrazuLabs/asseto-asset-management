from django.urls import path
from django.views.generic import TemplateView
# from .views import OrganizationLogo
from . import views
app_name = 'configurations'

urlpatterns=[
    # path('upload-logo/' ,TemplateView.as_view(template_name='configurations/logo.html'),name='upload_logo'),
    path('upload-logo/',views.logo_upload,name='upload_logo'),
    path('delete-logo/<int:id>',views.delete_logo,name='delete_logo')
]