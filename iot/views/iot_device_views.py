from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.management.utils import get_random_secret_key
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.forms import formset_factory, BaseFormSet
from iot.forms.device_forms import DeviceForm, DeviceAttachmentsForm, DeviceAttachmentsFormSet
from iot.models.device_models import Device, DeviceAttachments
from iot.utils.device_utils import add_device_attachment, get_device_details, get_sesnors_list


class BaseEditAttachmentFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop("organization", None)
        self.instances = kwargs.pop("instances", [])
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        kwargs["organization"] = self.organization
        if index is not None and index < len(self.instances):
            kwargs["instance"] = self.instances[index]
        return super()._construct_form(index, **kwargs)


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
def edit_device(request, id):
    device = get_object_or_404(Device, id=id, organization=request.user.organization)
    organization = getattr(request.user, "organization", None)

    existing_attachments = list(DeviceAttachments.objects.filter(device=device).order_by('created_at'))
    EditAttachmentFormSet = formset_factory(DeviceAttachmentsForm, formset=BaseEditAttachmentFormSet, extra=0)

    if request.method == "POST":
        device_form = DeviceForm(request.POST, instance=device, organization=organization)
        attachments_formset = EditAttachmentFormSet(
            request.POST, organization=organization, instances=existing_attachments
        )

        if device_form.is_valid() and attachments_formset.is_valid():
            device_form.save()

            kept_ids = []
            forms_data = list(zip(
                range(len(existing_attachments)),
                attachments_formset[:len(existing_attachments)]
            ))

            for idx, form in forms_data:
                if form in attachments_formset.deleted_forms:
                    continue
                if idx < len(existing_attachments):
                    att = existing_attachments[idx]
                    att.attahed_part = form.cleaned_data.get("attahed_part", "")
                    att.is_enable = form.cleaned_data.get("is_enable", False)
                    if form.cleaned_data.get("mqtt_topic"):
                        att.mqtt_topic = form.cleaned_data["mqtt_topic"]
                    att.save()
                    kept_ids.append(att.id)

            for form in attachments_formset[len(existing_attachments):]:
                cleaned_data = getattr(form, "cleaned_data", None)
                if not cleaned_data or form in attachments_formset.deleted_forms:
                    continue
                new_att = DeviceAttachments.objects.create(
                    organization=organization,
                    device=device,
                    attahed_part=cleaned_data.get("attahed_part", ""),
                    mqtt_topic=cleaned_data.get("mqtt_topic")
                    or get_random_secret_key(),
                    is_enable=cleaned_data.get("is_enable", False),
                )
                kept_ids.append(new_att.id)

            DeviceAttachments.objects.filter(device=device).exclude(id__in=kept_ids).delete()

            messages.success(request, "Device updated successfully")
            return redirect("iot:devices_list")
        else:
            print("Device Form Errors:", device_form.errors)
            print("Attachments Formset Errors:", attachments_formset.errors)
            print("Non Form Errors:", attachments_formset.non_form_errors())
    else:
        device_form = DeviceForm(instance=device, organization=organization)

        initial_data = [
            {
                "attahed_part": att.attahed_part,
                "mqtt_topic": att.mqtt_topic,
                "is_enable": att.is_enable,
            }
            for att in existing_attachments
        ]

        attachments_formset = EditAttachmentFormSet(
            initial=initial_data, organization=organization, instances=existing_attachments
        )

    return render(
        request,
        "iot_devices/edit-device.html",
        {
            "title": "Edit device",
            "device": device,
            "form": device_form,
            "attachments_formset": attachments_formset,
            "sidebar": "iot",
            "submenu": "devices",
        },
    )


@login_required()
def device_details(request, id):
    context = get_device_details(request, id)
    return render(request, "iot_devices/device-detail.html", context)

@login_required()
def paired_device(request):
    pass


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


@login_required()
def search_devices(request, page):
    """AJAX endpoint returning a paginated device table rows."""
    try:
        context = get_sesnors_list(request)
    except Exception:
        return HttpResponse(status=500)
    return render(request, "iot_devices/devices-data.html", context)
