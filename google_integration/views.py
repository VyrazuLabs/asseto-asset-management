import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from . import oauth, provisioning
from .firebase_admin_client import reset_cached_app
from .models import GoogleCloudFirebaseConfig

logger = logging.getLogger(__name__)


def _is_superuser(user) -> bool:
    """Gate: only superusers may connect/manage the instance-wide Firebase project."""
    return user.is_superuser


@login_required
@user_passes_test(_is_superuser)
def connect_google(request):
    """Redirect the superadmin to Google's OAuth consent screen."""
    return redirect(oauth.build_authorization_url(request))


@login_required
@user_passes_test(_is_superuser)
def google_oauth_callback(request):
    """Handle Google's OAuth redirect: verify state, provision, persist.

    Rejects on missing/mismatched `state` before any network call — the
    explicit CSRF fix over the existing Slack OAuth flow
    (`assets/views.py::slack_oauth_callback`), which has no such check.
    """
    if not oauth.verify_state(request):
        return HttpResponse("Invalid or expired OAuth state.", status=400)

    code = request.GET.get("code")
    if not code:
        return HttpResponse("Missing authorization code.", status=400)

    config = GoogleCloudFirebaseConfig.load()

    try:
        token_response = oauth.exchange_code_for_tokens(code)
        result = provisioning.provision_firebase_project(
            token_response, display_name="Asseto Asset Management"
        )
    except provisioning.ProvisioningError as exc:
        config.last_error = str(exc)
        config.save(update_fields=["last_error"])
        messages.error(request, f"Google Cloud connection failed: {exc}")
        return redirect(reverse("configurations:list_extensions"))

    with transaction.atomic():
        for field, value in result.items():
            setattr(config, field, value)
        config.is_connected = True
        config.connected_by = request.user
        config.connected_at = timezone.now()
        config.last_error = None
        config.save()

    reset_cached_app()
    messages.success(request, "Google Cloud connected — Firebase push notifications are now active.")
    return redirect(reverse("configurations:list_extensions"))


def firebase_messaging_sw(request):
    """Serve the Firebase messaging service worker, rendered from DB config.

    Replaces the old static file that shipped with a hardcoded, leaked
    project key. Must stay publicly fetchable (no permission gate) and at
    the root path — service worker scope is tied to the URL it's served
    from.
    """
    config = GoogleCloudFirebaseConfig.objects.filter(pk=1, is_connected=True).first()
    context = {
        "web_config_json": json.dumps(
            {
                "apiKey": config.web_api_key if config else "",
                "authDomain": config.web_auth_domain if config else "",
                "projectId": config.web_project_id if config else "",
                "storageBucket": config.web_storage_bucket if config else "",
                "messagingSenderId": config.web_messaging_sender_id if config else "",
                "appId": config.web_app_id if config else "",
            }
        ),
        "vapid_key_json": json.dumps(config.web_vapid_key if config and config.web_vapid_key else ""),
    }
    return render(
        request,
        "google_integration/firebase-messaging-sw.js",
        context,
        content_type="application/javascript",
    )
