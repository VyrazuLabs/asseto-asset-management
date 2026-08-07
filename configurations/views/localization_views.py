from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from configurations.models import LocalizationConfiguration

from ..constants import (ACTIVE_LANGUAGES, COUNTRY_CHOICES, CURRENCY_CHOICES,
                         DATETIME_CHOICES, DEFAULT_COUNTRY, NAME_FORMATS)


@login_required
def list_localizations(request):
    configurations = LocalizationConfiguration.objects.filter(
        organization=request.user.organization
    ).first()
    get_default_language = {"name": "English"}
    get_default_name_display_format = {}
    get_default_time_format = {}
    get_default_currency_format = {}
    get_default_country_format = {}
    if configurations:
        for id, name in ACTIVE_LANGUAGES:
            if id == configurations.default_language:
                get_default_language = {"name": name, "id": id}
        for id, name in NAME_FORMATS:
            if id == configurations.name_display_format:
                get_default_name_display_format = {"name": name, "id": id}
        for id, name in DATETIME_CHOICES:
            if id == configurations.time_format:
                get_default_time_format = {"name": name, "id": id}
        for id, name in CURRENCY_CHOICES:
            if id == configurations.currency:
                get_default_currency_format = {"name": name, "id": id}
    else:
        get_default_language = {"name": "English", "id": 0}
        get_default_name_display_format = {"name": "{first} {last}", "id": 0}
        get_default_time_format = {"name": "YYYY-MM-DD", "id": 0}
        get_default_currency_format = {"name": "INR", "id": 6}
        get_default_country_format = {"name": "India", "id": 0}
    return render(
        request,
        "configurations/list_localization.html",
        {
            "title": "Localization",
            "configurations": configurations,
            "country_choices": COUNTRY_CHOICES,
            "currency_choices": CURRENCY_CHOICES,
            "name_display_format": NAME_FORMATS,
            "default_language": ACTIVE_LANGUAGES,
            "datetime_choices": DATETIME_CHOICES,
            "default_country": DEFAULT_COUNTRY,
            "get_default_language": get_default_language,
            "get_default_name_display_format": get_default_name_display_format,
            "get_default_time_format": get_default_time_format,
            "get_default_currency_format": get_default_currency_format,
            "get_default_country_format": get_default_country_format,
            "submenu": "localization",
            "sidebar": "configurations",
        },
    )


@login_required
def create_localization_configuration(request):
    get_obj = LocalizationConfiguration.objects.filter(
        organization=request.user.organization
    ).first()
    if request.method == "POST":
        country_format = request.POST.get("country-format")
        currency_format = request.POST.get("currency-format")
        name_display_format = request.POST.get("name-format")
        default_language = request.POST.get("language-format")
        time_format = request.POST.get("time-format")

        if get_obj:
            # Update existing configuration
            get_obj.country_format = country_format
            get_obj.currency = currency_format
            get_obj.name_display_format = name_display_format
            get_obj.default_language = default_language
            get_obj.time_format = time_format
            get_obj.save()
        else:
            # Create new configuration
            LocalizationConfiguration.objects.create(
                organization=request.user.organization,
                country_format=country_format,
                currency=currency_format,
                name_display_format=name_display_format,
                default_language=default_language,
                time_format=time_format,
            )
        if "org_lang_id" in request.session:
            del request.session["org_lang_id"]
        return redirect("configurations:list_localization")

    return redirect("configurations:list_localization")