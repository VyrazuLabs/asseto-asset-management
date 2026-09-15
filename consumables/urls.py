from django.urls import path
from . import views

app_name = "consumables"

urlpatterns = [
    path("list", views.consumable_list, name="list"),
    path("add", views.add_consumable, name="add"),
    path("detail/<uuid:pk>", views.detail_consumable, name="detail"),
    path("edit/<uuid:pk>", views.edit_consumable, name="edit"),
    path("delete/<uuid:pk>", views.delete_consumable, name="delete"),
    path("checkout/<uuid:pk>", views.checkout_consumable, name="checkout"),
    path("search/<str:page>", views.search, name="search"),
]
