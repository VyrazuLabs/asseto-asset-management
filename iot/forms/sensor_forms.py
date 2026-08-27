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
    # Non-model field: used to cascade Device → Sensor in the UI
    device = forms.ModelChoiceField(
        queryset=Device.undeleted_objects.none(),
        required=False,
        empty_label="-- Select Device --",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_threshold_device",
            }
        ),
    )
    sensor = forms.ModelChoiceField(
        queryset=Sensor.undeleted_objects.none(),
        required=True,
        empty_label="-- Select Sensor --",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_threshold_sensor",
            }
        ),
    )
    alert_type = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Overheating Detected",
                "autocomplete": "off",
            }
        ),
    )
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

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)

        # Build device queryset
        if self._organization:
            device_qs = Device.undeleted_objects.filter(organization=self._organization)
        else:
            device_qs = Device.undeleted_objects.all()
        self.fields["device"].queryset = device_qs

        # Determine selected device from POST data or instance
        selected_device_id = None
        if self.data.get("device"):
            selected_device_id = self.data.get("device")
        elif self.instance and self.instance.pk:
            selected_device_id = self.instance.sensor.device_id if self.instance.sensor_id else None

        # Build sensor queryset filtered by device
        if selected_device_id:
            sensor_qs = Sensor.undeleted_objects.filter(device_id=selected_device_id)
            if self._organization:
                sensor_qs = sensor_qs.filter(organization=self._organization)
        elif self._organization:
            sensor_qs = Sensor.undeleted_objects.filter(organization=self._organization)
        else:
            sensor_qs = Sensor.undeleted_objects.all()
        self.fields["sensor"].queryset = sensor_qs

        # Pre-select device when editing an existing threshold
        if self.instance and self.instance.pk and self.instance.sensor_id:
            self.fields["device"].initial = self.instance.sensor.device_id

    class Meta:
        model = SensorThreshold
        fields = [
            "sensor",
            "alert_type",
            "operator",
            "value",
            "severity",
        ]

