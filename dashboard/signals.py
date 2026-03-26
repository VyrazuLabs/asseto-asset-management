# from django.db.models.signals import post_save, post_delete, pre_save
# from django.dispatch import receiver
# from .models import (
#     Department, Location, Organization,
#     ProductType, ProductCategory,
#     Address, CustomField, LicenseType
# )
# # -----------------------------
# # COMMON HANDLER FUNCTIONS
# # -----------------------------

# def log_create(instance):
#     print(f"✅ CREATED: {instance.__class__.__name__} -> {instance}")


# def log_update(instance):
#     print(f"✏️ UPDATED: {instance.__class__.__name__} -> {instance}")


# def log_delete(instance):
#     print(f"❌ DELETED: {instance.__class__.__name__} -> {instance}")


# def log_soft_delete(instance):
#     print(f"🗑️ SOFT DELETED: {instance.__class__.__name__} -> {instance}")


# def log_restore(instance):
#     print(f"♻️ RESTORED: {instance.__class__.__name__} -> {instance}")


# # -----------------------------
# # PRE SAVE (Detect Soft Delete / Restore)
# # -----------------------------

# @receiver(pre_save)
# def detect_soft_delete_or_restore(sender, instance, **kwargs):
#     if not hasattr(instance, 'is_deleted'):
#         return

#     if not instance.pk:
#         return

#     try:
#         old_instance = sender.objects.get(pk=instance.pk)
#     except sender.DoesNotExist:
#         return

#     if old_instance.is_deleted is False and instance.is_deleted is True:
#         log_soft_delete(instance)

#     elif old_instance.is_deleted is True and instance.is_deleted is False:
#         log_restore(instance)


# # -----------------------------
# # POST SAVE (Create / Update)
# # -----------------------------

# @receiver(post_save)
# def post_save_handler(sender, instance, created, **kwargs):
#     tracked_models = (
#         Department, Location, Organization,
#         ProductType, ProductCategory,
#         Address, CustomField, LicenseType
#     )

#     if sender not in tracked_models:
#         return

#     if created:
#         log_create(instance)
#     else:
#         log_update(instance)


# # -----------------------------
# # POST DELETE (Hard Delete)
# # -----------------------------

# @receiver(post_delete)
# def post_delete_handler(sender, instance, **kwargs):
#     tracked_models = (
#         Department, Location, Organization,
#         ProductType, ProductCategory,
#         Address, CustomField, LicenseType
#     )

#     if sender not in tracked_models:
#         return

#     log_delete(instance)
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import (
    Department, Location, Organization,
    ProductType, ProductCategory,
    Address, CustomField, LicenseType
)
from notifications.service import NotificationService
from notifications.models import Notification

User = get_user_model()

# -----------------------------
# TRACKED MODELS
# -----------------------------

TRACKED_MODELS = (
    Department, Location, Organization,
    ProductType, ProductCategory,
    Address, CustomField, LicenseType
)

# -----------------------------
# HELPER: GET ADMINS
# -----------------------------

def get_admins(instance):
    if hasattr(instance, "organization") and instance.organization:
        return User.objects.filter(
            is_superuser=True,
            organization=instance.organization
        )
    return User.objects.filter(is_superuser=True)

# -----------------------------
# HELPER: CREATE NOTIFICATION
# -----------------------------

def notify(users, title, message, icon=None, link=None, instance=None):
    notifications = [
        Notification(
            user=user,
            title=title,
            message=message,
            icon=icon,
            link=link,
            instance_id=getattr(instance, "pk", None),
            object_id=str(getattr(instance, "pk", "")),
        )
        for user in users
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)

# -----------------------------
# PRE SAVE (STORE OLD STATE)
# -----------------------------

def store_previous_state(sender, instance):
    if not hasattr(instance, 'is_deleted'):
        instance._old_is_deleted = None
        return

    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_is_deleted = old_instance.is_deleted
        except sender.DoesNotExist:
            instance._old_is_deleted = None
    else:
        instance._old_is_deleted = None


def register_pre_save(model):
    @receiver(pre_save, sender=model)
    def pre_save_handler(sender, instance, **kwargs):
        store_previous_state(sender, instance)


# -----------------------------
# POST SAVE HANDLER
# -----------------------------

def handle_post_save(sender, instance, created):
    admins = get_admins(instance)
    model_name = sender.__name__

    # CREATE
    if created:
        for admin in admins:
            NotificationService.send(
                user=admin,
                title=f"{model_name} Created",
                message=f"{instance} has been created.",
                icon="bi-plus-circle",
                link="#",
                instance_id=instance.id,
                object_id=str(instance.id)
            )
        return

    # SOFT DELETE
    if hasattr(instance, "_old_is_deleted"):
        if instance._old_is_deleted is False and instance.is_deleted is True:
            for admin in admins:
                NotificationService.send(
                    user=admin,
                    title=f"{model_name} Deleted",
                    message=f"{instance} was deleted.",
                    icon="bi-trash",
                    link="#",
                    instance_id=instance.id,
                    object_id=str(instance.id)
                )
            return

        # RESTORE
        if instance._old_is_deleted is True and instance.is_deleted is False:
            for admin in admins:
                NotificationService.send(
                    user=admin,
                    title=f"{model_name} Restored",
                    message=f"{instance} has been restored.",
                    icon="bi-arrow-counterclockwise",
                    link="#",
                    instance_id=instance.id,
                    object_id=str(instance.id)
                )
            return

    # UPDATE
    for admin in admins:
        NotificationService.send(
            user=admin,
            title=f"{model_name} Updated",
            message=f"{instance} has been updated.",
            icon="bi-pencil-square",
            link="#",
            instance_id=instance.id,
            object_id=str(instance.id)
        )


def register_post_save(model):
    @receiver(post_save, sender=model)
    def post_save_handler(sender, instance, created, **kwargs):
        handle_post_save(sender, instance, created)


# -----------------------------
# POST DELETE (HARD DELETE)
# -----------------------------

def handle_post_delete(sender, instance):
    admins = get_admins(instance)
    model_name = sender.__name__

    NotificationService.send(
        user=admins,
        title=f"{model_name} Permanently Deleted",
        message=f"{instance} was permanently removed.",
        icon="bi-x-circle",
        link="#",
        instance=instance,
        object_id=str(instance.id)
    )


def register_post_delete(model):
    @receiver(post_delete, sender=model)
    def post_delete_handler(sender, instance, **kwargs):
        handle_post_delete(sender, instance)


# -----------------------------
# REGISTER ALL SIGNALS
# -----------------------------

for model in TRACKED_MODELS:
    register_pre_save(model)
    register_post_save(model)
    register_post_delete(model)