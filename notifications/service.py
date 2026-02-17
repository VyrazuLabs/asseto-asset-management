from notifications.models import Notification, UserNotification
from notifications.utils import send_email
from assets.utils import slack_notification
from notifications.models import FirebaseToken
from firebase_admin import messaging
from .utils import send_data_message
from django.http import JsonResponse
class NotificationService:

    @staticmethod
    def send(
        *,
        user,
        title,
        message,
        icon=None,
        link=None,
        object_id=None,
        instance_id=None,
        is_superuser=False,
        updated_by=None
    ):
        #Always create DB notification
        notification = Notification.objects.create(
            notification_title=title,
            notification_text=message,
            icon=icon,
            link=link,
            instance_id=instance_id,
            is_superuser=is_superuser,
            updated_by=updated_by,
            object_id=object_id
        )

        UserNotification.objects.create(
            user=user,
            notification=notification
        )

        #In-app push
        if user.inapp_notification:
            token = FirebaseToken.objects.filter(user=user).first()
            if token:
                send_data_message(
                    token=token.token,
                    title=title,
                    body=message,
                    image_url=None
                )

        #Email
        if user.email_notification and user.email:
            send_email(
                user.email,
                notification_title=title,
                notification_text=message
            )

        #Slack
        if user.slack_notification:
            slack_notification(
                user,
                message,
                instance_id,
                None
            )

        return notification

