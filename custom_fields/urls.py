from django.urls import path
from . import views

app_name = "custom_fields"

urlpatterns = [
    path("",                      views.list_custom_fields,   name="list"),
    path("create/",               views.create_custom_field,  name="create"),
    path("search/<str:page>",     views.search_custom_fields, name="search"),
    path("<uuid:pk>/update/",     views.update_custom_field,  name="update"),
    path("<uuid:pk>/delete/",     views.delete_custom_field,  name="delete"),
    path("<uuid:pk>/toggle/",     views.toggle_custom_field,  name="toggle"),
]
