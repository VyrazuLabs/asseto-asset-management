"""
SMS integration views — provider-agnostic.

All provider-specific knowledge lives in configurations/sms_providers/.
This view only:
  - reads provider metadata from the registry (credential_fields, etc.)
  - stores / retrieves SMSConfiguration rows
  - delegates send/validate calls to the provider instance

Adding a new SMS provider requires ZERO changes here.
"""

import json
import logging
import re

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from configurations.models import Extensions, SMSConfiguration, SMSLog
from configurations.sms_providers.registry import PROVIDER_REGISTRY, get_provider_class

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider UI metadata — presentation-only data that belongs in the view tier.
# Field definitions (required keys, types) come from provider.credential_fields().
# This dict only carries badges, descriptions, docs links, and setup guides.
# ---------------------------------------------------------------------------

_PROVIDER_UI: dict[str, dict] = {
    "msg91": {
        "name": "MSG91",
        "badge": "Recommended (DLT Compliant)",
        "badge_class": "bg-primary",
        "doc_url": "https://msg91.com/help",
        "portal_url": "https://msg91.com",
        "description": "Fast and enterprise-grade SMS service with Indian TRAI/DLT compliance.",
        "guide": [
            "Log in or register at <a href='https://msg91.com' target='_blank' "
            "class='fw-bold text-primary'>msg91.com</a>.",
            "Register a 6-character <strong>Sender ID</strong> (e.g. <code>ASSETO</code>) "
            "on your Indian DLT portal and link it in MSG91.",
            "Go to <strong>SMS &gt; Campaign / Flow Builder</strong> and create a flow "
            "with variables (e.g. <code>ticket_id</code>, <code>subject</code>).",
            "Generate or copy your <strong>Auth Key</strong> from MSG91 Settings &gt; Authkey.",
            "Paste credentials below, send a quick <strong>Test SMS</strong>, "
            "then save and activate the service.",
        ],
    },
    "twilio": {
        "name": "Twilio",
        "badge": "Global SMS Carrier",
        "badge_class": "bg-success",
        "doc_url": "https://www.twilio.com/docs/sms",
        "portal_url": "https://console.twilio.com",
        "description": "Global SMS delivery platform ideal for international clients and employees.",
        "guide": [
            "Log in to the <a href='https://console.twilio.com' target='_blank' "
            "class='fw-bold text-primary'>Twilio Console</a>.",
            "Copy your <strong>Account SID</strong> and <strong>Auth Token</strong> "
            "from the Project Info panel.",
            "Ensure you have an active SMS-capable Twilio number under "
            "Phone Numbers &gt; Active Numbers.",
            "Enter the values below and verify with the Test SMS tool.",
        ],
    },
}


def _build_providers_metadata() -> dict:
    """
    Merge registry credential_fields() with UI-only presentation data.
    Returns a dict keyed by provider id — the template iterates this.
    """
    result = {}
    for key, cls in PROVIDER_REGISTRY.items():
        ui = _PROVIDER_UI.get(key, {})
        result[key] = {
            "id": key,
            "name": ui.get("name", key.upper()),
            "badge": ui.get("badge", ""),
            "badge_class": ui.get("badge_class", "bg-secondary"),
            "doc_url": ui.get("doc_url", ""),
            "portal_url": ui.get("portal_url", ""),
            "description": ui.get("description", ""),
            "guide": ui.get("guide", []),
            "fields": cls.credential_fields(),   # ← comes from the provider class
        }
    return result


def _mask_secret(value: str) -> str:
    """Replace a secret string with bullet characters for display."""
    return "•" * len(value) if value else ""


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


@login_required
@permission_required("configurations.view_extensions", raise_exception=True)
def sms_integration(request):
    """Render the SMS integration configuration dashboard."""
    org = request.user.organization
    providers_meta = _build_providers_metadata()

    # Ensure SMS extension row exists for this org
    sms_extension, _ = Extensions.objects.get_or_create(
        organization=org,
        entity_name="SMS",
        defaults={
            "description": (
                "Configure SMS provider to send instant automated alerts "
                "for support tickets and tasks."
            ),
            "status": 0,
            "validity": 0,
        },
    )

    # Existing configurations keyed by provider name
    existing_configs = {
        cfg.provider: cfg for cfg in SMSConfiguration.objects.filter(organization=org)
    }

    active_config = next((c for c in existing_configs.values() if c.is_active), None)

    # Determine which provider tab to show
    selected_key = request.GET.get("provider", active_config.provider if active_config else "msg91")
    if selected_key not in providers_meta:
        selected_key = next(iter(providers_meta))

    current_config = existing_configs.get(selected_key)

    # Build masked credential displays for every provider
    all_display_credentials: dict[str, dict] = {}
    provider_status_map: dict[str, bool] = {}
    for prov_key in providers_meta:
        cfg = existing_configs.get(prov_key)
        provider_status_map[prov_key] = bool(cfg and cfg.is_active)
        creds = cfg.credentials if cfg else {}
        all_display_credentials[prov_key] = {
            k: _mask_secret(str(v)) if ("key" in k or "secret" in k or "token" in k) else v
            for k, v in creds.items()
        }

    context = {
        "title": "SMS Service Configuration",
        "sms_extension": sms_extension,
        "providers": providers_meta,
        "selected_provider_key": selected_key,
        "selected_provider": providers_meta[selected_key],
        "current_config": current_config,
        "display_credentials": all_display_credentials.get(selected_key, {}),
        "has_credentials": bool(current_config and current_config.credentials),
        "active_config": active_config,
        # JSON for JS-driven tab switching (no reload)
        "providers_json": json.dumps(providers_meta),
        "all_credentials_json": json.dumps(all_display_credentials),
        "provider_status_json": json.dumps(provider_status_map),
    }
    return render(request, "configurations/sms_integration.html", context)


@login_required
@permission_required("configurations.edit_configuration", raise_exception=True)
@require_POST
def save_sms_configuration(request):
    """Save credentials and activation state for an SMS provider."""
    org = request.user.organization
    provider_key = request.POST.get("provider", "msg91").strip().lower()
    providers_meta = _build_providers_metadata()

    if provider_key not in providers_meta:
        messages.error(request, f"Unknown SMS provider: {provider_key}")
        return redirect("configurations:sms_integration")

    provider_meta = providers_meta[provider_key]
    config, _ = SMSConfiguration.objects.get_or_create(
        organization=org, provider=provider_key
    )
    old_credentials = dict(config.credentials or {})
    new_credentials: dict = {}

    # Validate and collect submitted fields using the provider's own field definitions
    for field in provider_meta["fields"]:
        key = field["key"]
        is_required = field.get("required", False)
        submitted = request.POST.get(key, "").strip()

        if field["type"] == "password":
            if "•" in submitted:
                # User left the masked placeholder — retain the stored value
                if old_credentials.get(key):
                    new_credentials[key] = old_credentials[key]
                elif is_required:
                    messages.error(request, f"Field '{field['label']}' is required.")
                    return redirect(f"/configurations/sms-integration/?provider={provider_key}")
                continue

            if not submitted:
                if is_required:
                    messages.error(request, f"Field '{field['label']}' is required.")
                    return redirect(f"/configurations/sms-integration/?provider={provider_key}")
                continue  # optional password cleared

            new_credentials[key] = submitted
            continue

        # Non-password fields
        if not submitted:
            if is_required:
                messages.error(request, f"Field '{field['label']}' is required.")
                return redirect(f"/configurations/sms-integration/?provider={provider_key}")
            continue

        new_credentials[key] = submitted

    config.credentials = new_credentials

    # Handle activation toggle
    is_active_requested = request.POST.get("is_active") == "on"
    other_active = (
        SMSConfiguration.objects.filter(organization=org, is_active=True)
        .exclude(pk=config.pk)
        .first()
    )

    if is_active_requested:
        # Pre-activation check: required credentials must be present
        missing = [
            f["label"]
            for f in provider_meta["fields"]
            if f.get("required") and not new_credentials.get(f["key"])
        ]
        if missing:
            messages.error(
                request,
                f"Cannot enable SMS service: missing required credentials "
                f"({', '.join(missing)}).",
            )
            return redirect(f"/configurations/sms-integration/?provider={provider_key}")

        if other_active:
            other_active.is_active = False
            other_active.save()

        config.is_active = True
        Extensions.objects.filter(organization=org, entity_name="SMS").update(status=1)

        if other_active:
            messages.success(
                request,
                f"{provider_meta['name']} activated! Switched from "
                f"{other_active.provider.upper()}.",
            )
        else:
            messages.success(
                request, f"{provider_meta['name']} configuration saved and SMS enabled!"
            )
    else:
        was_active = config.is_active
        config.is_active = False

        if was_active:
            Extensions.objects.filter(organization=org, entity_name="SMS").update(status=0)
            messages.success(
                request,
                f"{provider_meta['name']} configuration saved. SMS service disabled.",
            )
        elif other_active:
            messages.success(
                request,
                f"{provider_meta['name']} credentials saved (inactive). "
                f"{other_active.provider.upper()} remains the active provider.",
            )
        else:
            messages.success(request, f"{provider_meta['name']} credentials saved (inactive).")

    config.save()
    return redirect(f"/configurations/sms-integration/?provider={provider_key}")


@login_required
@permission_required("configurations.edit_configuration", raise_exception=True)
@require_POST
def test_sms(request):
    """
    AJAX endpoint: test-send an SMS using either saved or form-submitted credentials.

    Provider-agnostic: delegates all send logic to the provider instance.
    For MSG91 it also runs a credential pre-flight using validate_credentials().
    """
    org = request.user.organization
    provider_key = request.POST.get("provider", "msg91").strip().lower()
    recipient = request.POST.get("phone", "").strip()

    # -- Validate provider --
    try:
        ProviderClass = get_provider_class(provider_key)
    except ValueError:
        return JsonResponse(
            {"success": False, "error": f"Provider '{provider_key}' is not implemented yet."},
            status=400,
        )

    # -- Validate recipient phone --
    cleaned_recipient = recipient.replace(" ", "").replace("-", "")
    phone_digits = cleaned_recipient.lstrip("+")
    if (
        not re.fullmatch(r"\+?\d{10,15}", cleaned_recipient)
        or not phone_digits.isdigit()
        or not (10 <= len(phone_digits) <= 15)
    ):
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Invalid phone number: enter 10–15 digits, "
                    "optionally starting with + and country code "
                    "(e.g. 9876543210 or +919876543210)."
                ),
            },
            status=400,
        )

    # -- Resolve credentials: saved DB config + unsaved form overrides --
    db_config = SMSConfiguration.objects.filter(
        organization=org, provider=provider_key
    ).first()
    credentials = dict(db_config.credentials) if db_config and db_config.credentials else {}

    # Accept unsaved field values submitted with the test form
    for field in ProviderClass.credential_fields():
        key = field["key"]
        val = request.POST.get(key, "").strip()
        if val and "•" not in val:
            credentials[key] = val

    if not credentials:
        return JsonResponse(
            {
                "success": False,
                "error": "No credentials found. Please enter and save credentials first.",
            },
            status=400,
        )

    # -- Instantiate provider (validates required fields) --
    try:
        provider = ProviderClass(credentials)
    except ValueError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)

    # -- Optional pre-flight auth check (MSG91 only) --
    if hasattr(provider, "validate_credentials"):
        try:
            is_valid, auth_error = provider.validate_credentials()
            if not is_valid:
                SMSLog.objects.create(
                    organization=org,
                    provider=provider_key,
                    recipient=cleaned_recipient,
                    message="[test]",
                    status="failed",
                    provider_response={"validation_error": auth_error},
                    entity_type="test",
                    entity_id="test-sms",
                )
                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            f"Credential validation failed: {auth_error}. "
                            "Check your Auth Key "
                            "(if IP security is enabled, whitelist this server's IP)."
                        ),
                    },
                    status=400,
                )
        except Exception:
            pass  # network error during pre-flight → proceed to send anyway

    # -- Build test message --
    # MSG91 DLT flows always deliver their registered template body; the message
    # text is only used for other providers and for the SMSLog record.
    test_message = "Asseto Test Alert: SMS Integration is functioning properly."

    # -- Sanitize phone via provider's own formatter --
    normalized_phone = provider.sanitize_phone(cleaned_recipient)

    # -- Send --
    user_name = (
        request.user.get_full_name()
        or request.user.first_name
        or request.user.username
        or "Administrator"
    )
    org_name = getattr(org, "name", "Asseto")

    try:
        result = provider.send(
            to=normalized_phone,
            message=test_message,
            ticket_id="TK-TEST-001",
            subject="Asseto Test Alert",
            org_name=org_name,
            extra_vars={
                "name": user_name,
                "status": "Test Active",
                "priority": "Normal",
                "event": "System Test",
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error in test_sms for provider %s", provider_key)
        return JsonResponse(
            {"success": False, "error": f"Internal error: {exc}"}, status=500
        )

    # -- Audit log --
    SMSLog.objects.create(
        organization=org,
        provider=provider_key,
        recipient=cleaned_recipient,
        message=test_message,
        status="sent" if result.success else "failed",
        provider_response=result.raw_response or {},
        entity_type="test",
        entity_id="test-sms",
    )

    if result.success:
        return JsonResponse(
            {
                "success": True,
                "message": (
                    f"Test SMS queued via {provider_key.upper()} to {cleaned_recipient}! "
                    f"Request ID: {result.message_id}. Check your phone shortly."
                ),
                "details": result.raw_response,
            }
        )

    return JsonResponse(
        {
            "success": False,
            "error": f"{provider_key.upper()} rejected the request: {result.error}.",
            "details": result.raw_response,
        },
        status=400,
    )
