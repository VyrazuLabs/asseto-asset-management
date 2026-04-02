# from notifications.models import Notification, UserNotification
# from notifications.utils import send_email
# from assets.utils import slack_notification
# from notifications.models import FirebaseToken
# from firebase_admin import messaging
# from .utils import send_data_message
# from django.http import JsonResponse
from kombu.exceptions import OperationalError
# class NotificationService:

#     @staticmethod
#     def send(
#         *,
#         user,
#         title,
#         message,
#         icon=None,
#         link=None,
#         object_id=None,
#         instance_id=None,
#         is_superuser=False,
#         updated_by=None
#     ):
#         #Always create DB notification
#         notification = Notification.objects.create(
#             notification_title=title,
#             notification_text=message,
#             icon=icon,
#             link=link,
#             instance_id=instance_id,
#             is_superuser=is_superuser,
#             updated_by=updated_by,
#             object_id=object_id
#         )

#         UserNotification.objects.create(
#             user=user,
#             notification=notification
#         )

#         #In-app push
#         if user.inapp_notification:
#             token = FirebaseToken.objects.filter(user=user).first()
#             if token:
#                 print('Sending in-app notification to user:----', user.username,token.token)
#                 send_data_message(
#                     token=token.token,
#                     title=title,
#                     body=message,
#                     image_url=None
#                 )

#         #Email
#         if user.email_notification and user.email:
#             send_email(
#                 user.email,
#                 notification_title=title,
#                 notification_text=message
#             )

#         #Slack
#         if user.slack_notification:
#             slack_notification(
#                 user,
#                 message,
#                 instance_id,
#                 None
#             )

#         return notification

from notifications.tasks import send_notification_task

class NotificationService:

    @staticmethod
    def send(**kwargs):
        user_obj = kwargs.get("user")
        if hasattr(user_obj, "id"):
            user_id = user_obj.id
        elif hasattr(user_obj, "first"):  # QuerySet
            user_instance = user_obj.first()
            user_id = user_instance.id if user_instance else None
        else:
            user_id = user_obj  # assume it's already an ID
        payload = {
            "user": user_id,
            # "user": kwargs["user"],
            "title": kwargs["title"],
            "message": kwargs["message"],
            "icon": kwargs.get("icon"),
            "link": kwargs.get("link"),
            "object_id": kwargs.get("object_id"),
            "instance_id": kwargs.get("instance_id"),
            "is_superuser": kwargs.get("is_superuser", False),
            "updated_by": kwargs.get("updated_by").id if kwargs.get("updated_by") else None,
        }

        # async call
        try:
            send_notification_task.delay(payload)
        except OperationalError as e:
            print("????",e)
            print("⚠️ Celery broker unavailable, skipping async task")
            send_notification_task(payload)