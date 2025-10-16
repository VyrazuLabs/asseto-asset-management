from django.urls import path
from . import views

urlpatterns = [
    path("slack/install/<int:org_id>/", views.slack_install, name="slack_install"),
    path("slack/oauth/callback/", views.slack_oauth_callback, name="slack_oauth_callback"),
]