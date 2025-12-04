from django.urls import path
from . import views

app_name = 'license'

urlpatterns=[
    path('list/',views.license_list,name='license_list'),
    path('add/',views.add_license,name='add_license'),
    path('details/<int:id>',views.license_details,name='license_details'),
    path('update/<int:id>',views.update_license,name='update_license'),
    path('delete/<int:id>',views.delete_license,name='delete_license'),
    path('search/',views.search_license,name='search_license')
]