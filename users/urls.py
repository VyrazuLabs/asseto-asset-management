from django.urls import path
from .views import *
from .api_views import UserList,UserDetails,AddUser,UpdateUser,DeleteUSer,SearchUser

app_name = 'users'

urlpatterns = [
    #Template urls
    path('list', list, name='list'),
    path('detail/<uuid:id>', details, name='details'),
    path('add', add, name='add'),
    path('update/<uuid:id>', update, name='update'),
    path('delete/<uuid:id>', delete, name='delete'),
    path('status/<uuid:id>', status, name='status'),
    path('search/<str:page>', search, name='search'),
    path('csv', export_users_csv, name='export_users_csv'),
    path('pdf', export_users_pdf, name='export_users_pdf'),
    path('assigned-assets/<uuid:id>', user_assigned_assets, name='user_assigned_assets'),
    path('render-username/', render_format_based_username, name='render_format_based_username'),
]

user_api_url_patterns=[
    #api urls
    path('api/user/list/',UserList.as_view(),name='user_list'),
    path('api/user/add/',AddUser.as_view(),name='add_user'),
    path('api/user/details/<uuid:id>',UserDetails.as_view(),name='user_details'),
    path('api/user/update/<uuid:id>',UpdateUser.as_view(),name='update_user'),
    path('api/user/delete/<uuid:id>',DeleteUSer.as_view(),name='delete_user'),
    path('api/user/search/',SearchUser.as_view(),name='search_user')
]