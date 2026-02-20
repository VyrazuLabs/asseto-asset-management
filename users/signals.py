from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from notifications.models import Notification, UserNotification  # adjust if needed
from notifications.service import NotificationService
User = get_user_model()

@receiver(pre_save, sender=User)
def store_old_user_instance(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_instance = None

@receiver(post_save, sender=User)
def notify_user_changes(sender, instance, created, **kwargs):

    if instance.is_superuser:
        return

    admins = User.objects.filter(
        is_superuser=True,
        organization=instance.organization
    )


    if created:
        for admin in admins:
            NotificationService.send(
                user=admin,
                title="User Created",
                message=f"User '{instance.full_name}' has been created.",
                icon="bi-person-plus-fill",
                link="/users/list",
                instance_id=instance.id,
                object_id=str(instance.id)
            )
        return

    old_instance = getattr(instance, "_old_instance", None)

    if not old_instance:
        return

    changed_fields = []

    for field in instance._meta.fields:
        field_name = field.name

        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(instance, field_name, None)

        # Handle FK fields
        if field.is_relation and field.many_to_one:
            old_value = str(old_value) if old_value else None
            new_value = str(new_value) if new_value else None

        if old_value != new_value:
            changed_fields.append((field_name, old_value, new_value))

    if not changed_fields:
        return

    for admin in admins:

        if any(f[0] == "is_deleted" for f in changed_fields) and instance.is_deleted:
            NotificationService.send(
                user=admin,
                title="User Deleted",
                message=f"User '{instance.full_name}' was deleted.",
                icon="bi-person-dash-fill",
                link="/users/list",
                instance_id=instance.id,
                object_id=str(instance.id)
            )
            continue

        # Activation change
        if any(f[0] == "is_active" for f in changed_fields):
            if instance.is_deleted:
                break  # Skip if user is deleted, as deletion notification will be sent
            status_text = "Activated" if instance.is_active else "Deactivated"
            NotificationService.send(
                user=admin,
                title=f"User {status_text}",
                message=f"User '{instance.full_name}' has been {status_text.lower()}.",
                icon="bi-person-check-fill" if instance.is_active else "bi-person-x-fill",
                link="/users/list",
                instance_id=instance.id,
                object_id=str(instance.id)
            )
            continue

        # General update
        changes_text = ", ".join(
            f"{f[0].replace('_', ' ').title()}: '{f[1]}' → '{f[2]}'"
            for f in changed_fields
        )
        for f in changed_fields:
            NotificationService.send(
                user=admin,
                title="User Updated",
                message=f"User '{instance.full_name}' updated",
                icon="bi-pencil-square",
                link="/users/list",
                instance_id=instance.id,
                object_id=str(instance.id)
            )
