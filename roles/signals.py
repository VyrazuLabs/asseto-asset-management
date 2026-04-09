from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from .models import Role, AssetStatus
from notifications.service import NotificationService   # adjust import path if needed
from users.models import User


def get_admins(instance):
    if hasattr(instance, "organization") and instance.organization:
        return User.objects.filter(
            is_superuser=True,
            organization=instance.organization
        )
    return User.objects.filter(is_superuser=True)
# -----------------------------
# PRE SAVE → Detect Soft Delete / Restore
# -----------------------------

@receiver(pre_save)
def detect_soft_delete_or_restore(sender, instance, **kwargs):
    admins = get_admins(instance)
    if sender not in (AssetStatus,):
        return

    if not hasattr(instance, 'is_deleted'):
        return

    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    # Soft Delete
    if old_instance.is_deleted is False and instance.is_deleted is True:
        for admin in admins:
            NotificationService.send(
                user=admin,
                title=f"{sender.__name__} Deleted",
                message=f"{instance} was deleted.",
                icon="bi-trash",
                link="#",
                instance_id=instance.id,
                object_id=str(instance.id)
            )

    # Restore
    elif old_instance.is_deleted is True and instance.is_deleted is False:
        for admin in admins:
            NotificationService.send(
                user=admin,
                title=f"{sender.__name__} Restored",
                message=f"{instance} was restored.",
                icon="bi-arrow-counterclockwise",
                link="#",
                instance_id=instance.id,
                object_id=str(instance.id)
            )


# -----------------------------
# POST SAVE → Create / Update
# -----------------------------

@receiver(post_save)
def post_save_handler(sender, instance, created, **kwargs):
    tracked_models = (Role, AssetStatus)
    admins=get_admins(instance)
    if sender not in tracked_models:
        return

    if created:
        for admin in admins:
            NotificationService.send(
                user=admin,
                title=f"{sender.__name__} Created",
                message=f"{instance} has been created.",
                icon="bi-plus-circle",
                link="#",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
    else:
        for admin in admins:
            NotificationService.send(
                user=admins,
                title=f"{sender.__name__} Updated",
                message=f"{instance} has been updated.",
                icon="bi-pencil",
                link="#",
                instance_id=instance.id,
                object_id=str(instance.id),
            )


# -----------------------------
# POST DELETE → Hard Delete
# -----------------------------

@receiver(post_delete)
def post_delete_handler(sender, instance, **kwargs):
    tracked_models = (Role, AssetStatus)
    admins=get_admins(instance)
    if sender not in tracked_models:
        return
    for admin in admins:
        NotificationService.send(
            user=admin,
            title=f"{sender.__name__} Permanently Deleted",
            message=f"{instance} was permanently removed.",
            icon="bi-x-circle",
            link="#",
            instance_id=instance.id,
            object_id=str(instance.id),
        )