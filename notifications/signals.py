import sys
from django.db.models.signals import post_save, post_init, post_delete,pre_save
from django.dispatch import receiver
from django.conf import settings
from notifications.models import Notification, UserNotification
from authentication.models import User
from datetime import datetime, timedelta
from django.db.backends.signals import connection_created
from assets.models import AssignAsset
from django.db import connection
from assets.models import Asset
from notifications.utils import notifications_call,send_email
from assets.utils import slack_notification
from notifications.service import NotificationService
# User Notification
# Implement this with the service to maintain a clean code.
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_notification(sender, instance, created, **kwargs):
    if created:
        NotificationService.send(
            user=instance,
            title='New User',
            message=f'{instance.full_name} has been added to your team ({instance.role})',
            icon='bi-person-fill',
            instance_id=instance.id,
            object_id=str(instance.id)
        )

    elif instance.previous_role != instance.role:
        NotificationService.send(
            user=instance,
            title='Role Updated',
            message=f'{instance.full_name} role changed to {instance.role}',
            icon='bi-person-fill',
            instance_id=instance.id,
            object_id=str(instance.id)
        )

@receiver(post_init, sender=settings.AUTH_USER_MODEL)
def remember_state_user(sender, instance, **kwargs):
    instance.previous_role = instance.role

# Asset Notification

@receiver(pre_save, sender=Asset)
def save_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Asset.objects.get(pk=instance.pk)
            instance._old_status = old_instance.asset_status
        except Asset.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Asset)
def notify_admin_on_status_change(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_old_status'):
        old_status = instance._old_status
        new_status = instance.asset_status

        if old_status != new_status:
            notification = Notification.objects.create(
                notification_title="Status Changed",
                notification_text=f"The status of asset '{instance}' has been changed to '{new_status}'.",
                icon="bi-gear-fill",
                link=f"/assets/list",  # Update to actual admin URL
                is_superuser=True,
                updated_by=instance.updated_by,
                object_id=str(instance.id) if instance else None
            )
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                UserNotification.objects.create(user=admin, notification=notification)
            user = instance.updated_by
            # if user:
            #     if user.email_notification:
            #         send_email(
            #             user.email,
            #             notification_title="Updated asset",
            #             notification_text=f"{instance.name} status changed to {new_status}."
            #         )

            #     if user.slack_notification:
            #         slack_notification(
            #             user,
            #             f"{instance.name} status updated to {new_status}.",
            #             instance.id,
            #             instance.tag
            #         )
@receiver(post_save, sender=Asset)
def notify_admin_on_asset_created(sender, instance, created, **kwargs):
    if created:
        notification = Notification.objects.create(
            notification_title="Asset Created",
            notification_text=f"A new asset '{instance}' has been created.",
            icon="bi-plus-circle-fill",
            link="/assets/list",
            is_superuser=True,
            updated_by=instance.updated_by,
            object_id=str(instance.id)
        )

        admins = User.objects.filter(is_superuser=True)

        for admin in admins:
            UserNotification.objects.create(
                user=admin,
                notification=notification
            )

@receiver(post_save, sender=Asset)
def notify_admin_on_asset_updated(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_old_status'):
        
        old_status = instance._old_status
        new_status = instance.asset_status

        # Only notify if status did NOT change
        if old_status == new_status:
            notification = Notification.objects.create(
                notification_title="Asset Updated",
                notification_text=f"Asset '{instance}' has been updated.",
                icon="bi-pencil-square",
                link="/assets/list",
                is_superuser=True,
                updated_by=instance.updated_by,
                object_id=str(instance.id)
            )

            admins = User.objects.filter(is_superuser=True)

            for admin in admins:
                UserNotification.objects.create(
                    user=admin,
                    notification=notification
                )


@receiver(post_save, sender=AssignAsset)
def asset_notification(sender, instance, created,  **kwargs):
    if instance.previous_user != instance.user:
        # send_email(instance.user.email,notifications_title='Assigned asset',notification_text=f'{instance.asset.name} is assigned to you.')
        NotificationService.send(
            user=instance.user,
            title='Assigned Asset',
            message=f'{instance.asset.name} is assigned to you.',
            icon='bi-laptop',
            link=f'/assets/details/{instance.asset.id}',
            instance_id=instance.id,
            object_id=str(instance.asset.id)
        )

        # UserNotification.objects.create(
        #     user=instance.user,
        #     notification=notification
        # )

    if instance.previous_user != instance.user and not created:
        # send_email(instance.user.email,notifications_title='Assigned asset',notification_text=f'{instance.asset.name} is assigned to you.')
        NotificationService.send(
            user=instance.user,
            title='Assigned Asset',
            message=f'{instance.asset.name} is assigned to you.',
            icon='bi-laptop',
            link=f'/assets/details/{instance.asset.id}',
            instance_id=instance.id,
            object_id=str(instance.asset.id)
        )



        # UserNotification.objects.create(
        #     user=instance.previous_user,
        #     notification=notification
        # )


@receiver(post_delete, sender=AssignAsset)
def asset_delete_notification(sender, instance, *args,  **kwargs):
    # send_email(instance.user.email,notifications_title='Deleted Asset',notification_text=f'{instance.asset.name} is Deleted.')
        NotificationService.send(
            user=instance.previous_user,
            title='Asset Deleted',
            message=f'{instance.asset.name} has been deleted.',
            icon='bi-gear-fill',
            instance_id=instance.id
        )

@receiver(post_init, sender=AssignAsset)
def remember_state_asset(sender, instance, **kwargs):
    instance.previous_user = instance.user


def expiring_asset(days):
    # checking if table exists
    all_tables = connection.introspection.table_names()

    # Asset Expires Notification
    if 'assets_assignasset' in all_tables:
    
        time_threshold = datetime.now() + timedelta(days=days)
        expiring_assets = AssignAsset.objects.filter(
            asset__warranty_expiry_date=time_threshold)

        for expiring_asset in expiring_assets:

            super_user = User.objects.filter(
                is_superuser=True, organization=expiring_asset.user.organization).first()

            if not UserNotification.objects.filter(user=super_user, notification__notification_text=f'{expiring_asset.asset.name} warranty expires in {days} days.').exists():

                notification = Notification.objects.create(
                    instance_id=expiring_asset.id,
                    notification_title='Warranty Expires',
                    notification_text=f'{expiring_asset.asset.name} warranty expires in {days} days.',
                    icon='bi-person-workspace',
                    link=f'/assets/details/{expiring_asset.asset.id}',
                    object_id=str(expiring_asset.asset.id)
                )

                UserNotification.objects.create(
                    user=super_user,
                    notification=notification
                )
                # NotificationService.send(
                #     user=instance.previous_user,
                #     title='Asset Deleted',
                #     message=f'{instance.asset.name} has been deleted.',
                #     icon='bi-gear-fill',
                #     instance_id=instance.id
                # )

@receiver(connection_created)
def conn_db(sender, connection, **kwargs):
    # avoid running during migrations
    if any(cmd in sys.argv for cmd in ['makemigrations', 'migrate']):
        return
    expiring_asset(15)
    expiring_asset(7)
    expiring_asset(0)
