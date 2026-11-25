from uuid import UUID

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404

from common.template_pagination import create_paginated_objects
from dashboard.models import Organization
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
            mqtt_topic=cleaned_data.get("mqtt_topic"),
            is_enable=cleaned_data.get("is_enable", False),
        )
        attachment.save()


def get_sesnors_list(request):
    try:
        from assets.models import AssetImage

        organization = getattr(request.user, "organization", None)
        search_text = (request.GET.get("search_text") or "").strip()
        status_filter = (request.GET.get("status") or "").strip()

        query_objects = Device.undeleted_objects.values(
            "id", "name", "asset__name", "asset_id", "is_paired", "created_at"
        ).order_by("-created_at")

        if organization:
            query_objects = query_objects.filter(organization=organization)

        if search_text:
            id_query = Q()
            try:
                id_query = Q(id=UUID(search_text))
            except (ValueError, TypeError):
                pass
            query_objects = query_objects.filter(
                Q(name__icontains=search_text)
                | Q(asset__name__icontains=search_text)
                | id_query
            )

        if status_filter == "paired":
            query_objects = query_objects.filter(is_paired=Device.PairingChoice.PAIRED)
        elif status_filter == "unpaired":
            query_objects = query_objects.filter(
                is_paired=Device.PairingChoice.UNPAIRED
            )

        page_object = create_paginated_objects(request, query_objects)
        for device in page_object:
            device["device_id"] = device["id"].hex

        asset_ids = [d["asset_id"] for d in page_object if d.get("asset_id")]
        images_qs = AssetImage.objects.filter(asset_id__in=asset_ids).order_by(
            "-uploaded_at"
        )

        asset_images = {}
        for img in images_qs:
            if img.asset_id not in asset_images:
                asset_images[img.asset_id] = img

        return {
            "page_object": page_object,
            "search_text": search_text,
            "selected_status": status_filter,
            "asset_images": asset_images,
        }
    except Exception:
        return Exception


def get_device_details(request, id):
    device = get_object_or_404(
        Device.undeleted_objects, pk=id, organization=request.user.organization
    )
    attachments = device.device_attachments.all().order_by("created_at")

    history_list = device.history.all()
    paginator = Paginator(history_list, 10, orphans=1)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    return {
        "sidebar": "devices",
        "device_id": device.id.hex,
        "device": device,
        "attachments": attachments,
        "page_object": page_object,
        "title": f"Details - {device.name}",
    }
