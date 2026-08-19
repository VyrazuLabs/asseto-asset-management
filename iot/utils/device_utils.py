from common.template_pagination import create_paginated_objects
from dashboard.models import Organization
from iot.helpers.device_helpers import generate_topic
from iot.models.device_models import Device, DeviceAttachments


def add_device_attachment(
    organization: Organization, device: Device, attachments_formset
):
    for attachment_form in attachments_formset:
        cleaned_data = getattr(attachment_form, "cleaned_data", None)
        if not cleaned_data:
            continue

        attachment = DeviceAttachments(
            organization=organization,
            device=device,
            attahed_part=cleaned_data["attahed_part"],
            mqtt_topic=cleaned_data.get("mqtt_topic")
            or generate_topic(organization.id, cleaned_data["attahed_part"]),
            is_enable=cleaned_data.get("is_enable", False),
        )
        attachment.save()

def get_sesnors_list(request):
    try:
        organization = getattr(request.user, "organization", None)
        query_objects = Device.undeleted_objects.values(
            "id", "name", "device_sn", "asset__name", "is_paired", "created_at"
        ).order_by("-created_at")

        if organization:
            query_objects = query_objects.filter(organization=organization)

        return {"page_object": create_paginated_objects(request, query_objects)}
    except Exception:
        return Exception
