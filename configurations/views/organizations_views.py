from configurations.constants import CURRENCY_CHOICES
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

from dashboard.models import Organization


@login_required
# Was "dashboard.delete_location" — an unrelated leftover codename that
# happened to still resolve after the Phase 2 app_label migration; this view
# manages the organization settings page, so it belongs on Configurations.
@permission_required("configurations.edit_configuration", raise_exception=True)
def add_organization(request):
    if request.method == "POST":
        name = request.POST.get("organization_name")
        website = request.POST.get("organization_website")
        email = request.POST.get("organization_email")
        currency = request.POST.get("currency-format")
        phone = request.POST.get("organization_phone")

        get_organization = request.user.organization
        if get_organization is not None:
            Organization.objects.filter(id=get_organization.id).update(
                name=name, website=website, email=email, currency=currency, phone=phone
            )
            messages.success(request, "Organization Updated successfully")
        else:
            new_org = Organization.objects.create(
                name=name, website=website, email=email, currency=currency, phone=phone
            )
            request.user.organization = new_org
            request.user.save()
            messages.success(request, "Organization added successfully")

        return redirect("configurations:add_organization")

    elif request.method == "GET":
        get_user_organization = request.user.organization
        currency = ""
        if get_user_organization:
            get_org_data = Organization.objects.filter(
                id=get_user_organization.id
            ).first()
            if get_org_data:
                currency = get_org_data.get_currency_display_value()
        else:
            get_org_data = None
        return render(
            request,
            "configurations/add_organization.html",
            context={
                "title":"Add organization",
                "org_data": get_org_data,
                "currency": currency,
                "currency_choices": CURRENCY_CHOICES,
                "submenu": "organization",
                "sidebar": "configurations",
            },
        )