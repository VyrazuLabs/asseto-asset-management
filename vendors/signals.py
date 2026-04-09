# vendors/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Vendor
from notifications.service import NotificationService

User = get_user_model()

@receiver(pre_save, sender=Vendor)
def store_previous_vendor_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Vendor.objects.get(pk=instance.pk)
            instance._old_name = old_instance.name
            instance._old_status = old_instance.status
        except Vendor.DoesNotExist:
            instance._old_name = None
            instance._old_status = None
    else:
        instance._old_name = None
        instance._old_status = None
        
@receiver(post_save, sender=Vendor)
def vendor_notification(sender, instance, created, **kwargs):

    # Get organization admins
    admins = User.objects.filter(
        is_superuser=True,
        organization=instance.organization
    )

    #Vendor Created
    if created:
        for admin in admins:
            NotificationService.send(
                user=admin,
                title="Vendor Created",
                message=f"Vendor '{instance.name}' has been created.",
                icon="bi-building",
                link=f"/vendors/details/{instance.id}",
                object_id=str(instance.id),
                instance_id=instance.id
            )

    #Vendor Updated
    else:
        if hasattr(instance, "_old_name") and instance._old_name != instance.name:
            for admin in admins:
                NotificationService.send(
                    user=admin,
                    title="Vendor Updated",
                    message=f"Vendor name changed from '{instance._old_name}' to '{instance.name}'.",
                    icon="bi-pencil-square",
                    link=f"/vendors/details/{instance.id}",
                    instance_id=instance.id,
                    object_id=str(instance.id),
                )

        # 🔹 Vendor Status Changed
        if hasattr(instance, "_old_status") and instance._old_status != instance.status and not instance.is_deleted:
            status_text = "Activated" if instance.status else "Deactivated"

            for admin in admins:
                NotificationService.send(
                    user=admin,
                    title="Vendor Status Changed",
                    message=f"Vendor '{instance.name}' has been {status_text}.",
                    icon="bi-toggle-on",
                    link=f"/vendors/details/{instance.id}",
                    object_id=str(instance.id),
                    instance_id=instance.id
                )

        if hasattr(instance,"_old_status") and instance.is_deleted:
            for admin in admins:
                NotificationService.send(
                    user=admin,
                    title="Vendor Deleted",
                    message=f"Vendor '{instance.name}' has been Deleted.",
                    icon="bi-toggle-on",
                    link=f"/vendors/list",
                    object_id=str(instance.id),
                    instance_id=instance.id
                )