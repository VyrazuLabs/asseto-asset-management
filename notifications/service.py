from kombu.exceptions import OperationalError
from notifications.tasks import send_notification_task
class NotificationService:

    @staticmethod
    def send(**kwargs):
        user_obj = kwargs.get("user")
        if hasattr(user_obj, "id"):
            user_id = user_obj.id
        elif hasattr(user_obj, "first"):
            user_instance = user_obj.first()
            user_id = user_instance.id if user_instance else None
        else:
            user_id = user_obj  # assume it's already an ID
        payload = {
            "user": user_id,
            "title": kwargs["title"],
            "message": kwargs["message"],
            "icon": kwargs.get("icon"),
            "link": kwargs.get("link"),
            "object_id": kwargs.get("object_id"),
            "instance_id": kwargs.get("instance_id"),
            "is_superuser": kwargs.get("is_superuser", False),
            "updated_by": (
                kwargs.get("updated_by").id if kwargs.get("updated_by") else None
            ),
        }

        # async call
        try:
            send_notification_task.delay(payload)
        except OperationalError as e:
            print("????", e)
            print("Celery broker unavailable, skipping async task")
            send_notification_task(payload)
