from django.apps import AppConfig
from authentication.models import User
from django.db.models.signals import post_save 
from django.dispatch import receiver
from.seeders import seed_asset_statuses
from authentication.models import SeedFlag
from django.contrib.auth import get_user_model
from assets.models import Asset
from notifications.service import NotificationService
User = get_user_model()

print("ASSET SIGNALS")
@receiver(post_save, sender=Asset)
def asset_notification(sender, instance, created, **kwargs):
    if getattr(instance, "_skip_notification", False):
        return
    # Get organization admins
    admins = User.objects.filter(
        is_superuser=True,
        organization=instance.organization
    )
    if created:
        for admin in admins:
            instance._skip_notification = True  # ✅ block re-entry
            NotificationService.send(
                user=admin,
                title="Asset Created",
                message=f"Asset '{instance.name}' ({instance.tag}) has been created.",
                icon="bi-box-seam",
                link=f"/assets/details/{instance.id}",
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

        # Handle ForeignKeys
        field_object = instance._meta.get_field(field_name)
        if field_object.is_relation and field_object.many_to_one:
            old_value = str(old_value) if old_value else None
            new_value = str(new_value) if new_value else None

        if old_value != new_value:
            changed_fields.append((field_name, old_value, new_value))

    if not changed_fields:
        return



    for admin in admins:

        # Soft delete detection
        deleted_change = any(f for f in changed_fields if f[0] == "is_deleted")
        if deleted_change and instance.is_deleted:
            NotificationService.send(
                user=admin,
                title="Asset Deleted",
                message=f"Asset '{instance.name}', ({instance.tag}) was deleted.",
                icon="bi-trash",
                link=f"/assets/list",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
            continue

        # Status change detection
        status_change = any(f for f in changed_fields if f[0] == "asset_status")
        if status_change:
            NotificationService.send(
                user=admin,
                title="Asset Status Changed",
                message=f"Asset '{instance.name}' status changed.",
                icon="bi-arrow-repeat",
                link=f"/assets/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
            continue

        # Assignment change
        assigned_change = any(f for f in changed_fields if f[0] == "is_assigned")
        if assigned_change:
            status_text = "Assigned" if instance.is_assigned else "Unassigned"
            NotificationService.send(
                user=admin,
                title="Asset Assignment Updated",
                message=f"Asset '{instance.name}' is now {status_text}.",
                icon="bi-person-check",
                link=f"/assets/details/{instance.id}",
                instance_id=instance.id,
                object_id=str(instance.id),
            )
            continue

        changes_text = ", ".join(
            f"{f[0].replace('_', ' ').title()}: '{f[1]}' → '{f[2]}'"
            for f in changed_fields
        )

        NotificationService.send(
            user=admin,
            title="Asset Updated",
            message=f"Asset '{instance.name}' updated",
            icon="bi-pencil-square",
            link=f"/assets/details/{instance.id}",
            instance_id=instance.id,
            object_id=str(instance.id),
        )
        print("ASSET SIGNALS")

@receiver(post_save, sender=User)
def trigger_seed_on_first_superuser(sender,instance,created,**kwargs):
        if created and instance.is_superuser:
            
            if not SeedFlag.objects.exists():  # Only seed once
                seed_asset_statuses()
