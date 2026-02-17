from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from license.models import License
from notifications.models import Notification, UserNotification  # adjust import if needed
from notifications.service import NotificationService
User = get_user_model()


@receiver(pre_save, sender=License)
def store_old_license(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = License.objects.get(pk=instance.pk)
            instance._old_instance = old_instance
        except License.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None

@receiver(post_save, sender=License)
def notify_license_create_update(sender, instance, created, **kwargs):
    if created:
        NotificationService.send(
            notification_title="License Created",
            notification_text=f"License '{instance.name}' has been created.",
            icon="bi-plus-circle-fill",
            link="/license/list",
            is_superuser=True,
            updated_by=getattr(instance, "updated_by", None),
            object_id=str(instance.id)
        )


    else:
        NotificationService.send(
            notification_title="License Updated",
            notification_text=f"License '{instance.name}' has been updated.",
            icon="bi-pencil-square",
            link="/license/list",
            is_superuser=True,
            updated_by=getattr(instance, "updated_by", None),
            object_id=str(instance.id)
        )

    admins = User.objects.filter(is_superuser=True)

    # for admin in admins:
    #     UserNotification.objects.create(
    #         user=admin,
    #         notification=notification
    #     )
    if not created and hasattr(instance, "is_deleted") and instance.is_deleted:
        Notification.objects.create(
            notification_title="License Deleted",
            notification_text=f"License '{instance.name}' was moved to trash.",
            icon="bi-trash-fill",
            link="/license/list",
            is_superuser=True,
            updated_by=getattr(instance, "updated_by", None),
            object_id=str(instance.id)
        )

        # admins = User.objects.filter(is_superuser=True)
        # for admin in admins:
        #     UserNotification.objects.create(
        #         user=admin,
        #         notification=notification
        #     )
        return
