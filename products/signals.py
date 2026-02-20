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
    admins = User.objects.filter(
        is_superuser=True,
        organization=instance.organization
    )
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

    history = instance.history.all()[:2]

    if len(history) < 2:
        return

    new_record = history[0]
    old_record = history[1]

    changed_fields = []

    for field in instance._meta.fields:
        field_name = field.name

        old_value = getattr(old_record, field_name, None)
        new_value = getattr(new_record, field_name, None)

        if old_value != new_value:
            changed_fields.append((field_name, old_value, new_value))
        if any(f[0] == "is_deleted" for f in changed_fields) and instance.is_deleted:
                for admin in admins:
                    NotificationService.send(
                        user=admin,
                        title="Product Deleted",
                        message=f"Product '{instance.name}' was deleted.",
                        icon="bi-box-seam",
                        link=f"/products/details/{instance.id}",
                        instance_id=instance.id,
                        object_id=str(instance.id)
                    )
        for field_name, old_value, new_value in changed_fields:
            if field_name == "is_deleted" and instance.is_deleted:
            # Make readable field name
                readable_field = field_name.replace("_", " ").title()

                for admin in admins:
                    NotificationService.send(
                        user=admin,
                        title="Product Updated",
                        message=f"{readable_field} Product Updated'.",
                        icon="bi-pencil-square",
                        link=f"/products/details/{instance.id}",
                        instance_id=instance.id,
                        object_id=str(instance.id),
                    )
                    break
            break
            
        if hasattr(instance, "_old_status") and instance._old_status != instance.status and not instance.is_deleted:
            status_text = "Activated" if instance.status else "Deactivated"

            for admin in admins:
                NotificationService.send(
                    user=admin,
                    title="Product Status Changed",
                    message=f"Product '{instance.name}' has been {status_text}.",
                    icon="bi-toggle-on",
                    link=f"/products/list",
                    object_id=str(instance.id),
                    instance_id=instance.id
                )
        other_changes = [
        field for field in changed_fields
        if field not in ["is_deleted", "status"]
    ]

    if other_changes and not instance.is_deleted:
        readable_fields = ", ".join(
            field.replace("_", " ").title()
            for field in other_changes
        )

        for admin in admins:
            NotificationService.send(
                user=admin,
                title="Product Updated",
                message=f"Updated fields: {readable_fields} for product '{instance.name}'.",
                icon="bi-pencil-square",
                link=f"/products/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )