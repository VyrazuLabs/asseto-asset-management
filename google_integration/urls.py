from django.urls import path

from . import views

app_name = "google_integration"

urlpatterns = [
    path("connect/", views.connect_google, name="connect_google"),
    path("oauth/callback/", views.google_oauth_callback, name="google_oauth_callback"),
]
