import structlog
from django.apps import AppConfig
from authentication.models import User
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .seeders import seed_asset_statuses
from authentication.models import SeedFlag
from django.contrib.auth import get_user_model
from assets.models import Asset, AssignAsset
from notifications.service import NotificationService

User = get_user_model()

log = structlog.get_logger(__name__)
log.info("asset_signals_loaded")


def _send_after_commit(**kwargs):
    """Queue NotificationService.send until the current transaction commits.

    post_save runs inside callers' @transaction.atomic blocks; sending here
    would hold row locks open for the whole (potentially slow) notification
    path (Celery retry + sync fallback + Firebase), which invited deadlocks.
    """
    transaction.on_commit(lambda: NotificationService.send(**kwargs))


@receiver(post_save, sender=Asset)
def asset_notification(sender, instance, created, **kwargs):
    if getattr(instance, "_skip_notification", False):
        return
    # Get organization admins
    admins = User.objects.filter(is_superuser=True, organization=instance.organization)
    if created:
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

        # Handle ForeignKeys
        field_object = instance._meta.get_field(field_name)
        if field_object.is_relation and field_object.many_to_one:
            old_value = str(old_value) if old_value else None
            new_value = str(new_value) if new_value else None

        if old_value != new_value:
            changed_fields.append((field_name, old_value, new_value))

    if not changed_fields:
        return

    deleted_change = any(f for f in changed_fields if f[0] == "is_deleted")
    status_change = any(f for f in changed_fields if f[0] == "asset_status")
    assigned_entry = next((f for f in changed_fields if f[0] == "is_assigned"), None)

    if deleted_change and instance.is_deleted:
        notif_type = "deleted"
    elif assigned_entry:
        old_assigned, new_assigned = assigned_entry[1], assigned_entry[2]
        if not old_assigned and new_assigned:
            notif_type = "assign"
        elif old_assigned and not new_assigned:
            notif_type = "unassign"
        else:
            notif_type = "generic"
    elif status_change:
        notif_type = "status"
    else:
        notif_type = "generic"

    status_name = instance.asset_status.name if instance.asset_status else None
    status_msg = (
        f"Asset '{instance.name}' status changed to '{status_name}'."
        if status_name
        else f"Asset '{instance.name}' status changed."
    )

    for admin in admins:
        if notif_type == "deleted":
            _send_after_commit(
                user=admin,
                title="Asset Deleted",
                message=f"Asset '{instance.name}', ({instance.tag}) was deleted.",
                icon="bi-trash",
                link="/assets/list",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
        elif notif_type == "assign":
            _send_after_commit(
                user=admin,
                title="Asset Assigned",
                message=f"Asset '{instance.name}' has been assigned.",
                icon="bi-person-check",
                link=f"/assets/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
            _send_after_commit(
                user=admin,
                title="Asset Status Changed",
                message=status_msg,
                icon="bi-arrow-repeat",
                link=f"/assets/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
        elif notif_type == "unassign":
            _send_after_commit(
                user=admin,
                title="Asset Unassigned",
                message=f"Asset '{instance.name}' has been unassigned.",
                icon="bi-person-dash",
                link=f"/assets/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
            _send_after_commit(
                user=admin,
                title="Asset Status Changed",
                message=status_msg,
                icon="bi-arrow-repeat",
                link=f"/assets/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
        elif notif_type == "status":
            _send_after_commit(
                user=admin,
                title="Asset Status Changed",
                message=status_msg,
                icon="bi-arrow-repeat",
                link=f"/assets/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
        else:
            _send_after_commit(
                user=admin,
                title="Asset Updated",
                message=f"Asset '{instance.name}' updated",
                icon="bi-pencil-square",
                link=f"/assets/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
            log.info("asset_updated_notification_sent", asset_id=str(instance.id))


@receiver(pre_save, sender=AssignAsset)
def capture_previous_assignee(sender, instance, **kwargs):
    """Store previous user_id before AssignAsset save to detect reassignments."""
    if instance.pk:
        instance._old_user_id = (
            AssignAsset.objects.filter(pk=instance.pk)
            .values_list("user_id", flat=True)
            .first()
        )
    else:
        instance._old_user_id = None


@receiver(post_save, sender=AssignAsset)
def assign_asset_reassignment_notification(sender, instance, created, **kwargs):
    """Send 1 notification when an existing AssignAsset is reassigned to a new user."""
    if created or not instance.asset:
        return

    old_user_id = getattr(instance, "_old_user_id", None)
    if old_user_id is None or old_user_id == instance.user_id:
        return

    admins = User.objects.filter(
        is_superuser=True, organization=instance.asset.organization
    )
    user_label = str(instance.user) if instance.user else "a new user"
    for admin in admins:
        _send_after_commit(
            user=admin,
            title="Asset Reassigned",
            message=f"Asset '{instance.asset.name}' has been reassigned to {user_label}.",
            icon="bi-person-check",
            link=f"/assets/details/{instance.asset.id}",
            instance_id=instance.asset.id,
            object_id=str(instance.asset.id),
        )


@receiver(post_save, sender=User)
def trigger_seed_on_first_superuser(sender, instance, created, **kwargs):
    if created and instance.is_superuser:

        if not SeedFlag.objects.exists():  # Only seed once
            seed_asset_statuses()
