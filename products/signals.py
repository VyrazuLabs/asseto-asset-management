# products/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Product
from notifications.service import NotificationService

User = get_user_model()

@receiver(pre_save, sender=Product)
def store_previous_product_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            instance._old_name = old_instance.name
            instance._old_status = old_instance.status
        except Product.DoesNotExist:
            instance._old_name = None
            instance._old_status = None
    else:
        instance._old_name = None
        instance._old_status = None

@receiver(post_save, sender=Product)
def product_notification(sender, instance, created, **kwargs):
    # Get organization admins
    admins = User.objects.filter(
        is_superuser=True,
        organization=instance.organization
    )

    # PRODUCT CREATED
    if created:
        for admin in admins:
            NotificationService.send(
                user=admin,
                title="Product Created",
                message=f"Product '{instance.name}' has been created.",
                icon="bi-box-seam",
                link=f"/products/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
        return

    #PRODUCT UPDATED (Name Changed)
    if hasattr(instance, "_old_name") and instance._old_name != instance.name:
        for admin in admins:
            NotificationService.send(
                user=admin,
                title="Product Updated",
                message=f"Product name changed from '{instance._old_name}' to '{instance.name}'.",
                icon="bi-pencil-square",
                link=f"/products/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id)
            )

    #PRODUCT STATUS CHANGED
    if hasattr(instance, "_old_status") and instance._old_status != instance.status:
        status_text = "Activated" if instance.status else "Deactivated"

        for admin in admins:
            NotificationService.send(
                user=admin,
                title="Product Status Changed",
                message=f"Product '{instance.name}' has been {status_text}.",
                icon="bi-toggle-on",
                link=f"/products/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
