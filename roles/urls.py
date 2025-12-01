from django.urls import path
from .views import *

app_name = 'roles'

urlpatterns = [
    path('list', list, name='list'),
    path('add', add, name='add'),
    path('update/<str:name>', update, name='update'),
    path('delete/<str:name>', delete, name='delete'),
    path('status/<str:name>', status, name='status'),
    path('search/<str:page>', search, name='search'),
]
