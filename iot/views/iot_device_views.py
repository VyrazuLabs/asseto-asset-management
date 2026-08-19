from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.management.utils import get_random_secret_key
from django.shortcuts import redirect, render
from iot.forms.device_forms import DeviceAttachmentsFormSet, DeviceForm
from iot.utils.device_utils import add_device_attachment, get_sesnors_list


@login_required()
def add_device(request):
    organization = getattr(request.user, "organization", None)
    if request.method == "POST":
        device_form = DeviceForm(request.POST, organization=organization)
        attachments_formset = DeviceAttachmentsFormSet(
            request.POST, organization=organization
        )

        if device_form.is_valid() and attachments_formset.is_valid():
            device = device_form.save(commit=False)
            device.organization = organization
            device.device_token = get_random_secret_key()
            device.save()

            add_device_attachment(organization, device, attachments_formset)

            messages.success(request, "Device added successfully")
            return redirect("iot:devices_list")
    else:
        device_form = DeviceForm(organization=organization)
        attachments_formset = DeviceAttachmentsFormSet(organization=organization)

    return render(
        request,
        "iot_devices/add-device.html",
        {
            "title": "Add device",
            "form": device_form,
            "attachments_formset": attachments_formset,
            "sidebar": "iot",
            "submenu": "devices",
        },
    )


@login_required()
def devices_list(request):
    try:
        context: dict = get_sesnors_list(request)
        context["title"] = "Device list"
        context["sidebar"] = "iot"
        context["submenu"] = "devices"
        return render(request, "iot_devices/devices-list.html", context=context)
    except Exception as e:
        print(e)
        return render(
            request, "iot_devices/devices-list.html", context={"page_object": []}
        )


def device_details(request):
    pass

@login_required()
def paired_device(request):
    pass