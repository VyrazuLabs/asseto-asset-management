from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from iot.forms.sensor_forms import SensorThresholdForm
from iot.models.device_models import Device
from iot.models.sensor_models import Sensor, SensorAlarm, SensorThreshold
from iot.utils.threshold_utils import (
    acknowledge_alarm as _acknowledge_alarm,
    build_threshold_alarm_context,
    create_threshold_rule as _create_threshold_rule,
    delete_threshold_rule as _delete_threshold_rule,
    resolve_alarm as _resolve_alarm,
    trigger_alarm_for_threshold,
    update_threshold_rule as _update_threshold_rule,
)


@login_required()
def threshold_alarm_management(request):
    tab = request.GET.get("tab", "alarms")
    return render(
        request,
        "threshold/threshold-alarms.html",
        build_threshold_alarm_context(request, tab),
    )


@login_required()
def create_threshold_rule(request):
    if request.method != "POST":
        return redirect("iot:threshold_alarms")

    success, form = _create_threshold_rule(request)
    if success:
        messages.success(request, "Threshold rule created successfully")
        return redirect("/iot/thresholds-alarms/?tab=rules")

    messages.error(request, "Failed to create threshold rule. Please fix the errors below.")
    ctx = build_threshold_alarm_context(request, tab="rules", threshold_form=form)
    return render(request, "threshold/threshold-alarms.html", ctx)


@login_required()
def trigger_alarm(request, threshold_id):
    if request.method != "POST":
        return redirect("iot:threshold_alarms")

    threshold = get_object_or_404(SensorThreshold, pk=threshold_id)
    triggered_value = request.POST.get("triggered_value", threshold.value)

    trigger_alarm_for_threshold(threshold, triggered_value)

    messages.success(request, f"Alarm triggered for {threshold.sensor.name}")
    return redirect("/iot/thresholds-alarms/?tab=alarms")


@login_required()
def ack_alarm(request, alarm_id):
    if request.method != "POST":
        return redirect("iot:threshold_alarms")

    alarm = get_object_or_404(SensorAlarm, pk=alarm_id)
    _acknowledge_alarm(alarm, request.user)

    messages.success(request, "Alarm acknowledged")
    return redirect("iot:threshold_alarms")


@login_required()
def resolve_alarm(request, alarm_id):
    if request.method != "POST":
        return redirect("iot:threshold_alarms")

    alarm = get_object_or_404(SensorAlarm, pk=alarm_id)
    _resolve_alarm(alarm, request.user)

    messages.success(request, "Alarm resolved")
    return redirect("iot:threshold_alarms")


@login_required()
def update_threshold_rule(request, threshold_id):
    if request.method != "POST":
        return redirect("iot:threshold_alarms")

    threshold = get_object_or_404(SensorThreshold, pk=threshold_id)
    organization = getattr(request.user, "organization", None)

    form = SensorThresholdForm(
        request.POST, instance=threshold, organization=organization
    )

    success, result = _update_threshold_rule(threshold, form)
    if success:
        messages.success(request, "Threshold rule updated successfully")
        return redirect("/iot/thresholds-alarms/?tab=rules")

    error_msg = "; ".join(
        f"{form.fields[field].label or field}: {', '.join(errs)}"
        for field, errs in result.errors.items()
    ) or "Failed to update threshold rule."
    messages.error(request, error_msg)
    return redirect("iot:threshold_alarms")


@login_required()
def delete_threshold_rule(request, threshold_id):
    if request.method != "POST":
        return redirect("iot:threshold_alarms")

    threshold = get_object_or_404(SensorThreshold, pk=threshold_id)
    _delete_threshold_rule(threshold)
    messages.success(request, "Threshold rule deleted successfully")
    return redirect("/iot/thresholds-alarms/?tab=rules")


@login_required()
def sensors_by_device(request, device_id):
    """Return JSON list of sensors belonging to a device (for cascading dropdown)."""
    organization = getattr(request.user, "organization", None)
    qs = Sensor.undeleted_objects.filter(device_id=device_id)
    if organization:
        qs = qs.filter(organization=organization)
    data = [{"id": str(s.id), "name": s.name, "unit": s.unit} for s in qs]
    return JsonResponse({"sensors": data})
