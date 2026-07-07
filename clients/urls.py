from django.urls import path
from . import views

app_name = "clients"

urlpatterns = [
    path("list", views.client_list, name="list"),
    path("add", views.add_client, name="add"),
    path("details/<uuid:id>", views.client_detail, name="details"),
    path("update/<uuid:id>", views.update_client, name="update"),
    path("status/<uuid:id>", views.toggle_status, name="status"),
    path("delete/<uuid:id>", views.delete_client, name="delete"),
    path("search/<str:page>", views.search_clients, name="search"),
    path("export-csv", views.export_clients_csv, name="export_csv"),
    path("export-pdf", views.export_clients_pdf, name="export_pdf"),
    path("details/<uuid:id>/locations/add", views.add_client_location, name="add_location"),
    path("locations/update/<uuid:id>", views.update_client_location, name="update_location"),
    path("locations/delete/<uuid:id>", views.delete_client_location, name="delete_location"),
]
