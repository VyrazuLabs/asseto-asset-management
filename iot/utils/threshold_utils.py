import logging
import threading
import time

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone

from iot.forms.sensor_forms import SensorThresholdForm
from iot.models.device_models import Device
from iot.models.sensor_models import Sensor, SensorAlarm, SensorThreshold

logger = logging.getLogger(__name__)

COOLDOWN_SECONDS = 5 * 60   # repeat alarm every 5 minutes while threshold is breached


def _eval_operator(operator: str, reading: float, threshold_value: float) -> bool:
    """Return True when the reading satisfies the threshold operator."""
    return {
        "gt":  reading >  threshold_value,
        "lt":  reading <  threshold_value,
        "eq":  reading == threshold_value,
        "neq": reading != threshold_value,
    }.get(operator, False)


class _AlarmEngine:
    """
    Tracks per-(sensor, threshold) breach states and fires SensorAlarm objects.
    - Fires immediately on first breach.
    - Repeats every 5 minutes (COOLDOWN_SECONDS) as long as it remains breached.
    - Resets once reading drops back within threshold.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._last_alarm_at: dict[tuple, float] = {}

    def evaluate(self, sensor_id: str, reading: float) -> None:
        try:
            thresholds = list(
                SensorThreshold.objects.filter(sensor_id=sensor_id).select_related("sensor")
            )
        except Exception as exc:
            logger.warning("[AlarmEngine] Could not load thresholds for %s: %s", sensor_id, exc)
            return

        now = time.monotonic()

        for threshold in thresholds:
            key = (sensor_id, threshold.pk)
            breaching = _eval_operator(threshold.operator, reading, threshold.value)

            with self._lock:
                if breaching:
                    # Seed last_alarm_at from DB on first encounter (survives restarts)
                    if key not in self._last_alarm_at:
                        self._last_alarm_at[key] = self._fetch_last_alarm_monotonic(
                            sensor_id, threshold.pk, now
                        )

                    last_alarm = self._last_alarm_at[key]
                    time_since_last = now - last_alarm

                    # Fire immediately on first breach (last_alarm is 0 or >= 5 min ago),
                    # and repeat every 5 minutes while it remains breached.
                    if time_since_last >= COOLDOWN_SECONDS:
                        self._last_alarm_at[key] = now
                        should_fire = True
                    else:
                        should_fire = False
                else:
                    # Reading went back to normal — reset so the next breach triggers immediately
                    if key in self._last_alarm_at:
                        logger.debug(
                            "[AlarmEngine] Sensor recovered below threshold — resetting: sensor=%s threshold=%s",
                            sensor_id, threshold.pk,
                        )
                        self._last_alarm_at.pop(key, None)
                    should_fire = False

            if should_fire:
                self._fire(threshold, reading)

    def _fetch_last_alarm_monotonic(self, sensor_id: str, threshold_pk: int, now: float) -> float:
        """
        Look up the most recent SensorAlarm for this (sensor, threshold) pair
        and convert its created_at into an equivalent monotonic time so it can
        be compared against time.monotonic().

        Returns 0 if no previous alarm exists.
        """
        try:
            last = (
                SensorAlarm.objects.filter(sensor_id=sensor_id, rule_id=threshold_pk)
                .order_by("-created_at")
                .values("created_at")
                .first()
            )
            if last and last["created_at"]:
                import datetime
                db_time = last["created_at"]
                # How many seconds ago was that alarm (wall-clock)?
                wall_now = timezone.now()
                seconds_ago = (wall_now - db_time).total_seconds()
                # Map onto monotonic timeline: now - seconds_ago
                return max(0.0, now - seconds_ago)
        except Exception as exc:
            logger.warning("[AlarmEngine] Could not fetch last alarm time: %s", exc)
        return 0.0

    def _fire(self, threshold: "SensorThreshold", reading: float) -> None:
        
        try:
            alarm = SensorAlarm.objects.create(
                rule=threshold,
                sensor=threshold.sensor,
                triggered_value=reading,
                status="active",
            )
            logger.info(
                " Alarm created — sensor=%s threshold=%s reading=%.2f alarm_id=%s",
                threshold.sensor_id, threshold.pk, reading, alarm.pk,
            )
        except Exception as exc:
            logger.error("[AlarmEngine] Failed to create alarm: %s", exc)


# Module-level singleton — import and call .evaluate() from anywhere
alarm_engine = _AlarmEngine()


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
    """
    Legacy direct-trigger — kept for compatibility but prefer alarm_engine.evaluate().
    Creates an alarm immediately without persistence/cooldown checks.
    """
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
