from django.db.models.signals import post_save, post_init, post_delete
from django.dispatch import receiver
from django.conf import settings
from notifications.models import Notification, UserNotification
from authentication.models import User
from datetime import datetime, timedelta
from django.db.backends.signals import connection_created
from assets.models import AssignAsset
from django.db import connection

# User Notification


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def userNotification(sender, instance, created,  **kwargs):

    if instance.previous_role != instance.role:
        notification = Notification.objects.create(
            instance_id=instance.id,
            notification_title='New User' if created else 'Updated User',
            notification_text=f'{instance.full_name} has been added to your team ({instance.role})',
            icon='bi-person-fill',
        )

        users = User.objects.filter(
            role=instance.role, organization=instance.organization).exclude(pk=instance.id)
        for user in users:
            UserNotification.objects.create(
                user=user,
                notification=notification
            )

    if instance.previous_role is not None and instance.previous_role != instance.role and not created:
        notification = Notification.objects.create(
            instance_id=instance.id,
            notification_title='Updated User',
            notification_text=f'{instance.full_name} has been removed from your team ({instance.previous_role})',
            icon='bi-person-fill',
        )

        users = User.objects.filter(
            role=instance.previous_role, organization=instance.organization)
        for user in users:
            UserNotification.objects.create(
                user=user,
                notification=notification
            )


@receiver(post_init, sender=settings.AUTH_USER_MODEL)
def remember_state_user(sender, instance, **kwargs):

    instance.previous_role = instance.role


# Asset Notification

@receiver(post_save, sender=AssignAsset)
def asset_notification(sender, instance, created,  **kwargs):

    if instance.previous_user != instance.user:

        notification = Notification.objects.create(
            instance_id=instance.id,
            notification_title='Assigned asset',
            notification_text=f'{instance.asset.name} is assigned to you.',
            icon='bi-person-workspace',
        )

        UserNotification.objects.create(
            user=instance.user,
            notification=notification
        )

    if instance.previous_user != instance.user and not created:
        notification = Notification.objects.create(
            instance_id=instance.id,
            notification_title='Assigned asset',
            notification_text=f'{instance.asset.name} is unassigned from you.',
            icon='bi-person-workspace',
        )

        UserNotification.objects.create(
            user=instance.previous_user,
            notification=notification
        )


@receiver(post_delete, sender=AssignAsset)
def asset_delete_notification(sender, instance, *args,  **kwargs):
    notification = Notification.objects.create(
        instance_id=instance.id,
        notification_title='Assigned asset',
        notification_text=f'{instance.asset.name} is unassigned from you.',
        icon='bi-person-workspace',
    )

    UserNotification.objects.create(
        user=instance.previous_user,
        notification=notification
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
                    link=f'/assets/details/{expiring_asset.asset.id}'
                )

                UserNotification.objects.create(
                    user=super_user,
                    notification=notification
                )

@receiver(connection_created)
def conn_db(sender, connection, **kwargs):
    expiring_asset(15)
    expiring_asset(7)
    expiring_asset(0)
