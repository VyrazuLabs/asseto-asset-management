from django.db.models import QuerySet
from common.template_pagination import create_paginated_objects
from iot.models.sensor_models import Sensor


def create_sensor_list(request, query_objects: QuerySet[Sensor]):
    return {
        "page_object": create_paginated_objects(request, query_objects)
    }

def generate_mqtt_topic(organization_id,sensor_type):
    return f"{organization_id}/{sensor_type}"