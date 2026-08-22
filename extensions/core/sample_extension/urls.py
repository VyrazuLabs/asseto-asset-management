from django.urls import path

from . import views

app_name = "ext_sample_extension"

urlpatterns = [
    path("", views.index, name="index"),
]
