from celery import shared_task
from notifications.models import Notification, UserNotification, FirebaseToken
from notifications.utils import send_email
from assets.utils import slack_notification
from .utils import send_data_message


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3,acks_late=True)
# @shared_task(bind=True)
def send_notification_task(self, payload):
    # print("🔥 TASK STARTED:", payload)
    user = payload["user"]
    title = payload["title"]
    message = payload["message"]

    notification = Notification.objects.create(
        notification_title=title,
        notification_text=message,
        icon=payload.get("icon"),
        link=payload.get("link"),
        instance_id=payload.get("instance_id"),
        is_superuser=payload.get("is_superuser", False),
        updated_by=payload.get("updated_by"),
        object_id=payload.get("object_id"),
    )

    UserNotification.objects.create(
        user_id=user,
        notification=notification
    )

    # In-app push
    token = FirebaseToken.objects.filter(user_id=user).first()
    if token:
        send_data_message(
            token=token.token,
            title=title,
            body=message,
            image_url=None
        )

    # Email
    # (fetch user again to avoid serialization issues)
    from django.contrib.auth import get_user_model
    User = get_user_model()

    user_obj = User.objects.get(id=user)

    if user_obj.email_notification and user_obj.email:
        send_email(user_obj.email, title, message)

    # Slack
    if user_obj.slack_notification:
        slack_notification(user_obj, message, payload.get("instance_id"), None)