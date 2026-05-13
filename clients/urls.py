from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('list',                  views.client_list,    name='list'),
    path('add',                   views.add_client,     name='add'),
    path('details/<uuid:id>',     views.client_detail,  name='details'),
    path('update/<uuid:id>',      views.update_client,  name='update'),
    path('delete/<uuid:id>',      views.delete_client,  name='delete'),
    path('search/<str:page>',     views.search_clients, name='search'),
    path('export',                views.export_clients, name='export'),
]
