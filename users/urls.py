from django.urls import path
from .views import *

app_name = 'users'

urlpatterns = [
    path('list', list, name='list'),
    path('detail/<uuid:id>', details, name='details'),
    path('add', add, name='add'),
    path('update/<uuid:id>', update, name='update'),
    path('delete/<uuid:id>', delete, name='delete'),
    path('status/<uuid:id>', status, name='status'),
    path('search/<str:page>', search, name='search'),
    path('csv', export_users_csv, name='export_users_csv'),
    path('pdf', export_users_pdf, name='export_users_pdf'),
    path('assigned-assets/<uuid:id>', user_assigned_assets, name='user_assigned_assets')
]
