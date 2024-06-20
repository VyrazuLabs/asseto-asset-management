from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [

    path('list', views.list, name='list'),
    path('count', views.count, name='count'),
    path('data', views.data, name='data'),
    path('clear', views.clear, name='clear'),
    path('seen/<int:id>', views.seen, name='seen'),
    path('search/<str:page>', views.search, name='search'),
]
