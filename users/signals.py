from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from notifications.models import Notification, UserNotification  # adjust if needed

User = get_user_model()


@receiver(pre_save, sender=User)
def store_old_user_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            instance._old_instance = old_instance
        except User.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None


@receiver(post_save, sender=User)
def notify_user_changes(sender, instance, created, **kwargs):
    if instance.is_superuser:
        return

    notification = None

    if created:
        notification = Notification.objects.create(
            notification_title="User Created",
            notification_text=f"User '{instance.full_name}' has been created.",
            icon="bi-person-plus-fill",
            link="/users/list",
            is_superuser=True,
            updated_by=instance,
            object_id=str(instance.id)
        )

    else:
        old_instance = getattr(instance, "_old_instance", None)

        if old_instance:

            # Soft Delete Detection
            if hasattr(instance, "is_deleted") and instance.is_deleted and not old_instance.is_deleted:
                notification = Notification.objects.create(
                    notification_title="User Deleted",
                    notification_text=f"User '{instance.full_name}' was deleted.",
                    icon="bi-person-dash-fill",
                    link="/users/list",
                    is_superuser=True,
                    updated_by=instance,
                    object_id=str(instance.id)
                )

            # Activation / Deactivation
            elif old_instance.is_active != instance.is_active:
                status_text = "Activated" if instance.is_active else "Deactivated"

                notification = Notification.objects.create(
                    notification_title=f"User {status_text}",
                    notification_text=f"User '{instance.full_name}' has been {status_text.lower()}.",
                    icon="bi-person-check-fill" if instance.is_active else "bi-person-x-fill",
                    link="/users/list",
                    is_superuser=True,
                    updated_by=instance,
                    object_id=str(instance.id)
                )

            # General Update
            else:
                notification = Notification.objects.create(
                    notification_title="User Updated",
                    notification_text=f"User '{instance.full_name}' has been updated.",
                    icon="bi-pencil-square",
                    link="/users/list",
                    is_superuser=True,
                    updated_by=instance,
                    object_id=str(instance.id)
                )

    if notification:
        admins = User.objects.filter(is_superuser=True)

        for admin in admins:
            UserNotification.objects.create(
                user=admin,
                notification=notification
            )
