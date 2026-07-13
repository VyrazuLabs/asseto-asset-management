import base64
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from configurations.constants import INTEGRATION_CHOICES
from configurations.forms import ClientCredentialsForm
from configurations.models import Extensions, SlackConfiguration

from configurations.utils import hide_last_digits


@login_required
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
    if get_extensions:
        request.session["slack"] = True
    else:
        request.session["slack"] = False
    return render(
        request,
        "configurations/list-extensions.html",
        {"integration_choices": get_extensions, "api_extension": get_api_extension},
    )


@login_required
def extension_status(request, id):
    status = request.POST.get("status", "off")  # will be "on" or "off"

    ext = Extensions.objects.filter(id=id).first()
    ext.status = 1 if status == "on" else 0
    ext.save()

    return redirect("configurations:list_extensions")


@login_required
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
def api_extension_status(request, id):
    status = request.POST.get("api_status", "off")
    ext = get_object_or_404(Extensions, pk=id)
    ext.status = 1 if status == "on" else 0
    ext.save()
    return redirect("configurations:list_extensions")