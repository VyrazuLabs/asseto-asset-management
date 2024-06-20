from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('list', views.list, name='list'),
    path('details/<uuid:id>', views.details, name='details'),
    path('update/<uuid:id>', views.update, name='update'),
    path('delete/<uuid:id>', views.delete, name='delete'),
    path('status/<uuid:id>', views.status, name='status'),
    path('add', views.add, name='add'),
    path('search/<str:page>', views.search, name='search'),
    path('assigned-list', views.assigned_list, name='assigned_list'),
    path('assign-asset', views.assign_asset, name='assign_asset'),
    path('reassign-asset/<uuid:id>', views.reassign_asset, name='reassign_asset'),
    path('delete-assign/<uuid:id>', views.delete_assign, name='delete_assign'),
    path('assign_asset_search/<str:page>', views.assign_asset_search, name='assign_asset_search'),
]
