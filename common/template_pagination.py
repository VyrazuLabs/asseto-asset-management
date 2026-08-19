from django.core.paginator import Paginator
from django.db.models import QuerySet

from iot.models.sensor_models import Sensor


def create_paginated_objects(request, query_objects: QuerySet[Sensor]):
    PAGE_SIZE = 10
    ORPHANS = 1

    paginator = Paginator(query_objects, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    return page_object
