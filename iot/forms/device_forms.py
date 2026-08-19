from django import forms
from django.forms import BaseFormSet, formset_factory

from assets.models import Asset
from iot.models.device_models import Device, DeviceAttachments


class DeviceForm(forms.ModelForm):
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter Device Name",
                "autocomplete": "off",
            }
        ),
    )
    device_sn = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter Device Serial Number",
                "autocomplete": "off",
            }
        ),
    )
    asset = forms.ModelChoiceField(
        queryset=Asset.undeleted_objects.none(),
        required=False,
        empty_label="-- Select Asset --",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        if not organization and len(args) > 1 and not isinstance(args[1], dict):
            args_list = list(args)
            organization = args_list.pop(1)
            args = tuple(args_list)

        super().__init__(*args, **kwargs)

        if organization:
            self.fields["asset"].queryset = Asset.undeleted_objects.filter(
                organization=organization
            )
        else:
            self.fields["asset"].queryset = Asset.undeleted_objects.all()

    class Meta:
        model = Device
        fields = [
            "name",
            "device_sn",
            "asset",
        ]

class DeviceAttachmentsForm(forms.ModelForm):
    attahed_part = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter Attached Part",
                "autocomplete": "off",
            }
        ),
    )
    mqtt_topic = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Auto-generated if blank",
                "autocomplete": "off",
            }
        ),
    )
    is_enable = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        if not organization and len(args) > 1 and not isinstance(args[1], dict):
            args_list = list(args)
            organization = args_list.pop(1)
            args = tuple(args_list)

        super().__init__(*args, **kwargs)

    class Meta:
        model = DeviceAttachments
        fields = [
            "attahed_part",
            "mqtt_topic",
            "is_enable",
        ]


class BaseDeviceAttachmentsFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, index, **kwargs):
        kwargs["organization"] = self.organization
        return super()._construct_form(index, **kwargs)


DeviceAttachmentsFormSet = formset_factory(
    DeviceAttachmentsForm,
    formset=BaseDeviceAttachmentsFormSet,
    extra=1,
)