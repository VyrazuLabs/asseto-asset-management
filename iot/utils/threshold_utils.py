from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone

from iot.forms.sensor_forms import SensorThresholdForm
from iot.models.device_models import Device
from iot.models.sensor_models import Sensor, SensorAlarm, SensorThreshold


def build_threshold_alarm_context(request, tab="alarms", threshold_form=None):
    organization = getattr(request.user, "organization", None)

    all_alarms_qs = SensorAlarm.objects.all()
    if organization:
        all_alarms_qs = all_alarms_qs.filter(sensor__organization=organization)

    active_alarms_count = all_alarms_qs.filter(status="active").count()
    acknowledged_alarms_count = all_alarms_qs.filter(status="acknowledged").count()
    resolved_alarms_count = all_alarms_qs.filter(status="resolved").count()

    active_alarms_qs = all_alarms_qs.select_related(
        "sensor", "rule", "acknowledged_by", "resolved_by", "ticket"
    ).order_by("-created_at")

    alarms_paginator = Paginator(active_alarms_qs, 10)
    alarms_page_obj = alarms_paginator.get_page(request.GET.get("alarms_page"))

    thresholds_qs = SensorThreshold.objects.all()
    if organization:
        thresholds_qs = thresholds_qs.filter(sensor__organization=organization)
    thresholds_qs = thresholds_qs.select_related("sensor", "sensor__device").order_by("-created_at")

    thresholds_paginator = Paginator(thresholds_qs, 10)
    thresholds_page_obj = thresholds_paginator.get_page(
        request.GET.get("thresholds_page")
    )

    if threshold_form is None:
        threshold_form = SensorThresholdForm(organization=organization)

    if organization:
        sensors = Sensor.undeleted_objects.filter(organization=organization)
        devices = Device.undeleted_objects.filter(organization=organization)
    else:
        sensors = Sensor.undeleted_objects.all()
        devices = Device.undeleted_objects.all()

    return {
        "title": "Threshold & Alarm Management",
        "sidebar": "iot",
        "submenu": "thresholds",
        "active_tab": tab,
        "alarms_page_obj": alarms_page_obj,
        "thresholds_page_obj": thresholds_page_obj,
        "threshold_form": threshold_form,
        "sensors": sensors,
        "devices": devices,
        "active_alarms_count": active_alarms_count,
        "acknowledged_alarms_count": acknowledged_alarms_count,
        "resolved_alarms_count": resolved_alarms_count,
    }



def create_threshold_rule(request):
    organization = getattr(request.user, "organization", None)
    form = SensorThresholdForm(request.POST, organization=organization)

    if form.is_valid():
        form.save()
        return True, None

    return False, form


def trigger_alarm_for_threshold(threshold, triggered_value):
    try:
        triggered_value = float(triggered_value)
    except (TypeError, ValueError):
        triggered_value = threshold.value

    return SensorAlarm.objects.create(
        rule=threshold,
        sensor=threshold.sensor,
        triggered_value=triggered_value,
        status="active",
    )


def acknowledge_alarm(alarm, user):
    alarm.status = "acknowledged"
    alarm.acknowledged_by = user
    alarm.acknowledged_at = timezone.now()
    alarm.save()


def resolve_alarm(alarm, user):
    alarm.status = "resolved"
    alarm.resolved_by = user
    alarm.resolved_at = timezone.now()
    alarm.save()


def update_threshold_rule(threshold, form):
    if form.is_valid():
        form.save()
        return True, None
    return False, form


def delete_threshold_rule(threshold):
    threshold.delete()
