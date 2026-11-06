import base64
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from configurations.constants import INTEGRATION_CHOICES
from configurations.forms import ClientCredentialsForm
from configurations.models import Extensions, SlackConfiguration, SMSConfiguration

from configurations.utils import hide_last_digits


@login_required
@permission_required("configurations.view_extensions", raise_exception=True)
def integration(request):
    if request.method == "POST":
        integration_type = request.POST.get("integration_type")
        form = ClientCredentialsForm(request.POST)
        if form.is_valid():
            client_id = form.cleaned_data["client_id"]
            client_secret = form.cleaned_data["client_secret"]
            # integration_type = form.cleaned_data['integration_type']
            if integration_type:  # Slack
                # Logic to save Slack credentials
                request.session["slack"] = True
            else:
                request.session["slack"] = False
            # Save logic here...
            return redirect("configurations:integration")
    elif request.method == "GET":
        form = ClientCredentialsForm()
        integration_choices = INTEGRATION_CHOICES
        slack_config = SlackConfiguration.objects.filter(user=request.user).first()
        client_id = (
            base64.b64decode(slack_config.client_id).decode() if slack_config else None
        )
        client_secret = (
            base64.b64decode(slack_config.client_secret).decode()
            if slack_config
            else None
        )
        if client_id is not None:
            client_id = hide_last_digits(client_id)
        context = {"client_id": client_id, "client_secret": client_secret}
        # On GET or other methods, you may render the form page or handle differently
        return render(request, "configurations/integrations.html", context=context)

    return render(
        request,
        "configurations/integrations.html",
        {"form": form, "integration_choices": integration_choices},
    )


@login_required
@permission_required("configurations.view_extensions", raise_exception=True)
def list_extensions(request):
    # integration_choices=INTEGRATION_CHOICES
    for choice_id, (entity_name, description) in INTEGRATION_CHOICES:
        existing_extension = Extensions.objects.filter(
            organization=request.user.organization, entity_name=entity_name
        ).first()
        if not existing_extension:
            Extensions.objects.create(
                organization=request.user.organization,
                description=description,
                entity_name=entity_name,
                status=0,  # Inactive by default
                validity=0,
            )
    get_extensions = Extensions.objects.filter(
        entity_name="Slack", organization=request.user.organization
    ).first()

    get_api_extension = Extensions.objects.filter(
        entity_name="API", organization=request.user.organization
    ).first()

    get_sms_extension = Extensions.objects.filter(
        entity_name="SMS", organization=request.user.organization
    ).first()

    active_sms_config = SMSConfiguration.objects.filter(
        organization=request.user.organization, is_active=True
    ).first()

    if get_extensions:
        request.session["slack"] = True
    else:
        request.session["slack"] = False
    return render(
        request,
        "configurations/list-extensions.html",
        {
            "integration_choices": get_extensions,
            "api_extension": get_api_extension,
            "sms_extension": get_sms_extension,
            "active_sms_config": active_sms_config,
        },
    )


@login_required
@permission_required("configurations.edit_configuration", raise_exception=True)
def extension_status(request, id):
    is_ajax = (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or request.headers.get("HX-Request") == "true"
    )
    status = request.POST.get("status", "off")  # will be "on" or "off"

    ext = Extensions.objects.filter(id=id).first()
    if not ext:
        if is_ajax:
            return JsonResponse({"success": False, "error": "Extension not found."}, status=404)
        messages.error(request, "Extension not found.")
        return redirect("configurations:list_extensions")

    new_status = 1 if status == "on" else 0

    if ext.entity_name == "SMS":
        if new_status == 1:
            # Check if an SMS provider is configured with required credentials
            active_conf = SMSConfiguration.objects.filter(
                organization=request.user.organization, is_active=True
            ).first()

            if not active_conf:
                # Find any provider that has credentials configured
                configured_conf = None
                for cfg in SMSConfiguration.objects.filter(organization=request.user.organization):
                    creds = cfg.credentials or {}
                    if cfg.provider == "msg91" and creds.get("auth_key") and creds.get("template_id"):
                        configured_conf = cfg
                        break
                    elif cfg.provider == "twilio" and creds.get("account_sid") and creds.get("auth_token"):
                        configured_conf = cfg
                        break

                if not configured_conf:
                    err_msg = "Cannot enable SMS: Please configure SMS provider credentials first."
                    if is_ajax:
                        return JsonResponse({"success": False, "error": err_msg, "status": 0}, status=400)
                    messages.error(request, err_msg)
                    return redirect("configurations:list_extensions")

                # Activate the configured provider
                SMSConfiguration.objects.filter(
                    organization=request.user.organization
                ).exclude(pk=configured_conf.pk).update(is_active=False)
                configured_conf.is_active = True
                configured_conf.save()
                active_conf = configured_conf

            ext.status = 1
            ext.save()
            msg = f"SMS service enabled via {active_conf.provider.upper()}. Automated notifications will now be sent."
            if is_ajax:
                return JsonResponse({"success": True, "status": 1, "message": msg})
            messages.success(request, msg)
            return redirect("configurations:list_extensions")

        else:
            # Disabling SMS
            ext.status = 0
            ext.save()
            SMSConfiguration.objects.filter(
                organization=request.user.organization
            ).update(is_active=False)
            msg = "SMS service disabled. Automated notifications have stopped."
            if is_ajax:
                return JsonResponse({"success": True, "status": 0, "message": msg})
            messages.success(request, msg)
            return redirect("configurations:list_extensions")

    else:
        # Default behavior for other extensions (e.g. Slack)
        ext.status = new_status
        ext.save()
        if is_ajax:
            return JsonResponse({"success": True, "status": new_status})
        return redirect("configurations:list_extensions")


@login_required
@permission_required("configurations.edit_configuration", raise_exception=True)
def save_slack_configuration(request):
    if request.method == "POST":
        client_id = request.POST.get("client_id", "").strip()
        client_secret = request.POST.get("client_secret", "").strip()
        client_id = base64.b64encode(client_id.encode()).decode()
        client_secret = base64.b64encode(client_secret.encode()).decode()
        # Encode client_id and client_secret in base64

        slack_config, created = SlackConfiguration.objects.get_or_create(
            user=request.user
        )
        slack_config.client_id = client_id
        slack_config.client_secret = client_secret
        slack_config.save()
        # Redirect or render success message as needed
        return redirect("configurations:integration")
    if request.method == "GET":
        slack_config = SlackConfiguration.objects.filter(user=request.user).first()
        client_id = base64.b64decode(slack_config.client_id).decode()
        client_secret = base64.b64decode(slack_config.client_secret).decode()
        context = {"client_id": client_id, "client_secret": client_secret}
        # On GET or other methods, you may render the form page or handle differently
        return redirect("configurations:integration")

@login_required
@permission_required("configurations.edit_configuration", raise_exception=True)
def api_extension_status(request, id):
    status = request.POST.get("api_status", "off")
    ext = get_object_or_404(Extensions, pk=id)
    ext.status = 1 if status == "on" else 0
    ext.save()
    return redirect("configurations:list_extensions")