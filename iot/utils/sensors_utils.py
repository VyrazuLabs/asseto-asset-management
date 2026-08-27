from django.db.models import QuerySet
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from common.template_pagination import create_paginated_objects
from iot.models.sensor_models import Sensor


def create_sensor_list(request, query_objects: QuerySet[Sensor]):
    search_text = (request.GET.get("search_text") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()

    if search_text:
        query_objects = query_objects.filter(
            Q(name__icontains=search_text) |
            Q(sensor_type__icontains=search_text) |
            Q(device__name__icontains=search_text)
        )

    if status_filter == "paired":
        query_objects = query_objects.filter(is_paired=True)
    elif status_filter == "unpaired":
        query_objects = query_objects.filter(is_paired=False)

    return {
        "page_object": create_paginated_objects(request, query_objects),
        "search_text": search_text,
        "selected_status": status_filter,
    }


def generate_mqtt_topic(organization_id, sensor_type):
    return f"{organization_id}/{sensor_type}"


def get_sensor_details(request, id):
    sensor = get_object_or_404(
        Sensor.undeleted_objects, pk=id, organization=request.user.organization
    )

    history_list = sensor.history.all()
    paginator = Paginator(history_list, 10, orphans=1)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    return {
        "sidebar": "iot",
        "submenu": "sensors",
        "sensor": sensor,
        "page_object": page_object,
        "title": f"Details - {sensor.name}",
    }
