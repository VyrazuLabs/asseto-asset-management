
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from common.permissions import require_any_permission
from configurations.forms import TagConfigurationForm
from configurations.models import TagConfiguration


@csrf_exempt
@require_any_permission("configurations.add_configuration", "configurations.edit_configuration")
def create_or_update_tag_configuration(request, id=None):
    # Check if we're editing an existing configuration
    instance = None
    if id:
        instance = get_object_or_404(
            TagConfiguration, pk=id, organization=request.user.organization
        )
    if request.method == "POST":
        organization = request.user.organization
        form = TagConfigurationForm(request.POST, instance=instance)

        if form.is_valid():
            config = form.save(commit=False)
            config.organization = organization
            config.save()
            return redirect("configurations:list_tag")

        return render(request, "configurations/add_tag.html", {"form": form})

    form = TagConfigurationForm(instance=instance)
    context = {
        "form": form,
        "is_update": bool(instance),
        "configurations": instance,
    }
    template_name = "configurations/add_tag.html"
    return render(request, template_name, context)


@csrf_exempt
@login_required
@permission_required("configurations.edit_configuration", raise_exception=True)
def update_tag_configuration(request, id=None):
    config = get_object_or_404(TagConfiguration, pk=id)

    if request.method == "POST":

        update_form = TagConfigurationForm(request.POST, instance=config)
        if update_form.is_valid():
            update_form.save()
            return redirect("configurations:list_tag")
    else:
        update_form = TagConfigurationForm(instance=config)

    context = {"form": update_form, "configurations": config}
    return render(request, "configurations/add_tag.html", context)


@login_required
@permission_required("configurations.view_configuration", raise_exception=True)
def list_tag_configurations(request):
    configurations = TagConfiguration.objects.filter(
        organization=request.user.organization
    ).first()
    if configurations is None:
        instance = None
        form = TagConfigurationForm(instance=instance)
        return render(
            request,
            "configurations/add_tag.html",
            {
                "form": form,
                "is_update": bool(instance),
                "configurations": instance,
                "submenu": "tag-configuration",
                "sidebar": "configurations",
            },
        )
    return render(
        request,
        "configurations/list_tag.html",
        {
            "title": "Tag Configuration",
            "configurations": configurations,
            "submenu": "tag-configuration",
            "sidebar": "configurations",
        },
    )


@login_required
@permission_required("configurations.edit_configuration", raise_exception=True)
def toggle_default_settings(request, id):
    config = get_object_or_404(
        TagConfiguration, pk=id, organization=request.user.organization
    )
    config.use_default_settings = not config.use_default_settings
    config.save()
    
    # Return the updated checkbox HTML so HTMX can swap it in-place
    checked = "checked" if config.use_default_settings else ""
    url = reverse("configurations:toggle_default_settings", args=[config.id])
    
    html = f"""<input type="checkbox" 
        id="use_default_settings_{config.id}"
        name="use_default_settings"
        class="form-check-input"
        {checked}
        hx-post="{url}"
        hx-trigger="change"
        hx-target="#use_default_settings_{config.id}"
        hx-swap="outerHTML">"""
    return HttpResponse(html)