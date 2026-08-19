from django import forms
from iot.constants import UNIT_MAPPER
from iot.models.device_models import Device
from iot.models.sensor_models import Sensor, SensorThreshold


class SensorForm(forms.ModelForm):
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter Sensor Name",
                "autocomplete": "off",
            }
        ),
    )
    device = forms.ModelChoiceField(
        queryset=Device.undeleted_objects.none(),
        required=True,
        empty_label="-- Select Device --",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )
    sensor_type = forms.ChoiceField(
        required=True,
        choices=Sensor.SensorType.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )
    unit = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "data-unit-select": "",
            }
        ),
    )
    mqtt_topic = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Auto-generated or enter MQTT Topic",
                "autocomplete": "off",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop("organization", None)
        if not self._organization and len(args) > 1 and not isinstance(args[1], dict):
            args_list = list(args)
            self._organization = args_list.pop(1)
            args = tuple(args_list)

        super().__init__(*args, **kwargs)

        if self._organization:
            self.fields["device"].queryset = Device.undeleted_objects.filter(
                organization=self._organization
            )
        else:
            self.fields["device"].queryset = Device.undeleted_objects.all()

        initial_type = self.initial.get("sensor_type") or self.data.get(
            "sensor_type"
        )
        self.fields["unit"].choices = [
            (unit, unit) for unit in UNIT_MAPPER.get(initial_type, [])
        ]

    class Meta:
        model = Sensor
        fields = [
            "name",
            "device",
            "sensor_type",
            "unit",
            "mqtt_topic",
        ]


class SensorThresholdForm(forms.ModelForm):
    operator = forms.ChoiceField(
        required=True,
        choices=SensorThreshold.OPERATOR_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )
    value = forms.FloatField(
        required=True,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter Threshold Value",
                "step": "any",
            }
        ),
    )
    severity = forms.ChoiceField(
        required=True,
        choices=SensorThreshold.SEVERITY_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    class Meta:
        model = SensorThreshold
        fields = [
            "operator",
            "value",
            "severity",
        ]
