# audit/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Audit, AuditImage
from assets.models import AssignAsset
from notifications.service import NotificationService

User = get_user_model()

@receiver(post_save, sender=Audit)
def audit_created_notification(sender, instance, created, **kwargs):
    if not created:
        return

    asset = instance.asset
    organization = instance.organization

    #Notify Organization Admins
    admins = User.objects.filter(
        is_superuser=True,
        organization=organization
    )

    for admin in admins:
        NotificationService.send(
            user=admin,
            title="Audit Completed",
            message=f"Audit completed for asset '{asset.tag}'.",
            icon="bi-clipboard-check",
            link=f"/audit/details/{instance.id}",
            instance_id=instance.id,
            object_id=str(instance.id)
        )

    #Notify Assigned Asset User (if exists)
    assign_record = AssignAsset.objects.filter(asset=asset).order_by("-assigned_date").first()

    if assign_record and assign_record.user:
        NotificationService.send(
            user=assign_record.user,
            title="Asset Audited",
            message=f"Your assigned asset '{asset.tag}' has been audited.",
            icon="bi-clipboard-check",
            link=f"/audit/details/{instance.id}",
            instance_id=str(instance.id),
            object_id=str(instance.id)
        )

    #Notify Specific Assigned-To (if stored separately)
    if instance.assigned_to:
        try:
            assigned_user = User.objects.filter(full_name=instance.assigned_to).first()
            if assigned_user:
                NotificationService.send(
                    user=assigned_user,
                    title="Audit Assigned",
                    message=f"You have been assigned an audit for asset '{asset.tag}'.",
                    icon="bi-person-check",
                    link=f"/audit/details/{instance.id}",
                    instance_id=instance.id,
                    object_id=str(instance.id)
                )
        except Exception:
            pass
